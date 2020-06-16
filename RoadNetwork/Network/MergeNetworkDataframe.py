import geopandas as gpd
import pandas as pd
from RoadNetwork.Utilities.ColumnNames import *


# Start with nodes in SRN Network
# Filter by roundabouts first
# Drop all roads in OS that is already included in the SRN database
# For every roundabout
# Filter os data by dead end nodes
# Calculate proximity of dead end nodes to roundabout coordinate
# Where dead end nodes are below some threshold:
# Set all From_Node and To_node in edges database to the roundabout node
# Drop dead end nodes from database
# Filter by dead nodes in SRN Network
# For every dead end node:
# Calculate proximity of nodes with respect to this dead end node
# If below some proximity:
# Set edges databases containing these nodes to the dead end node
# Delete these nodes

# Perform the same operation for the OS Network database
# Once complete, then merge nodes and edges databases into one.

class MergeNetworkDataFrames:

    def __init__(self, threshold=5):
        self.THRESHOLD = 5

    def merge_two_network_dataframes(self, base_edges_df: gpd.GeoDataFrame, base_nodes_df: gpd.GeoDataFrame,
                                     to_merge_edges_df: gpd.GeoDataFrame, to_merge_nodes_df: gpd.GeoDataFrame):

        to_merge_edges_df = self._exclude_roads(base_edges_df, to_merge_edges_df)

        # roundabout_nodes = base_nodes_df.loc[base_nodes_df[N_TYPE] == N_ROUNDABOUT]

        # for _, roundabout_node in roundabout_nodes.iterrows():
        #     to_merge_nodes_df["is_connected"] = to_merge_nodes_df.loc[to_merge_nodes_df[N_TYPE] == N_DEAD_END,GEOMETRY]

        return to_merge_edges_df

    def _exclude_roads(self, base_edges_df, to_merge_edges_df):

        pd.options.mode.chained_assignment = None

        # Exclude roads in the to_merge_edges_df
        roads_to_exclude = base_edges_df[HE_ROAD_NO].unique()
        to_merge_edges_df["is_in_list"] = to_merge_edges_df[HE_ROAD_NO].apply(lambda x: x in roads_to_exclude)
        to_merge_edges_df = to_merge_edges_df.loc[to_merge_edges_df["is_in_list"] == False]
        to_merge_edges_df.drop("is_in_list", axis=1, inplace=True)

        pd.options.mode.chained_assignment = 'warn'

        return to_merge_edges_df

    def _euclidean_distance(self, coord1: tuple, coord2: tuple):
        """
        Calculates the Euclidean distance between two coordinates
        :param coord1: Tuple of numerical digits
        :param coord2: Second tupe of numerical digits
        :return: Returns the Euclidean distance between two coordinates
        """
        x1, y1 = coord1
        x2, y2 = coord2
        return sqrt(pow(x1 - x2, 2) + pow(y1 - y2, 2))

    def _is_connected_to_roundabout(self, roundabout_coords: tuple, road_coords: tuple,
                                    radius: float) -> bool:

        tolerance = radius + self.THRESHOLD
        distance = self._euclidean_distance(roundabout_coords, road_coords)

        return distance <= tolerance
