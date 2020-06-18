from math import sqrt
from RoadNetwork.Utilities.ColumnNames import *
from GeoDataFrameAux import *


class MergeNetworkDataFrames:

    def __init__(self, threshold=15):
        self.THRESHOLD = threshold

    def merge_two_network_dataframes(self, base_edges_gdf: gpd.GeoDataFrame, base_nodes_gdf: gpd.GeoDataFrame,
                                     aux_edges_gdf: gpd.GeoDataFrame, aux_nodes_gdf: gpd.GeoDataFrame) \
            -> (gpd.GeoDataFrame, gpd.GeoDataFrame):
        """
        Merges all aux-related dataframes into the base dataframe. This ensures all new connections between both
        dataframes are established, and removes edges and nodes that appear to be disconnected.

        :param base_edges_gdf: Geodataframe of all edges in the base network
        :param base_nodes_gdf: Geodataframe of all nodes in the base network
        :param aux_edges_gdf: Geodataframe of all edges in the auxiliary network to be copied into the base
        :param aux_nodes_gdf: Geodataframe of all nodes in the auxiliary network to be copied into the base
        :return: A tuple of two dataframes, both representing the merged edges and nodes of the network.
        """
        base_e = base_edges_gdf.copy()
        base_n = base_nodes_gdf.copy()
        aux_e = aux_edges_gdf.copy()
        aux_n = aux_nodes_gdf.copy()

        aux_e, aux_n = self._exclude_roads(base_e, aux_e, aux_n)
        # Establish connections between all Base roundabout nodes and dead-end nodes to other auxiliary nodes
        aux_e, aux_n, base_n = self._connect_by_nodes(base_n, aux_n, aux_e, N_ROUNDABOUT)
        aux_e, aux_n, base_n = self._connect_by_nodes(base_n, aux_n, aux_e, N_DEAD_END)

        # Establish connections between all auxiliary roundabout nodes and dead-end nodes to other base nodes
        base_e, base_n, aux_n = self._connect_by_nodes(aux_n, base_n, base_e, N_ROUNDABOUT)
        base_e, base_n, aux_n = self._connect_by_nodes(aux_n, base_n, base_e, N_DEAD_END)

        aux_e, aux_n = self._expunge_redundant_edges(aux_e, aux_n, base_n)
        aux_e = self._reindex_to_base_edges(base_e, aux_e)
        base_e = pd.concat([base_e, aux_e])
        base_n = pd.concat([base_n, aux_n])
        base_n = self._remove_redundant_nodes(base_n, base_e)

        return base_e, base_n

    def _exclude_roads(self, base_e: gpd.GeoDataFrame, aux_e: gpd.GeoDataFrame, aux_n: gpd.GeoDataFrame) \
            -> (gpd.GeoDataFrame, gpd.GeoDataFrame):
        """
        Removes roads in the aux_e dataframe that are already in the base_e dataframe. And removes all 'dead end' nodes
        corresponding to these roads that are in aux_n
        :param base_e: Geodataframe of all edges in the base network
        :param aux_e: Geodataframe of all edges in the auxiliary network to be copied into the base
        :param aux_n: Geodataframe of all nodes in the auxiliary network to be copied into the base
        :return: A tuple of updated dataframes aux_e and aux_n
        """
        # Temporarily de-activate warning
        pd.options.mode.chained_assignment = None

        roads_to_exclude = base_e[HE_ROAD_NO].unique()
        aux_e["is_in_list"] = aux_e[HE_ROAD_NO].apply(lambda x: x in roads_to_exclude)

        red_from_nodes = aux_e.loc[(aux_e["is_in_list"] == True) & (aux_e[FROM_NODE] != "None"), FROM_NODE]
        red_to_nodes = aux_e.loc[(aux_e["is_in_list"] == True) & (aux_e[TO_NODE] != "None"), TO_NODE]

        aux_n.drop(index=aux_n.index[(aux_n[N_NODE_ID].isin(red_from_nodes)) & (aux_n[N_TYPE] == N_DEAD_END)],
                   inplace=True)

        aux_n.drop(index=aux_n.index[(aux_n[N_NODE_ID].isin(red_to_nodes)) & (aux_n[N_TYPE] == N_DEAD_END)],
                   inplace=True)

        aux_e = aux_e.loc[aux_e["is_in_list"] == False]
        aux_e.drop("is_in_list", axis=1, inplace=True)
        pd.options.mode.chained_assignment = 'warn'

        print("Finished excluding roads")
        return aux_e, aux_n

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
        distance = self._euclidean_distance(first_coords, sec_coords)

        return distance <= tolerance

    def _connect_by_nodes(self, base_n: gpd.GeoDataFrame, aux_n: gpd.GeoDataFrame, aux_e: gpd.GeoDataFrame,
                          node_type: str) -> (gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame):
        """
        Establishes connections between all nodes of a particular 'node_type' in the base dataframe to other
        dead-end node in the aux dataframe.
        :param base_n: Dataframe of nodes in which nodes of node_type will be extracted and used to establish
        connections with other nodes in aux dataframe
        :param aux_n: Dataframe of nodes used to identify any that are close enough to the node of node_type
        from base_n
        :param aux_e: Corresponding dataframe of edges connected to aux_n
        :param node_type: The type of node to be iterated through in base_n
        :return: Updated aux_e, aux_n, and base_n tuple.
        """
        IS_CONNECTED = "is_connected"
        base_n[N_COORD] = base_n[GEOMETRY].apply(lambda x: extract_coord_at_index(x, 0))
        aux_n[N_COORD] = aux_n[GEOMETRY].apply(lambda x: extract_coord_at_index(x, 0))
        sel_nodes = base_n.loc[base_n[N_TYPE] == node_type]

        for index, node in sel_nodes.iterrows():
            sel_coord = node.Coord
            sel_buffer = node.Extent

            aux_n[IS_CONNECTED] = aux_n[N_COORD].apply(lambda x: self._is_connected(sel_coord, x, sel_buffer))

            nodes_replacing = aux_n.loc[aux_n[IS_CONNECTED] == True, N_NODE_ID]

            if len(nodes_replacing) > 0 and node.Type == N_DEAD_END:
                base_n.at[index, N_TYPE] = N_JUNCTION

            aux_e.loc[aux_e[FROM_NODE].isin(nodes_replacing), FROM_NODE] = node.node_id
            aux_e.loc[aux_e[TO_NODE].isin(nodes_replacing), TO_NODE] = node.node_id

            aux_n.drop(index=aux_n.index[aux_n[N_NODE_ID].isin(nodes_replacing)], inplace=True)

            aux_n.drop(IS_CONNECTED, axis=1, inplace=True)

        aux_n.drop(N_COORD, axis=1, inplace=True)
        base_n.drop(N_COORD, axis=1, inplace=True)

        return aux_e, aux_n, base_n

    def _reindex_to_base_edges(self, base_e: gpd.GeoDataFrame, aux_e: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Updates indices of the aux_e dataframe based on the indices of the base_e dataframe.
        :param base_e: dataframe of edges
        :param aux_e: dataframe of edges
        :return: re-indexed aux_e
        """
        offset = len(base_e)
        aux_e = self._reindex(aux_e)
        aux_e[INDEX] += offset
        aux_e[PREV_IND] += offset
        aux_e[NEXT_IND] += offset
        aux_e.index += offset

        return aux_e

    def _reindex(self, aux_e: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Resets indices of the dataframe aux_e, and also updates the prev_ind and next_ind columns
        :param aux_e: Dataframe of edges
        :return: Updated aux_e
        """
        old_ind = aux_e[INDEX].tolist()

        aux_e.reset_index(drop=True, inplace=True)
        aux_e[INDEX] = aux_e.index
        aux_e[PREV_IND] = aux_e.loc[pd.isna(aux_e[PREV_IND]) == False, PREV_IND].apply(lambda x: old_ind.index(int(x)))
        aux_e[NEXT_IND] = aux_e.loc[pd.isna(aux_e[NEXT_IND]) == False, NEXT_IND].apply(lambda x: old_ind.index(int(x)))
        return aux_e

    def _remove_redundant_nodes(self, combined_n: gpd.GeoDataFrame, combined_e: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Removes all nodes in combined_n that are not prevalent in combined_e
        :param combined_n: dataframe of nodes
        :param combined_e: dataframe of edges
        :return: updated dataframe of nodes with redundant nodes removed
        """
        used_nodes_from = list(combined_e.loc[pd.isna(combined_e[FROM_NODE]) == False, FROM_NODE].unique())
        used_nodes_to = list(combined_e.loc[pd.isna(combined_e[TO_NODE]) == False, TO_NODE].unique())

        used_nodes = used_nodes_to
        used_nodes.extend(used_nodes_from)
        used_nodes = list(set(used_nodes))

        combined_n = combined_n.loc[combined_n[N_NODE_ID].isin(used_nodes)]

        return combined_n

    def _expunge_redundant_edges(self, aux_e: gpd.GeoDataFrame, aux_n: gpd.GeoDataFrame, base_n: gpd.GeoDataFrame) \
            -> (gpd.GeoDataFrame, gpd.GeoDataFrame):
        """
        Identifies and removes any edges that are not connected to the base network
        :param aux_e: dataframe of auxiliary edges
        :param aux_n: dataframe of auxiliary nodes
        :param base_n: dataframe of nodes representing the base network
        :return: Updated auxiliary dataframe of edges and nodes
        """
        IN_NETWORK = "in_network"
        VISITED = "visited"

        connected_nodes = base_n[N_NODE_ID].tolist()
        indices = aux_e.INDEX.values.tolist()
        aux_e[IN_NETWORK] = False
        aux_e[VISITED] = 0

        for index in indices:
            if aux_e.loc[index][IN_NETWORK] == 0:
                if self._search_road_network(index, aux_e, connected_nodes):
                    aux_e.loc[aux_e[VISITED] == True, IN_NETWORK] = 1
                else:
                    aux_e.loc[aux_e[VISITED] == True, IN_NETWORK] = -1
                aux_e[VISITED] = False

        aux_e.drop(index=aux_e.index[aux_e[IN_NETWORK] == -1], inplace=True)

        aux_e.drop([IN_NETWORK, VISITED], axis=1, inplace=True)

        return aux_e, aux_n

    def _search_road_network(self, edge_ind: int, aux_e: gpd.GeoDataFrame, list_nodes: list) -> bool:
        """
        Searches through network recusively starting at edge_ind and returns true if connected to a node in list_node
        :param edge_ind: Index of the edge to be assessed
        :param aux_e: dataframe of edges to be pruned
        :param list_nodes: List of nodes that to be used as a basis to check if the edge is connected
        :return: True if edge is connected to a node that is in list_nodes, false otherwise
        """
        VISITED = "visited"

        #Mark the current edge as visited
        aux_e.at[aux_e[INDEX] == edge_ind, VISITED] = True
        edge = aux_e[aux_e[INDEX] == edge_ind]

        #Check if current edge is linked to another edge, and recursively search
        if not pd.isna(edge.NEXT_IND).values[0]:
            next_edge = aux_e[aux_e[INDEX] == int(edge.NEXT_IND.values[0])]
            if not next_edge.visited.values[0]:
                if self._search_road_network(int(edge.NEXT_IND.values[0]), aux_e, list_nodes):
                    return True
            elif next_edge.in_network.values[0] == 1:
                return True

        if not pd.isna(edge.PREV_IND).values[0]:
            prev_edge = aux_e[aux_e[INDEX] == int(edge.PREV_IND.values[0])]
            if not prev_edge.visited.values[0]:
                if self._search_road_network(int(edge.PREV_IND.values[0]), aux_e, list_nodes):
                    return True
                else:
                    return False
            elif prev_edge.in_network.values[0] == 1:
                return True

        #If edge is connected to a node, then run through _search_node
        if edge.TO_NODE.values[0] != HE_NONE:
            node_id = edge.TO_NODE.values[0]
            if self._search_node(node_id, edge_ind, aux_e, list_nodes):
                return True

        if edge.FROM_NODE.values[0] != HE_NONE:
            node_id = edge.FROM_NODE.values[0]
            if self._search_node(node_id, edge_ind, aux_e, list_nodes):
                return True

        return False

    def _search_node(self, node_id: str, edge_ind: int, aux_e: gpd.GeoDataFrame, list_nodes: list) -> bool:
        """
        Checks if node is part of list_nodes, and returns true. Otherwise recusively searches through next
        unvisited connected edge, returns false otherwise.
        :param node_id: ID of node to be examined
        :param edge_ind: Index of edge that the node is connected to
        :param aux_e: dataframe of edges of the network that is being assessed
        :param list_nodes: List of nodes that to be used as a basis to check if the edge is connected
        :return: True if node is in list_nodes, otherwise if all edges connected to node have been visited, then
        returns false
        """
        VISITED = "visited"
        IN_NETWORK = "in_network"
        if node_id in list_nodes:
            return True
        else:
            connected_edges = aux_e.loc[(aux_e[VISITED] == False) & ((aux_e[FROM_NODE] == node_id) |
                                                                       (aux_e[TO_NODE] == node_id))]
            connected_edges = connected_edges[connected_edges[INDEX] != edge_ind]

            if len(connected_edges) > 0:
                if len(connected_edges[connected_edges[IN_NETWORK] == 1]) > 0:
                    return True
                next_edge_index = connected_edges.iloc[0][INDEX]
                if self._search_road_network(next_edge_index, aux_e, list_nodes):
                    return True
        return False
