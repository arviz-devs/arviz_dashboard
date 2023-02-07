from __future__ import annotations

import arviz as az
import panel as pn
import param
from bokeh.models.sources import ColumnDataSource
from bokeh.models.tools import HoverTool
from bokeh.palettes import Colorblind8
from bokeh.plotting import figure

pn.extension()


def style_figure(fig: figure, title: str) -> None:
    """Style the given Bokeh figure.

    Parameters
    ----------
    fig : figure
        Bokeh figure object to style.
    title : str
        Title for the figure.

    Returns
    -------
    None
        Directly applies the style to the figure.
    """
    fig.outline_line_color = "black"
    fig.yaxis.visible = False
    fig.title = title


def create_selectors(idata: az.InferenceData) -> dict[str, param.Parameter]:
    """Create `param.Selector` objects for the dashboard.

    We do not know a priori the random variables used for any given model. We also do
    not know any hierarchy for the given model represented by the ArviZ `InferenceData`
    object. This method iterates through the `idata` object to find all the random
    variables used in the model, and any hierarchy if it exists.

    Parameters
    ----------
    idata : az.InferenceData
        An ArviZ `InferenceData` object that contains the posterior for the model.

    Returns
    -------
    output : dict[str, param.Parameter]
        A dictionary of random variable names as keys and `param` objects as values.

    Raises
    ------
    AttributeError
        If no "posterior" is found in the ArviZ `InferenceData` object, then a model has
        more than likely not been run.
    """
    if not hasattr(idata, "posterior"):
        raise AttributeError(
            "The given ArviZ InferenceData object does not contain a posterior. "
            "Have you run a model?"
        )
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
                objects=objects,
                default=[0],
            )
        else:
            output[f"{dimension}_selector"] = param.Selector(objects=objects)
    return output


def posterior_marginal1d_dashboard(idata: az.InferenceData) -> None:
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
    DashboardWidgets = type(
        "DashboardWidgets",
        (param.Parameterized,),
        create_selectors(idata),
    )

    class PosteriorMarginal1dDashboard(DashboardWidgets):
        """Parameterized class to that computes and reacts to user interactions.

        Parameters
        ----------
        idata : az.InferenceData
            An ArviZ `InferenceData` object that contains the posterior for the model.
        """

        chain_aggregation = param.Selector(objects=["separate", "aggregate"])

        def __init__(
            self: PosteriorMarginal1dDashboard,
            idata: az.InferenceData,
            **params,
        ) -> None:
            # Input data.
            self.posterior = idata["posterior"]
            self.chains = self.posterior.coords["chain"].data.tolist()
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
            """Compute the 1D kernel density estimate for the selected random variable.

            Returns
            -------
            output : dict[str, dict[str, list[float]]]
                A dictionary consisting of the random variable name as the key, and the
                KDE estimate as the value.
            """
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
                        chain_data,
                        bw_return=True,
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

        def plot(self: PosteriorMarginal1dDashboard, *args) -> figure:  # dead: disable
            """Plot the dashboard.

            Returns
            -------
            fig : figure
                The Bokeh figure containing 1D KDEs.
            """
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
            """Shows the dashboard in a Jupyter environment.

            Returns
            -------
            None
                Renders the dashboard directly in the notebook.
            """
            return pn.Row(self.param, self.plot)

    dashboard = PosteriorMarginal1dDashboard(idata)
    return dashboard.show()
