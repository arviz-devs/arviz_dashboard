"""Forest visualization."""

from pathlib import Path

import anywidget
import traitlets
from xarray.core.datatree import DataTree

from arviz_dashboard.py.models import PosteriorModel


class Forestplot(anywidget.AnyWidget, PosteriorModel):
    """Forest visualization."""

    _esm = Path(__file__).parent.parent.resolve() / "static" / "forestplot.js"
    data = traitlets.Dict().tag(sync=True)

    def __init__(self, dt: DataTree) -> None:
        parsed_data = self.parse_posterior_data(dt=dt)
        super().__init__(data=parsed_data)


def plot_forest(dt: DataTree) -> Forestplot:
    """Forest visualization.

    Parameters
    ----------
    dt : DataTree

    Returns
    -------
    Forestplot
    """
    return Forestplot(dt=dt)
