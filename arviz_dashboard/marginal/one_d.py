from __future__ import annotations

import arviz as az
import numpy as np
import numpy.typing as npt
import panel as pn
import param
import xarray
from bokeh.models.sources import ColumnDataSource
from bokeh.models.tools import HoverTool
from bokeh.palettes import Colorblind8
from bokeh.plotting import Figure, figure


pn.extension()


def style_figure(fig: Figure, title: str) -> None:
    fig.outline_line_color = "black"
    fig.yaxis.visible = False
    fig.title = title


def select_chain_data(
    all_chains: list[int],
    selected_chains: list[int],
    rv_data_xarray: xarray.DataArray,
    aggregation: str,
) -> npt.ArrayLike:
    # Select only the chains the user has selected.
    chain_mask = [True if chain in selected_chains else False for chain in all_chains]
    rv_chain_data = rv_data_xarray[chain_mask, ...].data

    # Handle concatenating chains together.
    if aggregation == "aggregate":
        rv_chain_data = np.concatenate(rv_chain_data, axis=0)
        rv_chain_data = rv_chain_data.reshape(1, *rv_chain_data.shape)

    return rv_chain_data


def create_selectors(idata: az.InferenceData) -> dict[str, param.Parameter]:
    output = {}
    output["rv_selector"] = param.Selector(
        label="Random variable",
        objects=list(idata["posterior"].data_vars.keys()),
    )
    dimensions = list(idata["posterior"].coords)
    for dimension in dimensions:
        if dimension == "draw":
            continue
        objects = idata["posterior"].coords[dimension].data.tolist()
        if dimension == "chain":
            output[f"{dimension}_selector"] = param.ListSelector(
                objects=objects, default=[0]
            )
        else:
            output[f"{dimension}_selector"] = param.Selector(objects=objects)
    return output


def posterior_marginal1d_dashboard(idata: az.InferenceData) -> None:

    DashboardWidgets = type(
        "DashboardWidgets",
        (param.Parameterized,),
        create_selectors(idata),
    )

    class PosteriorMarginal1dDashboard(DashboardWidgets):

        chain_aggregation = param.Selector(objects=["separate", "aggregate"])

        def __init__(
            self: PosteriorMarginal1dDashboard,
            idata: az.InferenceData,
            **params,
        ) -> None:
            # Input data.
            self.posterior = idata["posterior"]
            # rv_names = list(self.posterior.data_vars.keys())
            self.chains = self.posterior.coords["chain"].data.tolist()
            # self.num_chains = self.posterior.dims["chain"]
            # self.num_draws = self.posterior.dims["draw"]
            self.dimension_names = [
                dimension_name
                for dimension_name in self.posterior.coords.dims
                if dimension_name not in ["chain", "draw"]
            ]
            self.dimensions = {
                dimension_name: self.posterior.coords[dimension_name].values.tolist()
                for dimension_name in self.dimension_names
            }

            # Plotting
            self.palette = Colorblind8

            # Initialize param
            super().__init__(**params)

        def compute(
            self: PosteriorMarginal1dDashboard,
        ) -> dict[str, dict[str, list[float]]]:
            output = {}
            rv_data_xarray = self.posterior[self.rv_selector]
            rv_dimensions = list(rv_data_xarray.coords)
            mask = {"chain": self.chain_selector}
            for dimension_name in self.dimensions:
                if dimension_name in rv_dimensions:
                    dimension_value = getattr(self, f"{dimension_name}_selector")
                    dimension_objects = self.dimensions[dimension_name]
                    dimension_values = []
                    for i, dimension_object in enumerate(dimension_objects):
                        if dimension_object == dimension_value:
                            dimension_values.append(i)
                    mask[dimension_name] = dimension_values
            data = rv_data_xarray[mask].data
            if len(data.shape) == 1:
                data = data.reshape(1, -1)
            if self.chain_aggregation == "separate":
                for i, chain in enumerate(self.chain_selector):
                    chain_data = data[i]
                    support, density, bandwidth = az.stats.kde(
                        chain_data, bw_return=True
                    )
                    density /= density.max()
                    output[f"{chain}"] = {
                        "support": support.tolist(),
                        "density": density.tolist(),
                        "bandwidth": [float(bandwidth)],
                    }
            if self.chain_aggregation == "aggregate":
                chain_data = data.reshape(1, -1)
                support, density, bandwidth = az.stats.kde(chain_data, bw_return=True)
                density /= density.max()
                output["0"] = {
                    "support": support.tolist(),
                    "density": density.tolist(),
                    "bandwidth": [float(bandwidth)],
                }
            return output

        def plot(self: PosteriorMarginal1dDashboard, *args) -> Figure:
            fig = figure()
            style_figure(fig, self.rv_selector)
            data = self.compute()
            for i, (chain, chain_data) in enumerate(data.items()):
                if self.chain_aggregation == "aggregate":
                    color = self.palette[0]
                else:
                    color = self.palette[i]
                locals()[f"cds{i}"] = ColumnDataSource(
                    data={"x": chain_data["support"], "y": chain_data["density"]},
                )
                locals()[f"glyph{i}"] = fig.line(
                    x="x",
                    y="y",
                    source=locals()[f"cds{i}"],
                    line_alpha=0.6,
                    line_color=color,
                    line_width=2.0,
                    hover_line_alpha=1.0,
                    hover_line_color=color,
                )
                locals()[f"tips{i}"] = HoverTool(
                    renderers=[locals()[f"glyph{i}"]],
                    tooltips=[("Chain", chain), (self.rv_selector, "@x")],
                )
                fig.add_tools(locals()[f"tips{i}"])
            return fig

        def show(self: PosteriorMarginal1dDashboard) -> None:
            return pn.Row(self.param, self.plot)

    dashboard = PosteriorMarginal1dDashboard(idata)
    return dashboard.show()
