from arviz.data.inference_data import InferenceData
from bokeh.models.sources import ColumnDataSource
from bokeh.plotting import figure


def create_sources(idata: InferenceData) -> ColumnDataSource:
    posterior = idata["posterior"]
