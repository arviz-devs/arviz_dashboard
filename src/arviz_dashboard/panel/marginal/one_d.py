from __future__ import annotations

import arviz as az
import panel as pn
import param
from bokeh.models.sources import ColumnDataSource
from bokeh.models.tools import HoverTool
from bokeh.palettes import Colorblind8
from bokeh.plotting import figure

from arviz_dashboard import plots, widgets
from arviz_dashboard.dashboards import DashboardBaseClass

pn.extension()


def posterior_marginal1d(idata: az.InferenceData) -> None:
    """Dashboard for the one-dimensional marginals of random variable posteriors.

    Parameters
    ----------
    idata : az.InferenceData
        An ArviZ `InferenceData` object that contains the posterior for the model.

    Returns
    -------
    None
        If in a Jupyter environment, then the dashboard will be directly displayed.
    """
    # NOTE: See the docstring for `create_selectors` for a full description as to why we
    #       are creating objects this way. Briefly, we do not know the random variables
    #       used in a model, and this is a way to create them within the class below.
    Widgets = type("Widgets", (param.Parameterized,), widgets.create_selectors(idata))

    class PosteriorMarginal1d(DashboardBaseClass, Widgets):
        """Parameterized class to that computes and reacts to user interactions.

        Parameters
        ----------
        idata : az.InferenceData
            An ArviZ `InferenceData` object that contains the posterior for the model.
        """

        chain_aggregation = param.Selector(objects=["separate", "aggregate"])
        figure_names = ["marginal"]

        def __init__(
            self: PosteriorMarginal1d,
            idata: az.InferenceData,
            **params,
        ) -> None:
            # Initialize param and the base class
            super().__init__(idata, **params)

        def _compute(self: PosteriorMarginal1d) -> dict[str, dict[str, list[float]]]:
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
            for figure_name in self.figure_names:
                output[figure_name] = {}
                if figure_name == "marginal":
                    if self.chain_aggregation == "separate":
                        for i, chain in enumerate(self.chain_selector):
                            chain_data = data[i]
                            support, density, bandwidth = az.stats.kde(
                                chain_data,
                                bw_return=True,
                            )
                            density /= density.max()
                            output[figure_name][f"{chain}"] = {
                                "support": support.tolist(),
                                "density": density.tolist(),
                                "bandwidth": [float(bandwidth)],
                            }
                    if self.chain_aggregation == "aggregate":
                        chain_data = data.reshape(1, -1)
                        support, density, bandwidth = az.stats.kde(
                            chain_data,
                            bw_return=True,
                        )
                        density /= density.max()
                        output[figure_name]["0"] = {
                            "support": support.tolist(),
                            "density": density.tolist(),
                            "bandwidth": [float(bandwidth)],
                        }
            return output

        def _plot(self: PosteriorMarginal1d, *args) -> figure:
            data = self.compute()
            figures = {}
            for figure_name, figure_data in data.items():
                if figure_name == "marginal":
                    fig = figure()
                    plots.style_figure(fig, self.rv_selector)
                    for i, (chain, chain_data) in enumerate(figure_data.items()):
                        if self.chain_aggregation == "aggregate":
                            color = self.palette[0]
                        else:
                            color = self.palette[i]
                        cds = ColumnDataSource(
                            data={
                                "x": chain_data["support"],
                                "y": chain_data["density"],
                            },
                        )
                        glyph = fig.line(
                            x="x",
                            y="y",
                            source=cds,
                            line_alpha=0.6,
                            line_color=color,
                            line_width=2.0,
                            hover_line_alpha=1.0,
                            hover_line_color=color,
                        )
                        tips = HoverTool(
                            renderers=[glyph],
                            tooltips=[("Chain", chain), (self.rv_selector, "@x")],
                        )
                        fig.add_tools(tips)
                    figures[figure_name] = fig
            return pn.Row(*figures.values())

    dashboard = PosteriorMarginal1d(idata)
    return dashboard.show()
