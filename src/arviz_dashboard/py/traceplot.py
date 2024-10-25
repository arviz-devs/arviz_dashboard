from pathlib import Path

import anywidget
import traitlets
from xarray.core.datatree import DataTree

from arviz_dashboard.py.models import PosteriorModel


class Traceplot(anywidget.AnyWidget, PosteriorModel):
    _esm = Path(__file__).parent.parent.resolve() / "static" / "traceplot.js"
    data = traitlets.Dict().tag(sync=True)

    def __init__(self, idata: DataTree) -> None:
        data = self.parse_posterior_data(idata=idata)
        super().__init__(data=data)
