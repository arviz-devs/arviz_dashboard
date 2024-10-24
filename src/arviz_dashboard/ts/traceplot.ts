import * as Plot from "@observablehq/plot"
import {density1d} from "fast-kde/src/density1d"

import {linearRange} from "arvizjs/src/lib/stats/array"
import {getNestedObject} from "./utils"

function determine_num_grid_columns(dropdowns) {
    let num_dimensions = 0
    for (let data_variable in dropdowns) {
        const dimensions = Object.keys(dropdowns[data_variable]).length
        num_dimensions = Math.max(num_dimensions, dimensions)
    }
    const num_columns = num_dimensions + 1
    return num_columns
}

function create_grid_template_string(num_columns) {
    let grid_template = ""
    for (let i = 0; i < num_columns; i++) {
        const percentage = Math.floor(90 * (1 / num_columns))
        grid_template += `${percentage}% `
    }
    return grid_template
}

function render({model, el}) {
    const data = model.get("data")
    window.data = data
    const dropdowns = data.dropdowns
    const posterior = data.posterior
    const num_chains = data.num_chains
    const num_draws = data.num_draws
    const num_grid_columns = determine_num_grid_columns(dropdowns)
    const grid_template_columns = create_grid_template_string(num_grid_columns)

    // Create a div for the traceplot.
    const traceplot_div = document.createElement("div")
    traceplot_div.style.width = "100%"
    traceplot_div.style.height = "600px"

    // Create a div for all the select dropdowns.
    const select_div = document.createElement("div")
    select_div.id = "select-div"
    select_div.style.width = "100%"
    select_div.style.height = "75px"
    select_div.style.display = "grid"
    select_div.style.gridTemplateColumns = grid_template_columns
    select_div.style.columnGap = "10px"

    // Create a div for the data variables select.
    const data_variable_div = document.createElement("div")
    data_variable_div.id = "data-variable-div"
    data_variable_div.style.display = "grid"
    data_variable_div.style.gridTemplateRows = "60% 40%"
    data_variable_div.addEventListener("change", add_dimensions)
    const data_variable_title = document.createElement("p")
    data_variable_title.innerHTML = "<b>Data variable</b>"
    data_variable_div.appendChild(data_variable_title)
    const data_variable_select = document.createElement("select")
    data_variable_select.id = "data-variables-select"
    data_variable_select.name = "data variables"
    data_variable_select.addEventListener("change", update_plot)
    for (let data_variable in dropdowns) {
        data_variable_select.add(new Option(data_variable))
    }
    data_variable_div.appendChild(data_variable_select)
    select_div.appendChild(data_variable_div)

    // Create a div for the extra dimension(s) of the selected data variable.
    const extra_dimensions_div = document.createElement("div")
    extra_dimensions_div.id = "extra-dimensions-div"
    extra_dimensions_div.style.gridColumn = `2 / span ${num_grid_columns - 1}`
    select_div.appendChild(extra_dimensions_div)

    // Append the selects to the element.
    el.appendChild(select_div)

    // Create a div for the chains.
    const chains_div = document.createElement("div")
    chains_div.style.width = "100%"
    chains_div.style.height = "25px"
    chains_div.style.display = "flex"
    chains_div.style.flexDirection = "row"
    chains_div.style.alignItems = "center"
    chains_div.style.marginTop = "10px"
    for (let chain_num of [...Array(num_chains).keys()]) {
        const chain_checkbox = document.createElement("input")
        chain_checkbox.type = "checkbox"
        chain_checkbox.name = "input"
        chain_checkbox.id = `chain-${chain_num}`
        chain_checkbox.checked = true
        chain_checkbox.addEventListener("change", update_plot)
        const chain_label = document.createElement("label")
        chain_label.htmlFor = `chain-${chain_num}`
        chain_label.innerHTML = `Chain: ${chain_num}`
        chains_div.appendChild(chain_checkbox)
        chains_div.appendChild(chain_label)
    }

    // Append the chains to the element.
    el.appendChild(chains_div)

    // Create a div for the figures.
    const plot_div = document.createElement("div")
    plot_div.style.width = "100%"
    plot_div.style.height = "600px"
    plot_div.style.display = "flex"
    plot_div.style.flexDirection = "row"

    // Append the plot to the element.
    el.appendChild(plot_div)

    // Callbacks
    function add_dimensions() {
        extra_dimensions_div.innerHTML = ""
        const data_variable = document.getElementById("data-variables-select") as HTMLSelectElement
        if (data_variable !== null) {
            const data_variable_name = data_variable.value
            const coordinates = dropdowns[data_variable_name]
            const coordinate_keys = Object.keys(coordinates)
            const extra_dimension_div = document.createElement("div")
            extra_dimension_div.style.height = "100%"
            extra_dimension_div.style.display = "grid"
            extra_dimension_div.style.gridTemplateRows = "60% 40%"
            extra_dimension_div.style.gridTemplateColumns = create_grid_template_string(
                num_grid_columns - 1,
            )
            extra_dimension_div.style.columnGap = "10px"
            for (let i = 0; i < coordinate_keys.length; i++) {
                const coordinate_name = coordinate_keys[i]
                extra_dimension_div.id = `coordinate-${coordinate_name}-div`
                // Create a div for each additional dimension associated with the selected data
                // variable.
                extra_dimension_div.style.gridColumn = `${i + 1}`

                // Title for the additional dimension.
                const extra_dimension_title = document.createElement("p")
                extra_dimension_title.id = `coordinate-${coordinate_name}-title`
                extra_dimension_title.innerHTML = `<b>${coordinate_name}</b>`
                extra_dimension_div.appendChild(extra_dimension_title)

                // Create a select for all the additional dimensions.
                const extra_dimension_select = document.createElement("select")
                extra_dimension_select.id = `coordinate-${coordinate_name}-select`
                extra_dimension_select.style.gridColumn = `${i + 1}`
                extra_dimension_select.style.gridRow = "2"
                extra_dimension_select.addEventListener("change", update_plot)

                // Add the options for each additional dimension.
                const dimensions = dropdowns[data_variable_name][coordinate_name]
                if (Object.keys(dimensions).length !== 0) {
                    for (let dimension of dimensions) {
                        extra_dimension_select.add(new Option(dimension))
                    }
                }
                extra_dimension_div.appendChild(extra_dimension_select)
                extra_dimensions_div.appendChild(extra_dimension_div)
            }
        }
        select_div.appendChild(extra_dimensions_div)
        update_plot()
    }
    add_dimensions()

    function update_plot() {
        // Find the dropdown element for the model's data variables.
        const data_variable_select = document.getElementById(
            "data-variables-select",
        ) as HTMLSelectElement
        // Determine what the selected data variable is.
        const data_variable_name = data_variable_select?.value

        // Find all dropdown elements associated with the chosen data variable.
        const extra_dimensions = document.querySelectorAll('[id^="coordinate-"][id$=-select]')
        const extra_dimensions_titles = document.querySelectorAll('[id^="coordinate-"][id$=-title]')
        // Cycle through all the dropdowns and get their values. We will use these
        // to find the data in the nested posterior data object.
        let extra_dimension_names = new Array()
        let coordinate_names = new Array()
        for (let i = 0; i < extra_dimensions.length; i++) {
            const extra_dimension = extra_dimensions[i] as HTMLSelectElement
            const extra_dimension_name = extra_dimension?.value
            extra_dimension_names.push(extra_dimension_name)
            const extra_dimension_title = extra_dimensions_titles[i] as HTMLElement
            const coordinate = document.getElementById(
                `coordinate-${extra_dimension_title.textContent}-title`,
            )
            const coordinate_name = coordinate?.textContent
            coordinate_names.push(coordinate_name)
            coordinate_names.push(extra_dimension_name)
        }

        // Set a few plot aesthetics for the traceplot.
        let opacity = 0.5
        let tip = true

        // Determine the x-range from the number of draws found in the posterior data.
        let x = linearRange(0, num_draws, 1, false)
        let y_name = `${data_variable_name}`
        let chain_lines = new Array()
        let kde_lines = new Array()
        for (let chain_num = 0; chain_num < num_chains; chain_num++) {
            // Change the opacity of different chains based on which ones are selected. If there
            // are chains not selected, then also do not show the tooltip.
            let checkbox = document.getElementById(`chain-${chain_num}`) as HTMLInputElement
            opacity = checkbox?.checked ? 0.5 : 0.1
            tip = opacity === 0.5 ? true : false

            // Get the y-values for the traceplot from the posterior data.
            let y = new Array()
            if (extra_dimensions.length !== 0) {
                y = getNestedObject(
                    posterior,
                    [data_variable_name].concat([...coordinate_names, "chain", chain_num]),
                )
            } else {
                y = posterior[data_variable_name]["chain"][chain_num]
            }

            // Plot the traceplot data.
            let plot_data = new Array()
            for (let i = 0; i < x.length; i++) {
                let datum = {Draw: x[i], chain: `Chain: ${chain_num}`}
                datum[y_name] = y[i]
                plot_data.push(datum)
            }
            chain_lines.push(
                Plot.line(plot_data, {
                    x: "Draw",
                    y: y_name,
                    stroke: "chain",
                    tip: tip,
                    strokeOpacity: opacity,
                }),
            )

            // Compute the 1D KDE of the data.
            const kde = density1d(y, {bins: 512})
            const points: {x: number; y: number}[] = Array.from(kde)
            const kde_x = new Array()
            const kde_y = new Array()
            for (let i = 0; i < points.length; i++) {
                kde_x.push(points[i].x)
                kde_y.push(points[i].y)
            }

            // Plot the KDE.
            let kde_plot_data = new Array()
            for (let i = 0; i < kde_x.length; i++) {
                let datum = {x: kde_x[i], y: kde_y[i], chain: `Chain: ${chain_num}`}
                kde_plot_data.push(datum)
            }
            kde_lines.push(
                Plot.line(kde_plot_data, {
                    x: "x",
                    y: "y",
                    stroke: "chain",
                    tip: tip,
                    strokeOpacity: opacity,
                }),
            )
        }

        // Create the final traceplot.
        let traceplot = Plot.plot({
            grid: true,
            inset: 10,
            marks: [Plot.frame(), chain_lines],
        })
        if (plot_div.lastChild != null) {
            plot_div.lastChild.remove()
        }
        // Create the final KDE.
        let kdeplot = Plot.plot({
            grid: true,
            inset: 10,
            marks: [Plot.frame(), kde_lines],
        })
        if (plot_div.lastChild != null) {
            plot_div.lastChild.remove()
        }
        plot_div.appendChild(kdeplot)
        plot_div.appendChild(traceplot)
    }
    update_plot()
}

export default {render}
