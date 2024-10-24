from pathlib import Path

import anywidget
import traitlets
from xarray.core.datatree import DataTree

from arviz_dashboard.py.models import PosteriorModel


class Traceplot(anywidget.AnyWidget, PosteriorModel):
    _esm = Path(__file__).parent.parent.resolve() / "static" / "traceplot.js"
    data = traitlets.Dict().tag(sync=True)
    # hierarchy = traitlets.Dict().tag(sync=True)
    # num_chains = traitlets.Integer().tag(sync=True)
    # num_draws = traitlets.Integer().tag(sync=True)

    def __init__(self, idata: DataTree) -> None:
        data = self.parse_posterior_data(idata=idata)
        # self.num_chains = len(idata["posterior"].coords["chain"])
        # self.num_draws = len(idata["posterior"].coords["draw"])
        super().__init__(data=data)
