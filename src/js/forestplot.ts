import * as Plot from "@observablehq/plot";

function render({ model, el }) {
  const posterior = model.get("posterior");
  const posterior_hierarchy = determine_posterior_hierarchy(posterior);
  const posterior_data = parse_posterior_data(posterior);
  window.posterior_data = posterior_data;

  // Create a `div` for the selects.
  const select_div = document.createElement("div");
  select_div.style.width = "1000px";
  select_div.style.height = "25px";

  // Create selects for both the `data_vars` and any `coords` associated with a
  // `data_var`.
  const data_variables_select = document.createElement("select");
  data_variables_select.name = "data variables";
  data_variables_select.id = "data-variables-select";
  const data_dimensions_select = document.createElement("select");
  data_dimensions_select.name = "data dimensions";
  data_dimensions_select.id = "data-dimensions-select";

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
  // let selected_data_variable = data_variables_select.value;
  // let selected_coordinates_variable = data_coordinates_select.value;

  let x = posterior["coords"]["draw"]["data"];
  let y = posterior_data[data_variables_select.value][data_dimensions_select.value]["chains"]["chain0"];
  let plot_data = new Array();
  for (let i = 0; i < x.length; i++) {
    plot_data.push({ "x": x[i], "y": y[i] })
  }
  const plot_div = document.createElement("div");
  plot_div.style.width = "1000px";
  plot_div.style.height = "600px";
  let plot = Plot.plot({
    grid: true,
    inset: 10,
    color: { legend: true },
    marks: [
      Plot.frame(),
      Plot.line(
        plot_data,
        {
          x: "x",
          y: "y",
        }
      )
    ]
  });
  plot_div.appendChild(plot);

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

  const data = {};
  const num_chains = posterior["coords"]["chain"]["data"].length;
  const num_draws = posterior["coords"]["draw"]["data"].length;
  // Create the data structure to hold hierarchical variables.
  for (let data_variable_name in posterior_hierarchy) {
    const data_variable_object = posterior["data_vars"][data_variable_name]
    const chain_data = data_variable_object["data"]
    data[data_variable_name] = {}
    for (let i = 0; i < num_chains; i++) {
      const chain_draws = chain_data[i];

      // Check if we have a hierarchy within the draws.
      const is_hierarchical = typeof (chain_draws[0][0]) === "number"

      // Handle non-hierarchical data variables.
      if (!is_hierarchical) {
        if (i === 0) {
          data[data_variable_name]["chains"] = {}
          data[data_variable_name]["chains"][`chain${i}`] = new Array();
        } else {
          data[data_variable_name]["chains"][`chain${i}`] = new Array();
        }
      }

      // Handle hierarchical data variables.
      const data_dimension_names = posterior_hierarchy[data_variable_name]["dimension_values"];
      if (is_hierarchical) {
        for (let j = 0; j < data_dimension_names.length; j++) {
          const data_dimension_name = data_dimension_names[j];
          if (i === 0) {
            data[data_variable_name][data_dimension_name] = {};
            data[data_variable_name][data_dimension_name]["chains"] = {};
            data[data_variable_name][data_dimension_name]["chains"][`chain${i}`] = new Array();
          } else {
            data[data_variable_name][data_dimension_name]["chains"][`chain${i}`] = new Array();
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
        data[data_variable_name]["chains"][`chain${i}`] = chain_draws;
        continue;
      }

      // Handle hierarchical data variables.
      const data_dimension_names = posterior_hierarchy[data_variable_name]["dimension_values"];
      if (is_hierarchical) {
        for (let j = 0; j < num_draws; j++) {
          for (let k = 0; k < data_dimension_names.length; k++) {
            const data_dimension_name = data_dimension_names[k];
            const data_dimension_value = chain_draws[j][k];
            data[data_variable_name][data_dimension_name]["chains"][`chain${i}`].push(data_dimension_value);
          }
        }
      }
    }
  }
  return data;
}

export default { render };
