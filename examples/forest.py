import arviz as az
import bokeh.io
import panel as pn
from IPython.display import display

bokeh.io.reset_output()
bokeh.io.output_notebook()

pn.extension()


class ForestDashboard:
    def __init__(self) -> None:
        self.a = 10

def dashboard_forest(idatas_cmp):
    # define the widgets

    multi_select = pn.widgets.MultiSelect(
        name="ModelSelect",
        options=list(idatas_cmp.keys()),
        value=["mA"],
    )
    thre_slider = pn.widgets.FloatSlider(
        name="HDI Probability", start=0, end=1, step=0.05, value=0.7, width=200
    )
    truncate_checkbox = pn.widgets.Checkbox(name="Ridgeplot Truncate")
    ridge_quant = pn.widgets.RangeSlider(
        name="Ridgeplot Quantiles",
        start=0,
        end=1,
        value=(0.25, 0.75),
        step=0.01,
        width=200,
    )
    op_slider = pn.widgets.FloatSlider(
        name="Ridgeplot Overlap", start=0, end=1, step=0.05, 
        value=0.7, width=200
    )

    # construct widget
    @pn.depends(
        multi_select.param.value,
        thre_slider.param.value,
    )
    def get_forest_plot(
        multi_select,
        thre_slider,
    ):
        # generate graph
        data = []
        for model_ in multi_select:
            data.append(idatas_cmp[model_])

        forest_plt = az.plot_forest(
            data,
            model_names=multi_select,
            kind="forestplot",
            hdi_prob=thre_slider,
            backend="bokeh",
            figsize=(9, 9),
            show=False,
            combined=True,
            colors="cycle",
        )
        return forest_plt[0][0]

    @pn.depends(
        multi_select.param.value,
        thre_slider.param.value,
        truncate_checkbox.param.value,
        ridge_quant.param.value,
        op_slider.param.value,
    )
    def get_ridge_plot(
        multi_select,
        thre_slider,
        truncate_checkbox,
        ridge_quant,
        op_slider,
    ):
        # calculate the ridgeplot_quantiles
        temp_quant = list(ridge_quant)
        quant_ls = temp_quant
        quant_ls.sort()
        avg_quant = sum(temp_quant) / 2
        if quant_ls[0] < 0.5 and quant_ls[1] > 0.5:
            quant_ls.append(0.5)
            quant_ls.sort()
        else:
            quant_ls.append(avg_quant)
            quant_ls.sort()

        # generate graph
        data = []
        for model_ in multi_select:
            data.append(idatas_cmp[model_])

        ridge_plt = az.plot_forest(
            data,
            model_names=multi_select,
            kind="ridgeplot",
            hdi_prob=thre_slider,
            ridgeplot_truncate=truncate_checkbox,
            ridgeplot_quantiles=quant_ls,
            ridgeplot_overlap=op_slider,
            backend="bokeh",
            figsize=(9, 9),
            show=False,
            combined=True,
            colors="white",
        )
        return ridge_plt[0][0]

    plot_result_1 = pn.Row(get_forest_plot)
    plot_result_2 = pn.Column(
        pn.Row(truncate_checkbox),
        pn.Row(ridge_quant, op_slider),
        get_ridge_plot,
    )

    # show up
    display(
        pn.Column(
            pn.Row(multi_select),
            thre_slider,
            # pn.Row(variables_selection, update_coords),
            pn.Tabs(
                ("Forest_Plot", plot_result_1),
                (
                    "Rdiget_Plot",
                    plot_result_2,
                ),
            ),
        ).servable(),
    )
