import geopandas as gpd
import pandas as pd
from GeoDataFrameAux import extract_coord_at_index
from RoadGraph import euclidean_distance
from RoadGraph.StdColNames import *
from RoadGraph.StdKeyWords import *


class StdNodesEdgesGdfConnector:

    def __init__(self, threshold=0):
        self.THRESHOLD = threshold

    def connect_two_nodeEdges_std_gdfs_from_paths(self, first_path: str, second_path: str, out_path: str = None) \
            -> (gpd.GeoDataFrame, gpd.GeoDataFrame):
        """
        Decorator function that that executes connection between edges and nodes from file path inputs
        :param first_path: File path containing the nodes and edges dataframe of the first road network
        :param second_path: File path containing the nodes and edges dataframe of the second road network
        :param out_path: (Optional) File path to write out the compiled nodes and edges dataframe
        :return: Merged/connected nodes and edges dataframe based on dataframes from first path and second path
        """
        edges_a = gpd.read_file(first_path + "/edges.shp")
        nodes_a = gpd.read_file(first_path + "/nodes.shp")
        edges_b = gpd.read_file(second_path + "/edges.shp")
        nodes_b = gpd.read_file(second_path + "/nodes.shp")

        return self.connect_two_nodeEdges_std_gdfs(edges_a, nodes_a, edges_b, nodes_b, out_path)

    def connect_two_nodeEdges_std_gdfs(self, edges_a: gpd.GeoDataFrame, nodes_a: gpd.GeoDataFrame,
                                       edges_b: gpd.GeoDataFrame, nodes_b: gpd.GeoDataFrame,
                                       out_path: str = None) -> (gpd.GeoDataFrame, gpd.GeoDataFrame):
        """
        Connects two nodes and edges dataframes into a single geographical dataframe based on the nodal coordinates
        :param edges_a: Edges geoDataFrame of the first source
        :param nodes_a: Nodes geoDataFrame of the first source
        :param edges_b: Edges geoDataFrame of the second source
        :param nodes_b: Nodes geoDataFrame of the second source
        :param out_path: (Optional) file path to write out the merged/connected new geodataframes of the nodes and
        edges.
        :return: Merged/connected nodes and edges dataframe based on dataframes from first path and second sources
        """
        base_e = edges_a.copy()
        base_n = nodes_a.copy()
        aux_e = edges_b.copy()
        aux_n = nodes_b.copy()

        # Establish connections between all Base roundabout nodes and terminal nodes to other auxiliary nodes
        aux_e, aux_n, base_n = self._connect_by_nodes(base_n, aux_n, aux_e, STD_N_ROUNDABOUT)
        aux_e, aux_n, base_n = self._connect_by_nodes(base_n, aux_n, aux_e, STD_N_TERMINAL)

        # Establish connections between all auxiliary roundabout nodes and dead-end nodes to other base nodes
        base_e, base_n, aux_n = self._connect_by_nodes(aux_n, base_n, base_e, STD_N_ROUNDABOUT)
        base_e, base_n, aux_n = self._connect_by_nodes(aux_n, base_n, base_e, STD_N_TERMINAL)

        # Establish connections between terminal nodes and potential edges from other map
        aux_e = self._connect_by_edge(base_n, aux_e)
        base_e = self._connect_by_edge(aux_n, base_e)

        aux_e = self._reindex_to_base_edges(base_e, aux_e)
        base_e = pd.concat([base_e, aux_e])
        base_n = pd.concat([base_n, aux_n])

        if out_path is not None:
            base_e.to_file(out_path + "/edges.shp")
            base_n.to_file(out_path + "/nodes.shp")

        return base_e, base_n

    def _connect_by_nodes(self, base_n: gpd.GeoDataFrame, aux_n: gpd.GeoDataFrame, aux_e: gpd.GeoDataFrame,
                          node_type: str) -> (gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame):
        """
        Establishes connections between all nodes of a particular 'node_type' in the base dataframe to other
        terminal node in the aux dataframe.
        :param base_n: Dataframe of nodes in which nodes of node_type will be extracted and used to establish
        connections with other nodes in aux dataframe
        :param aux_n: Dataframe of nodes used to identify any that are close enough to the node of node_type
        from base_n
        :param aux_e: Corresponding dataframe of edges connected to aux_n
        :param node_type: The type of node to be iterated through in base_n
        :return: Updated aux_e, aux_n, and base_n tuple.
        """
        IS_CONNECTED = "is_connected"
        N_COORD = "coord"
        base_n[N_COORD] = base_n[STD_GEOMETRY].apply(lambda x: extract_coord_at_index(x, 0))
        aux_n[N_COORD] = aux_n[STD_GEOMETRY].apply(lambda x: extract_coord_at_index(x, 0))
        sel_nodes = base_n.loc[base_n[STD_N_TYPE] == node_type]
        for index, node in sel_nodes.iterrows():
            sel_coord = node[N_COORD]
            sel_buffer = node[STD_N_ROUNDABOUT_EXTENT]

            aux_n[IS_CONNECTED] = aux_n[N_COORD].apply(lambda x: self._is_connected(sel_coord, x, sel_buffer))

            nodes_replacing = aux_n.loc[aux_n[IS_CONNECTED] == True, STD_NODE_ID]

            if len(nodes_replacing) > 0 and node.Type == STD_N_TERMINAL:
                base_n.at[index, STD_N_TYPE] = STD_N_JUNCTION

            aux_e.loc[aux_e[STD_FROM_NODE].isin(nodes_replacing), STD_FROM_NODE] = node.node_id
            aux_e.loc[aux_e[STD_TO_NODE].isin(nodes_replacing), STD_TO_NODE] = node.node_id

            aux_n.drop(index=aux_n.index[aux_n[STD_NODE_ID].isin(nodes_replacing)], inplace=True)

            aux_n.drop(IS_CONNECTED, axis=1, inplace=True)

        aux_n.drop(N_COORD, axis=1, inplace=True)
        base_n.drop(N_COORD, axis=1, inplace=True)

        return aux_e, aux_n, base_n

    def _connect_by_edge(self, base_n: gpd.GeoDataFrame, aux_e: gpd.GeoDataFrame) -> gpd.GeoDataFrame:

        N_COORD = "coord"
        FIRST_COORD = "FIRST_COORD"
        LAST_COORD = "LAST_COORD"
        # Filter nodes by terminal nodes
        base_n[N_COORD] = base_n[STD_GEOMETRY].apply(lambda x: extract_coord_at_index(x, 0))
        sel_nodes = base_n.loc[base_n[STD_N_TYPE] == STD_N_TERMINAL]

        # Extract first and last coordinates from edges
        aux_e[FIRST_COORD] = aux_e[STD_GEOMETRY].apply(lambda x: extract_coord_at_index(x, 0))
        aux_e[LAST_COORD] = aux_e[STD_GEOMETRY].apply(lambda x: extract_coord_at_index(x, -1))

        for _, node in sel_nodes.iterrows():
            node_id = node[STD_NODE_ID]
            n_coord = node[N_COORD]

            is_connected = aux_e[FIRST_COORD].apply(lambda x: x == n_coord)
            connected_index = aux_e.index[(is_connected == True) & (aux_e[STD_FROM_NODE] == 'None')]
            if len(connected_index) > 0:
                print(node_id)
                base_n.loc[base_n[STD_NODE_ID] == node_id, STD_N_TYPE] = STD_N_JUNCTION
                aux_e.loc[connected_index, STD_FROM_NODE] = node_id
                aux_e.loc[connected_index, STD_PREV_IND] = pd.NA

            is_connected = aux_e[LAST_COORD].apply(lambda x: x == n_coord)
            connected_index = aux_e.index[(is_connected == True) & (aux_e[STD_TO_NODE] == 'None')]
            if len(connected_index) > 0:
                print(node_id)
                base_n.loc[base_n[STD_NODE_ID] == node_id, STD_N_TYPE] = STD_N_JUNCTION
                aux_e.loc[connected_index, STD_TO_NODE] = node_id
                aux_e.loc[connected_index, STD_NEXT_IND] = pd.NA

        base_n.drop([N_COORD], axis=1, inplace=True)
        aux_e.drop([FIRST_COORD, LAST_COORD], axis=1, inplace=True)

        return aux_e

    def _reindex_to_base_edges(self, base_e: gpd.GeoDataFrame, aux_e: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Updates indices of the aux_e dataframe based on the indices of the base_e dataframe.
        :param base_e: dataframe of edges
        :param aux_e: dataframe of edges
        :return: re-indexed aux_e
        """
        offset = len(base_e)
        aux_e = self._reindex(aux_e)
        aux_e[STD_INDEX] += offset
        aux_e[STD_PREV_IND] += offset
        aux_e[STD_NEXT_IND] += offset
        aux_e.index += offset

        return aux_e

    def _reindex(self, aux_e: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Resets indices of the dataframe aux_e, and also updates the prev_ind and next_ind columns
        :param aux_e: Dataframe of edges
        :return: Updated aux_e
        """
        old_ind = aux_e[STD_INDEX].tolist()

        aux_e.reset_index(drop=True, inplace=True)
        aux_e[STD_INDEX] = aux_e.index
        aux_e[STD_PREV_IND] = aux_e.loc[pd.isna(aux_e[STD_PREV_IND]) == False, STD_PREV_IND]. \
            apply(lambda x: old_ind.index(int(x)))
        aux_e[STD_NEXT_IND] = aux_e.loc[pd.isna(aux_e[STD_NEXT_IND]) == False, STD_NEXT_IND]. \
            apply(lambda x: old_ind.index(int(x)))
        return aux_e

    def _is_connected(self, first_coords: tuple, sec_coords: tuple, buffer: float) -> bool:
        """
        Checks if both coordinates are 'connected' based on a pre-defined threshold and an additional buffer
        (if needed)
        :param first_coords: The first coordinate
        :param sec_coords: The second coordinate
        :param buffer: An additional buffer to be added on top of threshold
        :return: Boolean, true if the calculated distance between the two coordinates are less than some threshold,
        false otherwise.
        """
        if pd.isna(buffer):
            buffer = 0.0
        else:
            buffer = float(buffer)

        tolerance = buffer + self.THRESHOLD
        distance = euclidean_distance(first_coords, sec_coords)

        return distance <= tolerance
