import {interval as hdiInterval} from "arvizjs/src/lib/stats/highestDensityInterval"
import {mean} from "arvizjs/src/lib/stats/pointStatistics"
import {getNestedObject} from "./utils"

function render({model, el}) {
    const data = model.get("data")
    const posterior = data.posterior
    const hierarchy = data.dropdowns

    const forest_data = compute_forestplot_data(posterior, 0.89)
    window.forest = forest_data

    // Create a div for the forestplot.
    const forestplot_div = document.createElement("div")
    forestplot_div.style.width = "100%"
    forestplot_div.style.height = "600px"

    // Create a div for all the select dropdowns.
    const select_div = document.createElement("div")
    select_div.id = "select-div"
    select_div.style.width = "100%"
    select_div.style.height = "75px"
    select_div.style.display = "grid"
    // select_div.style.gridTemplateColumns = grid_template_columns
    select_div.style.columnGap = "10px"

    // Create a div for the data variables select.
    const data_variable_div = document.createElement("div")
    data_variable_div.id = "data-variable-div"
    data_variable_div.style.display = "grid"
    data_variable_div.style.gridTemplateRows = "60% 40%"
    // data_variable_div.addEventListener("change", add_dimensions)
    const data_variable_title = document.createElement("p")
    data_variable_title.innerHTML = "<b>Data variable</b>"
    data_variable_div.appendChild(data_variable_title)
    const data_variable_select = document.createElement("select")
    data_variable_select.id = "data-variables-select"
    data_variable_select.name = "data variables"
    // data_variable_select.addEventListener("change", update_plot)
    for (let data_variable in hierarchy) {
        data_variable_select.add(new Option(data_variable))
    }
    data_variable_div.appendChild(data_variable_select)
    select_div.appendChild(data_variable_div)

    // Append the selects to the element.
    el.appendChild(select_div)
}

function flatten_posterior_dimensions(posterior) {
    function is_object(dimension) {
        return dimension && typeof dimension === "object" && !Array.isArray(dimension)
    }
    function add_delimiter(parent, child) {
        return parent ? `${parent}.${child}` : child
    }
    function paths(obj = {}, head = "") {
        return Object.entries(obj).reduce((product, [key, value]) => {
            let full_path = add_delimiter(head, key)
            return is_object(value) && head != "chain"
                ? product.concat(paths(value, full_path))
                : product.concat(full_path)
        }, [])
    }

    return paths(posterior)
}

function chunk(array, size) {
    const chunkedArray = []
    let index = 0
    while (index < array.length) {
        chunkedArray.push(array.slice(index, size + index))
        index += size
    }
    return chunkedArray
}

function compute_forestplot_data(posterior, hdiProbability = 0.89) {
    const posterior_paths = flatten_posterior_dimensions(posterior)
    const flat_posterior = new Object()
    for (let posterior_path of posterior_paths) {
        const posterior_path_tokens = posterior_path.split(".")
        const chain_data = getNestedObject(posterior, posterior_path_tokens)
        const data_variable = posterior_path_tokens.splice(0, 1)[0]
        // Remove the "chain" entry.
        const chain_index = posterior_path_tokens.indexOf("chain")
        posterior_path_tokens.splice(chain_index, 1)
        // Now create chunked arrays. This is going to give us something like
        // [[dimension, dim_value], ...]
        const groups = chunk(posterior_path_tokens, 2)
        // Next we concatenate the grouped values together.
        const dimension_value_names = new Array()
        for (const group of groups) {
            console.log(group)
            const dimension_value = group.join("=")
            dimension_value_names.push(dimension_value)
        }
        const all_dimensions_and_values = dimension_value_names.join(",")
        console.log(all_dimensions_and_values)
        let key = ""
        if (!all_dimensions_and_values) {
            key = `${data_variable}`
        } else {
            key = `${data_variable}[${all_dimensions_and_values}]`
        }
        flat_posterior[key] = chain_data
    }
    return flat_posterior
}

export default {render}
