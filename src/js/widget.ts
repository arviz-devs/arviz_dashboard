function render({ model, el }) {
  let div = document.createElement("div");
  div.style.height = "300px";
  let posterior = model.get("posterior");
  console.log(posterior);
  window.posterior = posterior;
  div.innerHTML = `${Object.keys(posterior["data_vars"]).toString()}`;
  el.appendChild(div);
}
export default { render };
