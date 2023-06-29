from __future__ import annotations

import arviz as az
import param


def create_selectors(idata: az.InferenceData) -> dict[str, param.Parameter]:
    """Create `param.Selector` objects for the dashboard.

    We do not know a priori the random variables used for any given model. We also do
    not know any hierarchy for the given model represented by the ArviZ `InferenceData`
    object. This method iterates through the `idata` object to find all the random
    variables used in the model, and any hierarchy if it exists.

    Parameters
    ----------
    idata : az.InferenceData
        An ArviZ `InferenceData` object that contains the posterior for the model.

    Returns
    -------
    output : dict[str, param.Parameter]
        A dictionary of random variable names as keys and `param` objects as values.

    Raises
    ------
    AttributeError
        If no "posterior" is found in the ArviZ `InferenceData` object, then a model has
        more than likely not been run.
    """
    if not hasattr(idata, "posterior"):
        raise AttributeError(
            "The given ArviZ InferenceData object does not contain a posterior. "
            "Have you run a model?"
        )
    output = {}
    output["rv_selector"] = param.Selector(
        label="Random variable",
        objects=list(idata["posterior"].data_vars.keys()),
    )
    dimensions = list(idata["posterior"].coords)
    for dimension in dimensions:
        if dimension == "draw":
            continue
        objects = idata["posterior"].coords[dimension].data.tolist()
        if dimension == "chain":
            output[f"{dimension}_selector"] = param.ListSelector(
                objects=objects,
                default=[0],
            )
        else:
            output[f"{dimension}_selector"] = param.Selector(objects=objects)
    return output
