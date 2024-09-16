import * as Plot from "@observablehq/plot";

function render({ model, el }) {
  const posterior = model.get("posterior");
  const num_chains = posterior["coords"]["chain"]["data"].length
  const posterior_hierarchy = determine_posterior_hierarchy(posterior);
  const posterior_data = parse_posterior_data(posterior);
  window.posterior_data = posterior_data;

  // Create a `div` for the selects.
  const select_div = document.createElement("div");
  select_div.style.width = "1000px";
  select_div.style.height = "50px";

  // Create selects for both the `data_vars` and any `coords` associated with a
  // `data_var`.
  const data_variables_select = document.createElement("select");
  data_variables_select.name = "data variables";
  data_variables_select.id = "data-variables-select";
  data_variables_select.addEventListener("change", update_plot);

  const data_dimensions_select = document.createElement("select");
  data_dimensions_select.name = "data dimensions";
  data_dimensions_select.id = "data-dimensions-select";
  data_dimensions_select.addEventListener("change", update_plot);

  // Create a div for the chains.
  const chains_div = document.createElement("div");
  chains_div.style.width = "1000px";
  chains_div.style.height = "25px";
  chains_div.style.display = "flex"
  chains_div.style.flexDirection = "row";
  chains_div.style.alignItems = "center";
  for (let chain_num of [...Array(num_chains).keys()]) {
    const chain_checkbox = document.createElement("input");
    chain_checkbox.type = "checkbox";
    chain_checkbox.name = "input";
    chain_checkbox.id = `chain-${chain_num}`;
    chain_checkbox.checked = true;
    chain_checkbox.addEventListener("change", update_plot)
    const chain_label = document.createElement("label");
    chain_label.htmlFor = `chain-${chain_num}`;
    chain_label.innerHTML = `Chain: ${chain_num}`;
    chains_div.appendChild(chain_checkbox);
    chains_div.appendChild(chain_label);
  }

  // Populate the `data_variables_select` menu with options.
  for (let data_variable_name in posterior_hierarchy) {
    data_variables_select.add(new Option(data_variable_name));
  }

  // Update the `data_dimensions_select` menu based on the selected data variable.
  data_variables_select.addEventListener("change", change_coordinate_select_options);
  function change_coordinate_select_options() {
    const selected_data_variable = data_variables_select.value;
    const data_dimensions = posterior_hierarchy[selected_data_variable];

    // Reset the `data_dimensions_select` menu.
    data_dimensions_select.options.length = 0;

    // If there are no extra dimensions associated with the selected data variable, then
    // disable the dimension menu.
    if (data_dimensions["dimension_values"].length == 0) {
      data_dimensions_select.disabled = true;
    } else if (data_dimensions["dimension_values"].length != 0) {
      data_dimensions_select.disabled = false;
    }

    // Populate the `data_dimensions_select` menu with the extra dimensions associated
    // with the selected data variable.
    for (let data_dimension_name of data_dimensions["dimension_values"]) {
      data_dimensions_select.add(new Option(data_dimension_name));
    }
  }
  change_coordinate_select_options();

  select_div.appendChild(data_variables_select);
  select_div.appendChild(data_dimensions_select);
  select_div.append(chains_div);

  const plot_div = document.createElement("div");
  plot_div.style.width = "1000px";
  plot_div.style.height = "600px";

  function update_plot() {
    let selected_data_variable = data_variables_select.value;
    let selected_dimension_variable = data_dimensions_select.value;
    let y_name = `${selected_data_variable} [${selected_dimension_variable}]`
    let chain_lines = new Array();
    let x = posterior["coords"]["draw"]["data"];
    let opacity = 0.5;
    let tip = true;
    for (let chain_num = 0; chain_num < num_chains; chain_num++) {
      let checkbox = document.getElementById(`chain-${chain_num}`)
      if (checkbox != null) {
        opacity = (checkbox as HTMLInputElement).checked ? 0.5 : 0.1;
        tip = opacity === 0.5 ? true : false;
      }
      else { opacity = 0.5; }
      let y = posterior_data[selected_data_variable][selected_dimension_variable]["chains"][`chain${chain_num} `];
      let plot_data = new Array();
      for (let i = 0; i < x.length; i++) {
        let datum = { "Draw": x[i], "chain": `Chain: ${chain_num} ` }
        datum[y_name] = y[i]
        plot_data.push(datum)
      }
      chain_lines.push(Plot.line(plot_data, { x: "Draw", y: y_name, stroke: "chain", tip: tip, strokeOpacity: opacity }))
    }

    // Create the plot.
    let plot = Plot.plot({
      grid: true,
      inset: 10,
      marks: [Plot.frame(), chain_lines],
    });
    if (plot_div.lastChild != null) {
      plot_div.lastChild.remove();
    }
    plot_div.appendChild(plot)
  }
  update_plot();

  const div = document.createElement("div");
  div.appendChild(select_div);
  div.appendChild(plot_div);

  el.appendChild(div);
}

function determine_posterior_hierarchy(posterior) {
  const posterior_hierarchy_array = new Array();

  const data_variables_object = posterior["data_vars"];
  for (let data_variable_name in data_variables_object) {
    const data_dimensions_array = posterior["data_vars"][data_variable_name]["dims"];
    // Ignore any data variables with only `chain` and `draw` dimensions.
    if (data_dimensions_array.length === 2) {
      posterior_hierarchy_array.push([data_variable_name, { "dimension_name": "", "dimension_values": [] }]);
      continue;
    }
    for (let data_dimension_name of data_dimensions_array) {
      // Ignore any data variables with only `chain` and `draw` dimensions.
      if (data_dimension_name == "chain" || data_dimension_name == "draw") {
        continue;
      }
      const dimension_values_array = posterior["coords"][data_dimension_name]["data"];
      posterior_hierarchy_array.push(
        [data_variable_name, { "dimension_name": data_dimension_name, "dimension_values": dimension_values_array }]
      );
    }
  }
  const posterior_hierarchy_object = Object.fromEntries(posterior_hierarchy_array);
  return posterior_hierarchy_object;
}

function parse_posterior_data(posterior) {
  const posterior_hierarchy = determine_posterior_hierarchy(posterior);

  const data = new Map();
  const num_chains = posterior["coords"]["chain"]["data"].length;
  const num_draws = posterior["coords"]["draw"]["data"].length;
  // Create the data structure to hold hierarchical variables.
  for (let data_variable_name in posterior_hierarchy) {
    const data_variable_object = posterior["data_vars"][data_variable_name]
    const chain_data = data_variable_object["data"]
    data[data_variable_name] = new Map()
    for (let i = 0; i < num_chains; i++) {
      const chain_draws = chain_data[i];

      // Check if we have a hierarchy within the draws.
      const is_hierarchical = typeof (chain_draws[0][0]) === "number"

      // Handle non-hierarchical data variables.
      if (!is_hierarchical) {
        if (i === 0) {
          data[data_variable_name]["chains"] = new Map();
          data[data_variable_name]["chains"][`chain${i} `] = new Array();
        } else {
          data[data_variable_name]["chains"][`chain${i} `] = new Array();
        }
      }

      // Handle hierarchical data variables.
      const data_dimension_names = posterior_hierarchy[data_variable_name]["dimension_values"];
      if (is_hierarchical) {
        for (let j = 0; j < data_dimension_names.length; j++) {
          const data_dimension_name = data_dimension_names[j];
          if (i === 0) {
            data[data_variable_name][data_dimension_name] = new Map();
            data[data_variable_name][data_dimension_name]["chains"] = new Map();
            data[data_variable_name][data_dimension_name]["chains"][`chain${i} `] = new Array();
          } else {
            data[data_variable_name][data_dimension_name]["chains"][`chain${i} `] = new Array();
          }
        }
      }
    }
  }

  // Populate the data structure.
  for (let data_variable_name in posterior_hierarchy) {
    const data_variable_object = posterior["data_vars"][data_variable_name]
    const chain_data = data_variable_object["data"]
    for (let i = 0; i < num_chains; i++) {
      const chain_draws = chain_data[i];

      // Check if we have a hierarchy within the draws.
      const is_hierarchical = typeof (chain_draws[0][0]) === "number"

      // Handle non-hierarchical data variables.
      if (!is_hierarchical) {
        data[data_variable_name]["chains"][`chain${i} `] = chain_draws;
        continue;
      }

      // Handle hierarchical data variables.
      const data_dimension_names = posterior_hierarchy[data_variable_name]["dimension_values"];
      if (is_hierarchical) {
        for (let j = 0; j < num_draws; j++) {
          for (let k = 0; k < data_dimension_names.length; k++) {
            const data_dimension_name = data_dimension_names[k];
            const data_dimension_value = chain_draws[j][k];
            data[data_variable_name][data_dimension_name]["chains"][`chain${i} `].push(data_dimension_value);
          }
        }
      }
    }
  }
  return data;
}

function compute_forestplot_data(posterior_data, posterior_hierarchy) {
  let data = new Array();
  for (let data_variable in posterior_data) {
    const data_dimensions = posterior_hierarchy[data_variable]

    // Handle data variables that DO NOT have extra dimensions.
    if (data_dimensions.length === 0) {
      const chain_data_array = posterior_data[data_variable]["chains"]
      let all_chain_data: number[] = new Array();
      for (let chain_data of chain_data_array) {
        all_chain_data.push(...chain_data);
      }
      const mean = all_chain_data.reduce((previous, current) => previous + current, 0) / all_chain_data.length;
      let datum = {
        "name": data_variable,
        "min": Math.min(...all_chain_data),
        "mean": mean,
        "max": Math.max(...all_chain_data),
      }
      data.push(datum);
    }

    // Handle data variables that HAVE extra dimensions.
    if (data_dimensions.length != 0) {
      for (let data_dimension of data_dimensions) {
        const chain_data_array = posterior_data[data_variable][data_dimension]["chains"]
        let all_chain_data: number[] = new Array();
        for (let chain_data of chain_data_array) {
          all_chain_data.push(...chain_data);
        }
        const mean = all_chain_data.reduce((previous, current) => previous + current, 0) / all_chain_data.length;
        let datum = {
          "name": `${data_variable} [${data_dimension}]`,
          "min": Math.min(...all_chain_data),
          "mean": mean,
          "max": Math.max(...all_chain_data),
        }
        data.push(datum);
      }
    }
  }
  return data;
}

export default { render };
