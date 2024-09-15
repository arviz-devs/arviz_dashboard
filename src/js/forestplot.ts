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


  // Add data to the plot.
  let chain_lines = new Array();
  let x = posterior["coords"]["draw"]["data"];
  for (let chain_num = 0; chain_num < num_chains; chain_num++) {
    let y = posterior_data[data_variables_select.value][data_dimensions_select.value]["chains"][`chain${chain_num}`];
    let plot_data = new Array();
    for (let i = 0; i < x.length; i++) {
      plot_data.push({ "x": x[i], "y": y[i] })
    }
    chain_lines.push(Plot.line(plot_data, { x: "x", y: "y" }))
  }

  // Create the plot.
  let plot = Plot.plot({
    grid: true,
    inset: 10,
    color: { range: ["steelblue", "orange", "brown", "grey"], legend: true, },
    marks: [
      Plot.frame(),
      ...chain_lines,
    ]
  });


  const plot_div = document.createElement("div");
  plot_div.style.width = "1000px";
  plot_div.style.height = "600px";
  plot_div.appendChild(plot);

  data_variables_select.addEventListener("change", update_plot);
  data_dimensions_select.addEventListener("change", update_plot);
  function update_plot() {
    let selected_data_variable = data_variables_select.value;
    let selected_dimension_variable = data_dimensions_select.value;
    // let x = posterior["coords"]["draw"]["data"];
    // let y = posterior_data[selected_data_variable][selected_dimension_variable]["chains"]["chain0"];
    // let plot_data = new Array();
    // for (let i = 0; i < x.length; i++) {
    //   plot_data.push({ "x": x[i], "y": y[i] })
    // }
    // let new_plot = Plot.plot({
    //   grid: true,
    //   inset: 10,
    //   color: { legend: true },
    //   marks: [
    //     Plot.frame(),
    //     Plot.line(
    //       plot_data,
    //       {
    //         x: "x",
    //         y: "y",
    //       }
    //     )
    //   ]
    // });
    let chain_lines = new Array();
    let x = posterior["coords"]["draw"]["data"];
    for (let chain_num = 0; chain_num < num_chains; chain_num++) {
      let y = posterior_data[data_variables_select.value][data_dimensions_select.value]["chains"][`chain${chain_num}`];
      let plot_data = new Array();
      for (let i = 0; i < x.length; i++) {
        plot_data.push({ "Draw": x[i], "y": y[i], "chain": `Chain: ${chain_num}` })
      }
      chain_lines.push(Plot.line(plot_data, { x: "Draw", y: "y", stroke: "chain", tip: true, strokeOpacity: 0.7 }))
    }

    // Create the plot.
    let new_plot = Plot.plot({
      grid: true,
      inset: 10,
      color: { range: ["steelblue", "orange", "brown", "grey"], legend: true, },
      marks: [
        Plot.frame(),
        chain_lines,
      ],
    });
    if (plot_div.lastChild != null) {
      plot_div.lastChild.remove();
    }
    plot_div.appendChild(new_plot)
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
            data[data_variable_name][data_dimension_name] = new Map();
            data[data_variable_name][data_dimension_name]["chains"] = new Map();
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
          "name": `${data_variable}[${data_dimension}]`,
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
