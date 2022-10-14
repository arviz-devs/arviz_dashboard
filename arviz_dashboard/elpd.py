import arviz as az
import bokeh.io
import matplotlib.pyplot as plt
import panel as pn
from bokeh.palettes import Category10
from bokeh.plotting import figure

bokeh.io.reset_output()
bokeh.io.output_notebook()


pn.extension()


def dashboard_elpd(idatas_cmp):
    models = list(idatas_cmp.keys())
    model_selection1 = pn.widgets.Select(value=models[0], options=models, name="Model1")
    model_selection2 = pn.widgets.Select(value=models[1], options=models, name="Model2")
    thre_slider = pn.widgets.FloatSlider(
        name="Threshold Value", start=1, end=3, step=0.1, value=2, width=200
    )
    thre_sel = pn.widgets.Select(
        value=None, options=list(["standard deviation"]), name="Threshold Type", width=200
    )
    ic_group = pn.widgets.RadioBoxGroup(
        name="Information Criterion", options=["loo", "waic"], inline=True
    )

    global str_pane
    str_pane = pn.pane.Str("", style={"font-size": "12pt", "color": "red"})

    # return the scatter_plot(usually with one hundred observations)
    @pn.depends(
        model_selection1.param.value,
        model_selection2.param.value,
        thre_slider.param.value,
        ic_group.param.value,
    )
    def get_elpd_plot(model_selection1, model_selection2, thre_slider, ic_group):
        global old_model_select1
        global old_model_select2

        old_model_select1 = ""
        old_model_select2 = ""

        if model_selection1 != model_selection2:
            if (
                old_model_select1 != ""
                and old_model_select1 == model_selection1
                and old_model_select2 == model_selection2
            ):
                str_pane.object = ""
                _, scatter_plt = plt.subplots()
                dict_cmp = {x: idatas_cmp[x] for x in [model_selection1, model_selection2]}

                # if the model selection did not change, we only need to update the y_min and y_max
                az.plot_elpd(
                    dict_cmp,
                    plot_kwargs={"marker": "."},
                    threshold=thre_slider,
                    ic=ic_group,
                    ax=scatter_plt,
                )
                scatter_plt.set_ylim(y_min, y_max)

            else:
                str_pane.object = ""
                _, scatter_plt = plt.subplots()
                dict_cmp = {x: idatas_cmp[x] for x in [model_selection1, model_selection2]}

                # store the model_selection info
                old_model_select1 = model_selection1
                old_model_select2 = model_selection2

                # create scatter_plt
                az.plot_elpd(
                    dict_cmp,
                    plot_kwargs={"marker": "."},
                    threshold=thre_slider,
                    ic=ic_group,
                    ax=scatter_plt,
                )
                y_min_og, y_max_og = scatter_plt.get_ylim()

                # if the model selection changed, we first need to get the default y_min and y_max
                y_min = round(y_min_og, 1)
                y_max = round(y_max_og, 1)
                scatter_plt.set_ylim(y_min, y_max)

            plt.close()
            return scatter_plt.figure
        else:
            str_pane.object = "Please try again. You can only compare two different models"

    @pn.depends(
        model_selection1.param.value,
        model_selection2.param.value,
        thre_slider.param.value,
        ic_group.param.value,
    )
    def get_stacked_bar_plot(model_selection1, model_selection2, thre_slider, ic_group):
        if model_selection1 != model_selection2:
            str_pane.object = ""
            dict_cmp = {x: idatas_cmp[x] for x in [model_selection1, model_selection2]}
            scatter_plt = az.plot_elpd(
                dict_cmp, plot_kwargs={"marker": "."}, threshold=thre_slider, ic=ic_group
            )
            scatter_ax = scatter_plt.figure.get_axes()[0]
            plt.close()

            # extract the points information from the elpd plot
            y_ob = scatter_ax.collections[0].get_offsets()[:, 1]
            neg_count = sum(1 for y_ob_point in list(y_ob) if y_ob_point < 0)
            pos_count = sum(1 for y_ob_point in list(y_ob) if y_ob_point > 0)

            # visualize the pos and neg in a stacked bar plot
            standard = ["count"]
            category = ["positive", "negative"]
            colors = [Category10[10][0], Category10[10][1]]

            data = {"standard": standard, "positive": [pos_count], "negative": [neg_count]}

            tooltips = "$name @standard: @$name"

            p = figure(
                x_range=standard,
                plot_height=300,
                plot_width=200,
                title="Summary of Observations",
                tooltips=tooltips,
                toolbar_location=None,
                tools="",
            )

            p.vbar_stack(category, x="standard", width=0.2, color=colors, source=data)

            p.y_range.start = 0
            p.x_range.range_padding = 0.1
            p.xgrid.grid_line_color = None
            p.axis.minor_tick_line_color = None
            p.outline_line_color = None
            p.toolbar.logo = None

            return p
        else:
            str_pane.object = "Please try again. You can only compare two different models"

    @pn.depends(model_selection1.param.value, model_selection2.param.value)
    def get_compare_plot(model_selection1, model_selection2):
        if model_selection1 != model_selection2:
            str_pane.object = ""
            dict_cmp = {x: idatas_cmp[x] for x in [model_selection1, model_selection2]}

            # create scatter_plt
            model_compare = az.compare(dict_cmp)
            compare_plt = az.plot_compare(model_compare, backend="bokeh", show=False)
            compare_plt.width = 400
            compare_plt.height = 300
            return compare_plt
        else:
            str_pane.object = "Please try again. You can only compare two different models"

    # show up
    display(
        pn.Column(
            pn.Row(model_selection1, model_selection2),
            pn.Row(thre_sel, pn.Column("Information Criterion:", ic_group)),
            thre_slider,
            str_pane,
            pn.Row(get_elpd_plot, get_stacked_bar_plot, get_compare_plot),
        ).servable()
    )
