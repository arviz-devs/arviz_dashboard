import arviz as az
import bokeh.io
import matplotlib.pyplot as plt
import panel as pn

bokeh.io.reset_output()
bokeh.io.output_notebook()


pn.extension()


def dashboard_ppc(idatas_cmp):
    model_selection1 = pn.widgets.Select(
        value=None, options=list(idatas_cmp.keys()), name="Model1"
    )
    thre_slider = pn.widgets.FloatSlider(
        name="Threshold Value", start=0, end=1, step=0.05, value=0.7, width=200
    )

    @pn.depends(model_selection1.param.value, thre_slider.param.value)
    def get_ppc_plot(model_selection1, thre_slider):
        ppc_plt = az.plot_ppc(
            idatas_cmp[model_selection1],
            data_pairs={"y": "y"},
            backend="bokeh",
            show=False,
            observed_rug=True,
        )
        vars(
            vars(vars(ppc_plt[0][0])["_property_values"]["renderers"][2])[
                "_property_values"
            ]["glyph"]
        )["_property_values"]["line_color"] = "colors"

        ##get the list of x valus corresponded to the khat plot
        observed_rug_ls = list(
            vars(
                vars(vars(ppc_plt[0][0])["_property_values"]["renderers"][2])[
                    "_property_values"
                ]["data_source"]
            )["_property_values"]["data"]["_"]
        )

        ##generate the list of colors
        ### step1 get the khat_color
        loo_radon = az.loo(idatas_cmp[model_selection1], pointwise=True)
        khat_plt = az.plot_khat(loo_radon, show_bins=True, backend="bokeh", show=False)

        colors = []
        glyph_len = len(vars(khat_plt)["_property_values"]["renderers"])

        for location in range(glyph_len):
            glyph = vars(vars(khat_plt)["_property_values"]["renderers"][location])[
                "_property_values"
            ]["glyph"]
            if str(glyph)[0:4] != "Text":
                y_value = vars(glyph)["_property_values"]["y"]
                if y_value > thre_slider:
                    colors.append("#D81B60")

                else:
                    colors.append("#1E88E5")

        ### step2 sort the x values
        temp_rug_ls = sorted(observed_rug_ls)
        rug_color = dict()
        for id_ in range(len(temp_rug_ls)):
            rug_color[temp_rug_ls[id_]] = colors[id_]

        ## step3 get the final colors
        colors_final = []
        for rug in observed_rug_ls:
            colors_final.append(rug_color[rug])

        vars(
            vars(vars(ppc_plt[0][0])["_property_values"]["renderers"][2])[
                "_property_values"
            ]["data_source"]
        )["_property_values"]["data"]["colors"] = colors_final

        return ppc_plt[0][0]

    @pn.depends(model_selection1.param.value, thre_slider.param.value)
    def get_khat_plot(model_selection1, thre_slider):
        loo_radon = az.loo(idatas_cmp[model_selection1], pointwise=True)
        khat_plt = az.plot_khat(loo_radon, show_bins=True, backend="bokeh", show=False)

        colors = []
        glyph_len = len(vars(khat_plt)["_property_values"]["renderers"])

        for location in range(glyph_len):
            glyph = vars(vars(khat_plt)["_property_values"]["renderers"][location])[
                "_property_values"
            ]["glyph"]
            if str(glyph)[0:4] != "Text":
                y_value = vars(glyph)["_property_values"]["y"]
                if y_value > thre_slider:
                    colors.append("#D81B60")

                else:
                    colors.append("#1E88E5")

        khat_plt_update = az.plot_khat(
            loo_radon, color=colors, show_bins=True, backend="bokeh", show=False
        )
        # khat_plt_update.width=400
        # khat_plt_update.height=300
        return khat_plt_update

    # show up
    display(
        pn.Column(
            pn.Row(model_selection1), thre_slider, pn.Row(get_ppc_plot, get_khat_plot)
        ).servable()
    )
