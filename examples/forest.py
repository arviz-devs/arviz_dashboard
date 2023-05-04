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
    
    def __init__(self, idatas_cmp, **params) -> None:
        
        self.idatas_cmp = idatas_cmp
        self.default_model = list(self.idatas_cmp.keys())[0]
        self.param["model"].objects = list(self.idatas_cmp.keys())
        self.param["model"].default = self.default_model
        self.param["data_variable"].objects  = list(self.idatas_cmp[self.default_model].posterior.data_vars.variables)
        super().__init__(**params)
    

    @param.depends("model", watch=True)
    def _update_data_variables(self):
        data_variables = list(self.idatas_cmp[self.model].posterior.data_vars.variables)
        self.param["data_variable"].objects = data_variables
        if self.data_variable not in data_variables:
            self.data_variable = data_variables[0]

    @param.depends("data_variable", watch=True)
    def _update_coordinates(self):
        if (
            self.idatas_cmp[self.model]
            .posterior.data_vars.variables[self.data_variable][0][0]
            .size
            > 1
        ):
            coor_variables = list(
                self.idatas_cmp[self.model].posterior.indexes["school"]
            )
        else:
            coor_variables = [""]
        self.param["coor_variable"].objects = coor_variables
        if self.coor_variable not in coor_variables:
            self.coor_variable = coor_variables[0]


class ForestDashboard(ModelVar):
    def __init__(self, idatas_cmp) -> None:
        self.idatas_cmp = idatas_cmp
        super().__init__(self.idatas_cmp)

    def dashboard_forest(self):
        # define the widgets
        multi_select = pn.widgets.MultiSelect(
            name="ModelSelect",
            options=list(self.idatas_cmp.keys()),
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
            name="Ridgeplot Overlap", start=0, end=1, step=0.05, value=0.7, width=200
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
                data.append(self.idatas_cmp[model_])

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
                data.append(self.idatas_cmp[model_])

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
                pn.Row(self.param.model,self.param.data_variable,self.param.coor_variable ),
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
