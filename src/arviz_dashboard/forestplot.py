from __future__ import annotations

from pathlib import Path

import anywidget
import traitlets


class Forestplot(anywidget.AnyWidget):
    _esm = Path(__file__).parent.resolve() / "static" / "widget.js"
    posterior = traitlets.Dict().tag(sync=True)

    def __init__(self: Forestplot, posterior: dict) -> None:
        super().__init__(posterior=posterior)
