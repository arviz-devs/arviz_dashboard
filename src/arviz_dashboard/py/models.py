"""Data models.

This module contains the classes that define data models used for the corresponding TypeScript
files, found in `arviz_dashboard/ts`.
"""

import itertools
from typing import TypedDict

from xarray.core.datatree import DataTree


class PosteriorData(TypedDict):
    dropdowns: dict
    posterior: dict
    num_chains: int
    num_draws: int


class PosteriorModel:
    def update(self, original_dictionary: dict, update_with: dict) -> dict:
        for key, value in update_with.items():
            if isinstance(value, dict):
                original_dictionary[key] = self.update(original_dictionary.get(key, {}), value)
            else:
                original_dictionary[key] = value
        return original_dictionary

    def parse_posterior_data(self, idata: DataTree) -> PosteriorData:
        posterior = idata["posterior"]
        data_variables = posterior.data_vars
        num_chains = len(posterior.coords["chain"].data)
        num_draws = len(posterior.coords["draw"].data)

        data = {}
        dropdowns = {}
        for data_variable in data_variables:
            dropdowns[data_variable] = {}
            data[data_variable] = {}

            # Determine if there are any coordinates associated with the given `data_variable`.
            # These are hierarchical values associated with the `data_variable`, and must retain
            # their order.
            coordinates = list(posterior[data_variable].coords)
            # Remove the `chain` and `draw` coordinate from the set of coordinate variables for the
            # given `data_variable`. We do not need them for finding coordinate names.
            coordinates = [coord for coord in coordinates if coord not in {"chain", "draw"}]

            # If no coordinates were found for the given `data_variable`, then we can extract the
            # chain data and add it to the data.
            if not coordinates:
                chain_data = posterior[data_variable].data.tolist()
                data[data_variable]["chain"] = chain_data

            # If we have coordinates associated with the `data_variable`, then we need to work
            # harder to extract them so we retain their hierarchy.
            ignore_columns = [*coordinates, "chain", "draw"]
            if coordinates:
                coordinates_df = posterior[data_variable].to_dataframe().reset_index()

                # Fill in the dropdowns data.
                for coordinate in coordinates:
                    if coordinate not in dropdowns[data_variable]:
                        dropdowns[data_variable][coordinate] = []
                    dimensions = coordinates_df[coordinate].unique()
                    dropdowns[data_variable][coordinate] = dimensions.tolist()

                values = [
                    column for column in coordinates_df.columns if column not in ignore_columns
                ]
                # Using a pivot we can transform the "long-format" dataframe into a
                # "wide-format" for data extraction.
                coordinate_chains_df = (
                    coordinates_df.pivot_table(
                        index=[*coordinates, "chain"],
                        columns="draw",
                        values=values,
                    )
                    .droplevel(level=0, axis="columns")
                    .reset_index()
                )
                # We group by the coordinates in order to extract chain data, and create a nested
                # dictionary that we can add it to.
                grouped = coordinate_chains_df.groupby(coordinates)
                groups = grouped.groups
                coordinate_names_and_values = []
                for group in groups:
                    group_name = group
                    if not isinstance(group_name, tuple):
                        group_name = (group,)
                    group_df = grouped.get_group(group_name)
                    chain_data = group_df.set_index([*coordinates, "chain"]).to_numpy().tolist()
                    grouped_df = group_df.set_index(coordinates)
                    # The `zip` gives us the following structure
                    # [(coordinate_name1, coordinate_value1), (...), ...]. We flatten the list using
                    # itertools to give [coordinate_name1, coordinate_value1, ...].
                    values = grouped_df.index.drop_duplicates().to_list()
                    if isinstance(values[0], tuple):
                        values = values[0]
                    coord_names_and_values = list(
                        itertools.chain.from_iterable(
                            zip(
                                grouped_df.index.names,
                                values,
                            ),
                        ),
                    )
                    # We create a list of nested dictionaries from the grouped dataframe
                    # coordinates.
                    temp_dict = {"chain": chain_data}
                    for coord_name_and_value in list(coord_names_and_values)[::-1]:
                        temp_dict = {coord_name_and_value: temp_dict}
                    coordinate_names_and_values.append(temp_dict)
                # Next we create the highly nested dictionary from the `coordinate_names_and_values`
                # list.
                keys = {}
                for item in coordinate_names_and_values:
                    keys = self.update(keys, item)
                data[data_variable] = keys
        return {
            "dropdowns": dropdowns,
            "posterior": data,
            "num_chains": num_chains,
            "num_draws": num_draws,
        }
