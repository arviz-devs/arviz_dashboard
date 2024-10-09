from pathlib import Path
from typing import TypedDict

import anywidget
import traitlets


class PosteriorData(TypedDict):
    hierarchy: dict
    posterior: dict


class Forestplot(anywidget.AnyWidget):
    _esm = Path(__file__).parent.resolve() / "static" / "forestplot.js"
    posterior = traitlets.Dict().tag(sync=True)
    hierarchy = traitlets.Dict().tag(sync=True)
    num_chains = traitlets.Integer().tag(sync=True)

    def __init__(self, idata) -> None:
        data = self.parse_posterior_data(idata=idata)
        self.num_chains = len(idata["posterior"].coords["chain"])
        super().__init__(posterior=data["posterior"], hierarchy=data["hierarchy"])

    def parse_posterior_data(self, idata) -> PosteriorData:
        posterior = idata["posterior"]
        data_variables = posterior.data_vars

        data = {}
        hierarchy = {}
        for data_variable in data_variables:
            hierarchy[data_variable] = {}
            data[data_variable] = {"chains": [], "coordinates": {}}

            # Determine if there are any coordinates associated with the given `data_variable`.
            # These are hierarchical values associated with the `data_variable`.
            coordinates: set[str] = set(posterior[data_variable].coords)
            # Remove the `chain` and `draw` coordinate from the set of coordinate variables for the
            # given `data_variable`. We do not need them for finding coordinate names.
            coordinates -= {"chain", "draw"}

            # If no coordinates were found for the given `data_variable`, then we can extract the
            # chain data and add it to the data.
            if not coordinates:
                chain_data = posterior[data_variable].data.tolist()
                data[data_variable]["chains"] = chain_data

            # If we have coordinates associated with the `data_variable`, then we need to work
            # harder to extract them so we retain their hierarchy.
            if coordinates:
                # This will give us a "long-format" dataframe.
                coordinates_df = posterior[data_variable].to_dataframe().reset_index()
                # What we need is a "wide-format" dataframe using a pivot.
                ignore_columns = coordinates ^ {"chain", "draw"}
                values = [
                    column for column in coordinates_df.columns if column not in ignore_columns
                ]
                coordinates_chains_df = (
                    coordinates_df.pivot_table(
                        index=coordinates ^ {"chain"},
                        columns="draw",
                        values=values,
                    )
                    .droplevel(level=0, axis="columns")
                    .reset_index()
                )
                for coordinate in coordinates:
                    if coordinate not in hierarchy[data_variable]:
                        hierarchy[data_variable] = []
                    if coordinate not in data[data_variable]["coordinates"]:
                        data[data_variable]["coordinates"][coordinate] = {}
                    dimensions = coordinates_chains_df[coordinate].unique()
                    hierarchy[data_variable] = dimensions.tolist()
                    for dimension in dimensions:
                        if dimension not in data[data_variable]["coordinates"][coordinate]:
                            data[data_variable]["coordinates"][coordinate][dimension] = {
                                "chains": []
                            }
                        chain_data = (
                            coordinates_chains_df[coordinates_chains_df[coordinate] == dimension]
                            .drop(columns=[coordinate, "chain"])
                            .values.tolist()
                        )
                        data[data_variable]["coordinates"][coordinate][dimension][
                            "chains"
                        ] = chain_data
        return {"hierarchy": hierarchy, "posterior": data}
