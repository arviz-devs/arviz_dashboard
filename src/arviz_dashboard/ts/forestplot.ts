import {interval as hdiInterval} from "arvizjs/src/lib/stats/highestDensityInterval"
import {mean} from "arvizjs/src/lib/stats/pointStatistics"
import {get_from_nested_object} from "./utils"

function render({model, el}) {
    const data = model.get("data")
    const posterior = data.posterior
    const hierarchy = data.dropdowns

    const flat_posterior = flatten_posterior(posterior)
    const forest_data = compute_forest_data(flat_posterior)
    window.forest_data = forest_data

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

function flatten_posterior_dimensions(posterior: Posterior): Array<string> {
    function is_object(dimension: any) {
        return dimension && typeof dimension === "object" && !Array.isArray(dimension)
    }
    function add_delimiter(parent: string, child: string): string {
        return parent ? `${parent}.${child}` : child
    }
    function paths(obj: Object = {}, head: string = "") {
        return Object.entries(obj).reduce((product, [key, value]) => {
            let full_path = add_delimiter(head, key)
            return is_object(value) && head != "chain"
                ? product.concat(paths(value, full_path))
                : product.concat(full_path)
        }, [])
    }

    return paths(posterior)
}

function chunk(array: Array<string>, size: number) {
    const chunked_array = new Array()
    let index = 0
    while (index < array.length) {
        chunked_array.push(array.slice(index, size + index))
        index += size
    }
    return chunked_array
}

interface FlatPosterior {
    [key: string]: number[][]
}
interface Posterior {
    [key: string]: Object
}

function flatten_posterior(posterior: Posterior): FlatPosterior {
    const posterior_paths = flatten_posterior_dimensions(posterior)
    const flat_posterior = new Object() as FlatPosterior
    for (const posterior_path of posterior_paths) {
        const posterior_path_tokens = posterior_path.split(".")
        const chain_data: number[][] = get_from_nested_object(posterior, posterior_path_tokens)
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
            const dimension_value = group.join("=")
            dimension_value_names.push(dimension_value)
        }
        const all_dimensions_and_values = dimension_value_names.join(",")
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

function compute_forest_data(
    flat_posterior: FlatPosterior,
    combine_chains: boolean = false,
    hdi_probability: number = 0.89,
) {
    let hdi = new Object()
    for (const key in flat_posterior) {
        const chain_data = flat_posterior[key]
        if (combine_chains) {
            const all_chain_data = new Array()
            for (const chain_datum of chain_data) {
                all_chain_data.push(...chain_datum)
            }
            const datum = hdiInterval(all_chain_data, hdi_probability)
            hdi[key] = [
                {
                    hdi_lower: datum.lowerBound,
                    mean: mean(all_chain_data),
                    hdi_upper: datum.upperBound,
                },
            ]
        } else {
            const hdi_datum = new Array()
            for (const chain_datum of chain_data) {
                const datum = hdiInterval(chain_datum, hdi_probability)
                hdi_datum.push({
                    hdi_lower: datum.lowerBound,
                    mean: mean(chain_datum),
                    hdi_upper: datum.upperBound,
                })
            }
            hdi[key] = hdi_datum
        }
    }
    return hdi
}

export default {render}
