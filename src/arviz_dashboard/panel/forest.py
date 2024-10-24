from __future__ import annotations

import arviz as az
import bokeh.io
import panel as pn
import param
from IPython.display import display

bokeh.io.reset_output()
bokeh.io.output_notebook()

pn.extension()


class ModelVar(param.Parameterized):
    model = param.Selector("")
    data_variable = param.Selector("")
    coor_variable = param.Selector("")
    index_key = ""

    def __init__(self, idata_dict: dict[str, az.InferenceData], **params) -> None:
        self.idata_dict = idata_dict
        self.models = list(self.idata_dict.keys())
        self.default_model = self.models[0]
        self.param["model"].objects = self.models
        self.param["model"].default = self.default_model
        self.param["data_variable"].objects = list(
            self.idata_dict[self.default_model].posterior.data_vars.variables
        )
        super().__init__(**params)

    @param.depends("model", watch=True)
    def _update_data_variables(self: ModelVar):
        data_variables = list(self.idata_dict[self.model].posterior.data_vars.variables)
        self.param["data_variable"].objects = data_variables
        if self.data_variable not in data_variables:
            self.data_variable = data_variables[0] if data_variables else None

    @param.depends("data_variable", watch=True)
    def _update_coordinates(self: ModelVar):
        if (
            self.idata_dict[self.model]
            .posterior.data_vars.variables[self.data_variable]
            .ndim
            > 2
        ):
            self.index_key = list(
                dict(self.idata_dict[self.model].posterior.dims).keys()
            )[2]
            coor_variables = list(
                self.idata_dict[self.model].posterior.indexes[self.index_key]
            )
        else:
            coor_variables = [""]
        self.param["coor_variable"].objects = coor_variables


class ForestDashboard(ModelVar):
    def __init__(self, idata_dict) -> None:
        self.idata_dict = idata_dict
        super().__init__(self.idata_dict)

    def dashboard_forest(self):
        # define the widgets
        model_ls = list(self.idata_dict.keys())
        models_selection_widget = pn.widgets.MultiSelect(
            name="ModelSelect",
            options=model_ls,
            value=[model_ls[0]],
        )
        hdi_slider = pn.widgets.FloatSlider(
            name="HDI Probability",
            start=0,
            end=1,
            step=0.05,
            value=0.7,
            width=200,
        )
        ridgeplot_truncate_checkbox = pn.widgets.Checkbox(name="Ridgeplot Truncate")
        ridgeplot_quantiles = pn.widgets.RangeSlider(
            name="Ridgeplot Quantiles",
            start=0,
            end=1,
            value=(0.25, 0.75),
            step=0.01,
            width=200,
        )
        ridgeplot_overlap_slider = pn.widgets.FloatSlider(
            name="Ridgeplot Overlap",
            start=0,
            end=1,
            step=0.05,
            value=0.7,
            width=200,
        )

        forestplot_rope_slider = pn.widgets.RangeSlider(
            name="Rope Range",
            start=-10,
            end=10,
            value=(2, 5),
            step=1,
            width=200,
        )

        # construct widget
        @pn.depends(
            models_selection_widget.param.value,
            hdi_slider.param.value,
            forestplot_rope_slider.param.value,
            self.param.data_variable,
            self.param.coor_variable,
        )
        def get_forest_plot(
            models_selection_widget: pn.widgets.MultiSelect,
            hdi_slider: pn.widgets.FloatSlider,
            forestplot_rope_slider: pn.widgets.RangeSlider,
            data_variable: param.Selector,
            coor_variable: param.Selector,
        ):
            # generate graph
            data = []
            for model in models_selection_widget:
                data.append(self.idata_dict[model])
            # add rope
            rope = {}
            # e.g. "school" is one dimension of the xarray.Variable
            idata_dim_dict = {}
            idata_dim_dict[self.index_key] = coor_variable
            idata_dim_dict["rope"] = forestplot_rope_slider
            rope[data_variable] = [idata_dim_dict]
            # print(rope)
            forest_plt = az.plot_forest(
                data,
                model_names=models_selection_widget,
                rope=rope,
                kind="forestplot",
                hdi_prob=hdi_slider,
                backend="bokeh",
                figsize=(9, 9),
                show=False,
                combined=True,
                colors="cycle",
            )
            # forest_plt is a narray as well as forest_plt[0],
            # thus we used forest_plt[0][0] to get the figure
            return forest_plt.base[0]

        @pn.depends(
            models_selection_widget.param.value,
            hdi_slider.param.value,
            ridgeplot_truncate_checkbox.param.value,
            ridgeplot_quantiles.param.value,
            ridgeplot_overlap_slider.param.value,
        )
        def get_ridge_plot(
            models_selection_widget: pn.widgets.MultiSelect,
            hdi_slider: pn.widgets.FloatSlider,
            ridgeplot_truncate_checkbox: pn.widgets.Checkbox,
            ridgeplot_quantiles: pn.widgets.RangeSlider,
            ridgeplot_overlap_slider: pn.widgets.FloatSlider,
        ):
            # calculate the ridgeplot_quantiles
            quant_ls = sorted(list(ridgeplot_quantiles))
            avg_quant = sum(quant_ls) / 2
            if quant_ls[0] < 0.5 and quant_ls[1] > 0.5:
                quant_ls.append(0.5)
                quant_ls.sort()
            else:
                quant_ls.append(avg_quant)
                quant_ls.sort()

            # generate graph
            data = []
            for model_ in models_selection_widget:
                data.append(self.idata_dict[model_])

            ridge_plt = az.plot_forest(
                data,
                model_names=models_selection_widget,
                kind="ridgeplot",
                hdi_prob=hdi_slider,
                ridgeplot_truncate=ridgeplot_truncate_checkbox,
                ridgeplot_quantiles=quant_ls,
                ridgeplot_overlap=ridgeplot_overlap_slider,
                backend="bokeh",
                figsize=(9, 9),
                show=False,
                combined=True,
                colors="white",
            )
            return ridge_plt.base[0]

        plot_result_1 = pn.Column(
            pn.WidgetBox(
                "add rope",
                pn.Row(
                    self.param.model,
                    self.param.data_variable,
                    self.param.coor_variable,
                ),
                forestplot_rope_slider,
            ),
            get_forest_plot,
        )
        plot_result_2 = pn.Column(
            pn.Row(ridgeplot_truncate_checkbox),
            pn.Row(ridgeplot_quantiles, ridgeplot_overlap_slider),
            get_ridge_plot,
        )
        # show up in jupyter env
        display(
            pn.Column(
                pn.Row(models_selection_widget),
                hdi_slider,
                # pn.Row(self.param),
                pn.Tabs(
                    ("Forest_Plot", plot_result_1),
                    (
                        "Rdiget_Plot",
                        plot_result_2,
                    ),
                ),
            ).servable(),
        )
