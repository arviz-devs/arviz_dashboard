import * as Plot from "@observablehq/plot";
import { linearRange } from "arvizjs/src/lib/stats/array";

function render({ model, el }) {
  const posterior = model.get("posterior");
  const num_chains = model.get("num_chains");
  const num_draws = model.get("num_draws");
  const hierarchy = model.get("hierarchy");
  window.posterior = posterior;
  window.hierarchy = hierarchy;

  // Create a div for all the posterior inputs.
  const posterior_input_div = document.createElement("div");
  posterior_input_div.style.width = "1000px";
  posterior_input_div.style.height = "100px";
  posterior_input_div.style.display = "flex";
  posterior_input_div.style.flexDirection = "row";
  posterior_input_div.style.gap = "10px";

  const data_variable_div = document.createElement("div");
  data_variable_div.id = "data-variable-div";
  data_variable_div.addEventListener("change", add_dimensions);
  const data_variable_title = document.createElement("p");
  data_variable_title.innerHTML = "<b>Data variable</b>";
  data_variable_div.appendChild(data_variable_title);
  const data_variable_select = document.createElement("select");
  data_variable_select.name = "data variables";
  data_variable_select.id = "data-variables-select";
  data_variable_select.addEventListener("change", update_plot);
  for (let data_variable in hierarchy) {
    data_variable_select.add(new Option(data_variable));
  }
  data_variable_div.appendChild(data_variable_select);
  posterior_input_div.appendChild(data_variable_div);

  // Create a div for the chains.
  const chains_div = document.createElement("div");
  chains_div.style.width = "1000px";
  chains_div.style.height = "25px";
  chains_div.style.display = "flex";
  chains_div.style.flexDirection = "row";
  chains_div.style.alignItems = "center";
  for (let chain_num of [...Array(num_chains).keys()]) {
    const chain_checkbox = document.createElement("input");
    chain_checkbox.type = "checkbox";
    chain_checkbox.name = "input";
    chain_checkbox.id = `chain-${chain_num}`;
    chain_checkbox.checked = true;
    chain_checkbox.addEventListener("change", update_plot);
    const chain_label = document.createElement("label");
    chain_label.htmlFor = `chain-${chain_num}`;
    chain_label.innerHTML = `Chain: ${chain_num}`;
    chains_div.appendChild(chain_checkbox);
    chains_div.appendChild(chain_label);
  }

  const plot_div = document.createElement("div");
  plot_div.style.width = "1000px";
  plot_div.style.height = "600px";

  // Create a div for all elements of the widget.
  const div = document.createElement("div");
  div.id = "forestplot-div";
  div.appendChild(posterior_input_div);
  div.appendChild(chains_div);
  div.appendChild(plot_div);

  // Append the widget div to the notebook element.
  el.appendChild(div);

  // Callbacks
  function add_dimensions() {
    let extra_dimensions_div = document.getElementById(
      "extra-dimensions-div",
    ) as HTMLDivElement;
    if (extra_dimensions_div === null) {
      extra_dimensions_div = document.createElement("div");
      extra_dimensions_div.id = "extra-dimensions-div";
    } else if (extra_dimensions_div !== null) {
      extra_dimensions_div.innerHTML = "";
    }
    const extra_dimensions_title = document.createElement("p");
    extra_dimensions_title.id = "extra-dimensions-title";
    const data_variable = document.getElementById(
      "data-variables-select",
    ) as HTMLSelectElement;
    if (data_variable !== null) {
      const data_variable_name = data_variable.value;
      const coordinates = hierarchy[data_variable_name];
      for (let coordinate in coordinates) {
        extra_dimensions_title.innerHTML = `<b>${coordinate}</b>`;
        const extra_dimensions_select = document.createElement("select");
        extra_dimensions_select.addEventListener("change", update_plot);
        extra_dimensions_select.id = `coordinate-${coordinate}`;
        const dimensions = hierarchy[data_variable_name][coordinate];
        if (Object.keys(dimensions).length !== 0) {
          for (let dimension of dimensions) {
            extra_dimensions_select.add(new Option(dimension));
          }
        }
        extra_dimensions_div.appendChild(extra_dimensions_title);
        extra_dimensions_div.appendChild(extra_dimensions_select);
      }
    }
    posterior_input_div.appendChild(extra_dimensions_div);
    update_plot();
  }
  add_dimensions();

  function update_plot() {
    const data_variable_select = document.getElementById(
      "data-variables-select",
    ) as HTMLSelectElement;

    let extra_dimension_names = new Array();
    const extra_dimensions = document.querySelectorAll('[id^="coordinate-"]');
    for (let i = 0; i < extra_dimensions.length; i++) {
      const extra_dimension = extra_dimensions[i] as HTMLSelectElement;
      extra_dimension_names.push(extra_dimension.value);
    }

    const coordinate = document.getElementById("extra-dimensions-title");
    const coordinate_name = coordinate?.textContent;

    let data_variable_name = "";
    if (data_variable_select !== null) {
      data_variable_name = data_variable_select.value;
    }

    let x = linearRange(0, num_draws, 1, false);
    let y_name = `${data_variable_name}`;
    let chain_lines = new Array();
    let opacity = 0.5;
    let tip = true;
    for (let chain_num = 0; chain_num < num_chains; chain_num++) {
      let checkbox = document.getElementById(`chain-${chain_num}`);
      if (checkbox !== null) {
        opacity = (checkbox as HTMLInputElement).checked ? 0.5 : 0.1;
        tip = opacity === 0.5 ? true : false;
      } else {
        opacity = 0.5;
      }
      let y = new Array();
      if (extra_dimensions.length !== 0) {
        y = getNestedObject(
          posterior[data_variable_name]["coordinates"][coordinate_name],
          extra_dimension_names.concat(["chains", chain_num]),
        );
      } else {
        y = posterior[data_variable_name]["chains"][chain_num];
      }
      let plot_data = new Array();
      for (let i = 0; i < x.length; i++) {
        let datum = { Draw: x[i], chain: `Chain: ${chain_num} ` };
        datum[y_name] = y[i];
        plot_data.push(datum);
      }
      chain_lines.push(
        Plot.line(plot_data, {
          x: "Draw",
          y: y_name,
          stroke: "chain",
          tip: tip,
          strokeOpacity: opacity,
        }),
      );
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
    plot_div.appendChild(plot);
  }
  update_plot();
}

const getNestedObject = (nestedObj, pathArr) => {
  return pathArr.reduce(
    (obj, key) => (obj && obj[key] !== "undefined" ? obj[key] : undefined),
    nestedObj,
  );
};

export default { render };
