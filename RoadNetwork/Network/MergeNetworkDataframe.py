from math import sqrt

import geopandas as gpd
import pandas as pd
from RoadNetwork.Utilities.ColumnNames import *
from GeoDataFrameAux import *


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

    def __init__(self, threshold=15):
        self.THRESHOLD = threshold

    def merge_two_network_dataframes(self, base_edges_df: gpd.GeoDataFrame, base_nodes_df: gpd.GeoDataFrame,
                                     to_merge_edges_df: gpd.GeoDataFrame, to_merge_nodes_df: gpd.GeoDataFrame):

        base_edges_df = base_edges_df.copy()
        base_nodes_df = base_nodes_df.copy()
        to_merge_edges_df = to_merge_edges_df.copy()
        to_merge_nodes_df = to_merge_nodes_df.copy()

        print('1')
        to_merge_edges_df, to_merge_nodes_df = self._exclude_roads(base_edges_df, to_merge_edges_df, to_merge_nodes_df)
        print('2')

        to_merge_edges_df, to_merge_nodes_df, base_nodes_df = self._connect_by_nodes(base_nodes_df, to_merge_nodes_df,
                                                                                     to_merge_edges_df, N_ROUNDABOUT)
        print('3')

        to_merge_edges_df, to_merge_nodes_df, base_nodes_df = self._connect_by_nodes(base_nodes_df, to_merge_nodes_df,
                                                                                     to_merge_edges_df, N_DEAD_END)
        print('4')
        base_edges_df, base_nodes_df, to_merge_nodes_df = self._connect_by_nodes(to_merge_nodes_df, base_nodes_df,
                                                                                 base_edges_df, N_ROUNDABOUT)
        print('5')
        base_edges_df, base_nodes_df, to_merge_nodes_df = self._connect_by_nodes(to_merge_nodes_df, base_nodes_df,
                                                                                 base_edges_df, N_DEAD_END)
        print('6')
        to_merge_edges_df, to_merge_nodes_df = self._expunge_redundant_edges(to_merge_edges_df,
                                                                             to_merge_nodes_df,
                                                                             base_nodes_df)
        print('7')
        to_merge_edges_df = self._reindex_to_base_edges(base_edges_df, to_merge_edges_df)
        print('8')
        base_edges_df = pd.concat([base_edges_df, to_merge_edges_df])
        base_nodes_df = pd.concat([base_nodes_df, to_merge_nodes_df])
        base_nodes_df = self._remove_redundant_nodes(base_nodes_df, base_edges_df)
        print('9')
        return base_edges_df, base_nodes_df

    def _exclude_roads(self, base_edges_df, to_merge_edges_df, to_merge_nodes_df):
        pd.options.mode.chained_assignment = None
        # Exclude roads in the to_merge_edges_df
        roads_to_exclude = base_edges_df[HE_ROAD_NO].unique()
        to_merge_edges_df["is_in_list"] = to_merge_edges_df[HE_ROAD_NO].apply(lambda x: x in roads_to_exclude)

        redundant_from_nodes = to_merge_edges_df.loc[(to_merge_edges_df["is_in_list"] == True) &
                                                     (to_merge_edges_df[FROM_NODE] != "None"), FROM_NODE]

        redundant_to_nodes = to_merge_edges_df.loc[(to_merge_edges_df["is_in_list"] == True) &
                                                   (to_merge_edges_df[TO_NODE] != "None"), TO_NODE]

        to_merge_nodes_df.drop(index=to_merge_nodes_df.index[(to_merge_nodes_df[N_NODE_ID].isin(redundant_from_nodes)) &
                                                             (to_merge_nodes_df[N_TYPE] == N_DEAD_END)], inplace=True)

        to_merge_nodes_df.drop(index=to_merge_nodes_df.index[(to_merge_nodes_df[N_NODE_ID].isin(redundant_to_nodes)) &
                                                             (to_merge_nodes_df[N_TYPE] == N_DEAD_END)], inplace=True)

        to_merge_edges_df = to_merge_edges_df.loc[to_merge_edges_df["is_in_list"] == False]
        to_merge_edges_df.drop("is_in_list", axis=1, inplace=True)
        pd.options.mode.chained_assignment = 'warn'
        print("Finished excluding roads")
        return to_merge_edges_df, to_merge_nodes_df

    def _reindex(self, to_merge_edges_df):
        old_index = to_merge_edges_df[INDEX].tolist()

        to_merge_edges_df.reset_index(drop=True, inplace=True)
        to_merge_edges_df[INDEX] = to_merge_edges_df.index
        to_merge_edges_df[PREV_IND] = to_merge_edges_df.loc[
            pd.isna(to_merge_edges_df[PREV_IND]) == False, PREV_IND].apply(lambda x: old_index.index(int(x)))
        to_merge_edges_df[NEXT_IND] = to_merge_edges_df.loc[
            pd.isna(to_merge_edges_df[NEXT_IND]) == False, NEXT_IND].apply(lambda x: old_index.index(int(x)))
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

    def _is_connected(self, target_coords: tuple, road_coords: tuple, buffer: float) -> bool:

        if pd.isna(buffer):
            buffer = 0.0
        else:
            buffer = float(buffer)

        tolerance = buffer + self.THRESHOLD
        distance = self._euclidean_distance(target_coords, road_coords)

        return distance <= tolerance

    def _connect_by_nodes(self, base_nodes_df, to_merge_nodes_df, to_merge_edges_df, node_type: str):

        base_nodes_df[N_COORD] = base_nodes_df[GEOMETRY].apply(lambda x: extract_coord_at_index(x, 0))
        to_merge_nodes_df[N_COORD] = to_merge_nodes_df[GEOMETRY].apply(lambda x: extract_coord_at_index(x, 0))
        sel_nodes = base_nodes_df.loc[base_nodes_df[N_TYPE] == node_type]

        for index, node in sel_nodes.iterrows():
            sel_coord = node.Coord
            sel_buffer = node.Extent

            to_merge_nodes_df["is_connected"] = \
                to_merge_nodes_df[N_COORD].apply(lambda x: self._is_connected(sel_coord, x, sel_buffer))

            nodes_replacing = to_merge_nodes_df.loc[to_merge_nodes_df["is_connected"] == True, N_NODE_ID]

            if len(nodes_replacing) > 0 and node.Type == N_DEAD_END:
                base_nodes_df.at[index, N_TYPE] = N_JUNCTION

            to_merge_edges_df.loc[to_merge_edges_df[FROM_NODE].isin(nodes_replacing), FROM_NODE] = node.node_id
            to_merge_edges_df.loc[to_merge_edges_df[TO_NODE].isin(nodes_replacing), TO_NODE] = node.node_id

            to_merge_nodes_df.drop(index=to_merge_nodes_df.index[to_merge_nodes_df[N_NODE_ID].isin(nodes_replacing)],
                                   inplace=True)

            to_merge_nodes_df.drop('is_connected', axis=1, inplace=True)

        to_merge_nodes_df.drop(N_COORD, axis=1, inplace=True)
        base_nodes_df.drop(N_COORD, axis=1, inplace=True)

        return to_merge_edges_df, to_merge_nodes_df, base_nodes_df

    def _reindex_to_base_edges(self, base_edges_df, to_merge_edges_df):

        offset = len(base_edges_df)
        to_merge_edges_df = self._reindex(to_merge_edges_df)
        to_merge_edges_df[INDEX] += offset
        to_merge_edges_df[PREV_IND] += offset
        to_merge_edges_df[NEXT_IND] += offset
        to_merge_edges_df.index += offset

        return to_merge_edges_df

    def _remove_redundant_nodes(self, combined_nodes_gdf, combined_edges_gdf):

        used_nodes_from = list(combined_edges_gdf.loc[pd.isna(combined_edges_gdf[FROM_NODE]) == False,
                                                      FROM_NODE].unique())
        used_nodes_to = list(combined_edges_gdf.loc[pd.isna(combined_edges_gdf[TO_NODE]) == False,
                                                    TO_NODE].unique())

        used_nodes = used_nodes_to
        used_nodes.extend(used_nodes_from)
        used_nodes = list(set(used_nodes))

        combined_nodes_gdf = combined_nodes_gdf.loc[combined_nodes_gdf[N_NODE_ID].isin(used_nodes)]

        return combined_nodes_gdf

    def _expunge_redundant_edges(self, to_merge_edges_gdf, to_merge_nodes_gdf, base_nodes_gdf):

        connected_nodes = base_nodes_gdf[N_NODE_ID].tolist()
        to_merge_edges_gdf['verified'] = 'Unverified'
        indices = to_merge_edges_gdf.INDEX.values.tolist()
        to_merge_edges_gdf['visited'] = False

        for index in indices:
            if to_merge_edges_gdf.loc[index]['verified'] == 'Unverified':
                # print(index)

                self._search_road_network(index, to_merge_edges_gdf, connected_nodes)
                to_merge_edges_gdf['visited'] = False

        # redundant_from_nodes = to_merge_edges_gdf.loc[(to_merge_edges_gdf["verified"] == 'Rejected') &
        #                                              (to_merge_edges_gdf[FROM_NODE] != "None"), FROM_NODE]
        #
        # redundant_to_nodes = to_merge_edges_gdf.loc[(to_merge_edges_gdf["verified"] == 'Rejected') &
        #                                            (to_merge_edges_gdf[TO_NODE] != "None"), TO_NODE]

        # to_merge_nodes_gdf.drop(index=to_merge_nodes_gdf.index[to_merge_nodes_gdf[N_NODE_ID].isin(redundant_from_nodes)],
        #                         inplace=True)
        # to_merge_nodes_gdf.drop(index=to_merge_nodes_gdf.index[to_merge_nodes_gdf[N_NODE_ID].isin(redundant_to_nodes)],
        #                        inplace=True)

        to_merge_edges_gdf.drop(index=to_merge_edges_gdf.index[to_merge_edges_gdf['verified'] == 'Rejected'],
                                inplace=True)

        to_merge_edges_gdf.drop(['verified', 'visited'], axis=1, inplace=True)

        return to_merge_edges_gdf, to_merge_nodes_gdf

    def _search_road_network(self, edge_index, to_merge_edges_gdf, connected_nodes):

        # Mark visited as true the current edge in the to_merge_edges_gdf
        to_merge_edges_gdf.at[to_merge_edges_gdf[INDEX] == edge_index, 'visited'] = True
        edge = to_merge_edges_gdf[to_merge_edges_gdf[INDEX] == edge_index]

        # If NEXT_IND is not null, mark current edge as visited and search_road_network to next edge and return
        if not pd.isna(edge.NEXT_IND).values[0]:

            next_edge_index = to_merge_edges_gdf[to_merge_edges_gdf[INDEX] == int(edge.NEXT_IND.values[0])]
            if not next_edge_index.visited.values[0]:
                if self._search_road_network(int(edge.NEXT_IND.values[0]), to_merge_edges_gdf, connected_nodes):
                    to_merge_edges_gdf.at[to_merge_edges_gdf[INDEX] == edge_index, 'verified'] = "Accepted"
                    return True
            elif next_edge_index.verified.values[0] == "Accepted":
                to_merge_edges_gdf.at[to_merge_edges_gdf[INDEX] == edge_index, 'verified'] = "Accepted"
                return True

        # If PREV_IND is not null, mark current edge as visited and search_road_network to next edge and return
        if not pd.isna(edge.PREV_IND).values[0]:
            prev_edge = to_merge_edges_gdf[to_merge_edges_gdf[INDEX] == int(edge.PREV_IND.values[0])]
            if not prev_edge.visited.values[0]:
                if self._search_road_network(int(edge.PREV_IND.values[0]), to_merge_edges_gdf, connected_nodes):
                    to_merge_edges_gdf.at[to_merge_edges_gdf[INDEX] == edge_index, 'verified'] = "Accepted"
                    return True
                else:
                    if edge_index == 594:
                        print('a')
                    to_merge_edges_gdf.at[to_merge_edges_gdf[INDEX] == edge_index, 'verified'] = "Rejected"
                    return False
                
            elif prev_edge.verified.values[0] == "Accepted":
                to_merge_edges_gdf.at[to_merge_edges_gdf[INDEX] == edge_index, 'verified'] = "Accepted"
                return True

        if edge.TO_NODE.values[0] != "None":
            node_id = edge.TO_NODE.values[0]
            if node_id in connected_nodes:
                to_merge_edges_gdf.at[to_merge_edges_gdf[INDEX] == edge_index, 'verified'] = "Accepted"
                return True
            else:
                connected_edges = to_merge_edges_gdf.loc[(to_merge_edges_gdf['visited'] == False) &
                                                         ((to_merge_edges_gdf[FROM_NODE] == node_id) |
                                                          (to_merge_edges_gdf[TO_NODE] == node_id))]

                connected_edges = connected_edges[connected_edges[INDEX] != edge_index]

                if len(connected_edges) > 0:
                    if len(connected_edges[connected_edges['verified'] == 'Accepted']) > 0:
                        to_merge_edges_gdf.at[to_merge_edges_gdf[INDEX] == edge_index, 'verified'] = "Accepted"
                        return True

                    next_edge_index = connected_edges.iloc[0][INDEX]

                    if self._search_road_network(next_edge_index, to_merge_edges_gdf, connected_nodes):
                        to_merge_edges_gdf.at[to_merge_edges_gdf[INDEX] == edge_index, 'verified'] = "Accepted"
                        return True

        if edge.FROM_NODE.values[0] != "None":
            node_id = edge.FROM_NODE.values[0]
            if node_id in connected_nodes:
                to_merge_edges_gdf.at[to_merge_edges_gdf[INDEX] == edge_index, 'verified'] = "Accepted"
                return True
            else:
                connected_edges = to_merge_edges_gdf.loc[(to_merge_edges_gdf['visited'] == False) &
                                                         ((to_merge_edges_gdf[FROM_NODE] == node_id) |
                                                          (to_merge_edges_gdf[TO_NODE] == node_id))]

                connected_edges = connected_edges[connected_edges[INDEX] != edge_index]

                if len(connected_edges) > 0:
                    if len(connected_edges[connected_edges['verified'] == 'Accepted']) > 0:
                        to_merge_edges_gdf.at[to_merge_edges_gdf[INDEX] == edge_index, 'verified'] = "Accepted"
                        return True

                    next_edge_index = connected_edges.iloc[0][INDEX]

                    if self._search_road_network(next_edge_index, to_merge_edges_gdf, connected_nodes):
                        to_merge_edges_gdf.at[to_merge_edges_gdf[INDEX] == edge_index, 'verified'] = "Accepted"
                        return True

        if edge_index == 594:
            print('b')
        to_merge_edges_gdf.at[to_merge_edges_gdf[INDEX] == edge_index, 'verified'] = "Rejected"
        return False
