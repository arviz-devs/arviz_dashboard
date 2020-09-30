"""Streaming functionality."""
import pandas as pd
import panel as pn
import streamz
from bokeh.plotting import ColumnDataSource, figure

__all__ = ["get_streaming_components"]


def get_streaming_components(structure, y, x="draw", timed_window=0.1, plot_dict=None):
    """Streaming interface.

    Parameters
    ----------
    structure: pd.DataFrame
        Empty DataFrame with the correct input dtypes.

    Returns
    -------
    streamz.Stream
    panel.pane

    Example
    -------
    >> structure = pd.DataFrame({"x" : np.array([], dtype=float)})
    >> pane, stream = get_streaming_components(structure)
    >> pane.app()
    >> for sample in model:
           stream.emit(sample)
    """
    if plot_dict is None:
        plot_dict = {}

    cds = ColumnDataSource(structure)
    p = figure(width=400, height=200)
    p.line(x="draw", y=y, source=cds, **plot_dict)

    def update_source(data, cds, p):
        if data:
            data = pd.concat(data, axis=0)
            cds.stream(data)
        return p

    source = streamz.Stream()
    stream = source.timed_window(timed_window).map(update_source, cds=cds, p=p)
    pane = pn.pane.Streamz(stream, always_watch=True)
    return pane, source
