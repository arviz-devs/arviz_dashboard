from bokeh.plotting import figure


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
