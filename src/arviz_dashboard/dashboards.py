from __future__ import annotations

import arviz as az
import panel as pn
import param
from bokeh.palettes import Colorblind8
from bokeh.plotting import figure


class DashboardBaseClass(param.Parameterized):
    """Base class for creation dashboards."""

    figure_names = []

    def __init__(self: DashboardBaseClass, idata: az.InferenceData, **params) -> None:
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

        super().__init__(**params)

    def _compute(self: DashboardBaseClass):
        raise NotImplementedError("To be implemented by the inheriting class.")

    def compute(self: DashboardBaseClass):
        """Compute the data needed for the dashboard for the selected random variable."""
        return self._compute()

    def _plot(self: DashboardBaseClass, *args):
        raise NotImplementedError("To be implemented by the inheriting class.")

    def plot(self: DashboardBaseClass, *args):
        """Plots for the dashboard."""
        return self._plot(*args)

    def show(self: DashboardBaseClass) -> None:
        """Shows the dashboard in a Jupyter environment.

        Returns
        -------
        None
            Renders the dashboard directly in the notebook.
        """
        return pn.Row(self.param, self.plot)
