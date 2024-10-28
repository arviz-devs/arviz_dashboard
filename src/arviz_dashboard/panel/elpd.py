"""
Module for creating a dashboard to compare ELPD (Expected Log Point Density) of models.
"""

import arviz as az
import bokeh.io
import matplotlib.pyplot as plt
import panel as pn
from bokeh.palettes import Category10
from bokeh.plotting import figure

# Set up Bokeh for notebook output
bokeh.io.reset_output()
bokeh.io.output_notebook()
pn.extension()


def dashboard_elpd(idatas_cmp: dict) -> None:
    """
    Create a dashboard for comparing ELPD (Expected Log Point Density) between models.

    Parameters
    ----------
    idatas_cmp : dict
        A dictionary containing comparison data for models.
    """
    models = list(idatas_cmp.keys())
    model_selection1 = pn.widgets.Select(value=models[0], options=models, name="Model 1")
    model_selection2 = pn.widgets.Select(value=models[1], options=models, name="Model 2")
    thre_slider = pn.widgets.FloatSlider(
        name="Threshold Value",
        start=1,
        end=3,
        step=0.1,
        value=2,
        width=200,
    )
    thre_sel = pn.widgets.Select(
        value=None,
        options=["standard deviation"],
        name="Threshold Type",
        width=200,
    )
    ic_group = pn.widgets.RadioBoxGroup(
        name="Information Criterion",
        options=["loo", "waic"],
        inline=True,
    )
    str_pane = pn.pane.Str("", styles={"font-size": "12pt", "color": "red"})

    @pn.depends(
        model_selection1.param.value,
        model_selection2.param.value,
        thre_slider.param.value,
        ic_group.param.value,
    )
    def get_elpd_plot(
        model_selection1: str,
        model_selection2: str,
        thre_slider: float,
        ic_group: str,
    ):
        """
        Generate an ELPD plot for the selected models.

        Parameters
        ----------
        model_selection1 : str
            The first model selected for comparison.
        model_selection2 : str
            The second model selected for comparison.
        thre_slider : float
            The threshold value for the ELPD plot.
        ic_group : str
            The information criterion to be used for the plot.

        Returns
        -------
        figure
            A Bokeh figure object representing the ELPD plot.
        """
        if model_selection1 == model_selection2:
            str_pane.object = "Please try again. You can only compare two different models."
            return None

        dict_cmp = {x: idatas_cmp[x] for x in [model_selection1, model_selection2]}
        _, scatter_plt = plt.subplots()

        # Generate the plot
        az.plot_elpd(
            dict_cmp,
            plot_kwargs={"marker": "."},
            threshold=thre_slider,
            ic=ic_group,
            ax=scatter_plt,
        )
        y_min, y_max = scatter_plt.get_ylim()
        scatter_plt.set_ylim(round(y_min, 1), round(y_max, 1))

        plt.close()
        return scatter_plt.figure

    @pn.depends(
        model_selection1.param.value,
        model_selection2.param.value,
        thre_slider.param.value,
        ic_group.param.value,
    )
    def get_stacked_bar_plot(
        model_selection1: str,
        model_selection2: str,
        thre_slider: float,
        ic_group: str,
    ):
        """
        Generate a stacked bar plot summarizing positive and negative observations from the ELPD plot.

        Parameters
        ----------
        model_selection1 : str
            The first model selected for comparison.
        model_selection2 : str
            The second model selected for comparison.
        thre_slider : float
            The threshold value for the stacked bar plot.
        ic_group : str
            The information criterion to be used for the plot.

        Returns
        -------
        figure
            A Bokeh figure object representing the stacked bar plot.
        """
        if model_selection1 == model_selection2:
            str_pane.object = "Please try again. You can only compare two different models."
            return None

        dict_cmp = {x: idatas_cmp[x] for x in [model_selection1, model_selection2]}
        scatter_plt = az.plot_elpd(
            dict_cmp,
            plot_kwargs={"marker": "."},
            threshold=thre_slider,
            ic=ic_group,
        )
        scatter_ax = scatter_plt.figure.get_axes()[0]
        plt.close()

        # Extract observation counts
        y_ob = scatter_ax.collections[0].get_offsets()[:, 1]
        neg_count = sum(1 for y_ob_point in y_ob if y_ob_point < 0)
        pos_count = sum(1 for y_ob_point in y_ob if y_ob_point > 0)

        # Prepare data for the stacked bar plot
        data = {
            "standard": ["count"],
            "positive": [pos_count],
            "negative": [neg_count],
        }
        tooltips = "$name @standard: @$name"

        p = figure(
            x_range=["count"],
            height=300,
            width=200,
            title="Summary of Observations",
            tooltips=tooltips,
            toolbar_location=None,
            tools="",
        )
        p.vbar_stack(
            ["positive", "negative"],
            x="standard",
            width=0.2,
            color=[Category10[10][0], Category10[10][1]],
            source=data,
        )
        p.y_range.start = 0
        p.xgrid.grid_line_color = None
        p.axis.minor_tick_line_color = None
        p.outline_line_color = None
        p.toolbar.logo = None

        return p

    @pn.depends(model_selection1.param.value, model_selection2.param.value)
    def get_compare_plot(model_selection1: str, model_selection2: str):
        """
        Compare models using the ELPD values and generate a comparison plot.

        Parameters
        ----------
        model_selection1 : str
            The first model selected for comparison.
        model_selection2 : str
            The second model selected for comparison.

        Returns
        -------
        figure
            A Bokeh figure object representing the model comparison plot.
        """
        if model_selection1 == model_selection2:
            str_pane.object = "Please try again. You can only compare two different models."
            return None

        dict_cmp = {x: idatas_cmp[x] for x in [model_selection1, model_selection2]}
        model_compare = az.compare(dict_cmp)
        compare_plt = az.plot_compare(model_compare, backend="bokeh", show=False)
        compare_plt.width = 400
        compare_plt.height = 300

        return compare_plt

    # Display the dashboard
    display(
        pn.Column(
            pn.Row(model_selection1, model_selection2),
            pn.Row(thre_sel, pn.Column("Information Criterion:", ic_group)),
            thre_slider,
            str_pane,
            pn.Row(get_elpd_plot, get_stacked_bar_plot, get_compare_plot),
        ).servable(),
    )
