from RoadNetwork.Network.RoadNetworkBuilder import *
import numpy as np


class OSRoadsNetworkBuilder(RoadNetworkBuilder):

    def __init__(self, connection_threshold=5):
        super().__init__(connection_threshold)

    def _connect_all_road_segments(self, roads_gdf: gpd.GeoDataFrame, nodes: dict) \
            -> (gpd.GeoDataFrame, dict):
        """
        Overriding function that calls all other function to connect each road segment
        :param roads_gdf: roads geo data frame.
        :param nodes: dictionary containing list of nodes
        :return: Returns updated roads gdf and nodes dict
        """
        roads_gdf, nodes = self._connect_and_assign_nodes_using_funct_name(roads_gdf, nodes, HE_MAIN_CARRIAGEWAY)
        roads_gdf, nodes = self._connect_and_assign_nodes_using_funct_name(roads_gdf, nodes, HE_SLIP_ROAD)

        return roads_gdf, nodes

    def _connect_and_assign_nodes_using_funct_name(self, roads_gdf: gpd.GeoDataFrame, node_dict: dict,
                                                   funct_name: str) -> (gpd.GeoDataFrame, dict):
        """
        Explicitly connects and assigns nodes to all road segments by function name and geometry,
        :param roads_gdf: Geodataframe of roads data
        :param node_dict: dictionary record of all nodes
        :param funct_name: name of road type to perform connection operation on
        :return: Updated roads_gdf and node_dict
        """
        funct_gdf = roads_gdf.loc[roads_gdf[HE_FUNCT_NAME] == funct_name]
        no_of_roads = len(funct_gdf)

        for i in range(no_of_roads):
            segment = funct_gdf.iloc[i, :]
            index = int(segment.INDEX)

            first_coord = segment.FIRST_COORD
            last_coord = segment.LAST_COORD
            road_no = segment.ROA_NUMBER

            if pd.isna(segment.NEXT_IND) and segment.TO_NODE == "None":
                #Find roads connected to last coord
                node_dict, roads_gdf = self._find_connections(funct_gdf, roads_gdf, index, last_coord,
                                                              node_dict, road_no, is_last_coord = True)
                #Update dataframe
                funct_gdf = roads_gdf.loc[roads_gdf[HE_FUNCT_NAME] == funct_name]

            if pd.isna(segment.PREV_IND) and segment.FROM_NODE == "None":

                node_dict, roads_gdf = self._find_connections(funct_gdf, roads_gdf, index, first_coord,
                                                              node_dict, road_no, is_last_coord=False)

                # Update dataframe prior to next iteration
                funct_gdf = roads_gdf.loc[roads_gdf[HE_FUNCT_NAME] == funct_name]

        print("Finishing _connect_road_segments_based_on_funct_name")

        return roads_gdf, node_dict

    def _find_connections(self, funct_gdf: gpd.GeoDataFrame, roads_gdf: gpd.GeoDataFrame, index: int,
                          target_coord: (float, float), node_dict: dict, road_no: str,
                          is_last_coord: bool) -> (dict, gpd.GeoDataFrame):
        """
        Establishes connections between the road feature corresponding to index, and assigns nodes
        where there are either multiple connections or a connection between two different carriageways

        :param funct_gdf: Dataframe of road features that are used for this comparative analysis
        :param roads_gdf: Parent dataframe in which the assignments will take place
        :param index: index of the current road feature that is being examined
        :param target_coord: coordinates of the vertex of the road feature
        :param node_dict: dictionary containing list of created nodes
        :param road_no: Road ID of current road feature
        :param is_last_coord: Checks if the vertex corresponds to the last coordinate or first, and assigns parameters
        accordingly
        :return: Updated node_dict and roads_gdf
        """
        connected_to_road_a = funct_gdf.loc[funct_gdf[FIRST_COORD] == target_coord]
        connected_to_road_b = funct_gdf.loc[funct_gdf[LAST_COORD] == target_coord]

        if is_last_coord:
            connected_to_road_b = connected_to_road_b.loc[connected_to_road_b[INDEX] != index]
            INDEX_A = NEXT_IND
            INDEX_B = PREV_IND
            NODE_A = TO_NODE
        else:
            connected_to_road_a = connected_to_road_a.loc[connected_to_road_a[INDEX] != index]
            INDEX_A = PREV_IND
            INDEX_B = NEXT_IND
            NODE_A = FROM_NODE

        if len(connected_to_road_a) == 1 and len(connected_to_road_b) == 0 \
                and connected_to_road_a[HE_ROAD_NO].values[0] == road_no:
            connecting_index = int(connected_to_road_a[INDEX].values[0])
            roads_gdf.at[index, INDEX_A] = connecting_index
            roads_gdf.at[connecting_index, INDEX_B] = index

            if not is_last_coord:
                roads_gdf = self._swap_coords(roads_gdf, connecting_index)

        elif len(connected_to_road_a) == 0 and len(connected_to_road_b) == 1 \
                and connected_to_road_b[HE_ROAD_NO].values[0] == road_no:
            connecting_index = int(connected_to_road_b[INDEX].values[0])
            roads_gdf.at[index, INDEX_A] = connecting_index
            roads_gdf.at[connecting_index, INDEX_B] = index

            # Reconfigure coordinate orientation
            if is_last_coord:
                roads_gdf = self._swap_coords(roads_gdf, connecting_index)

        elif len(connected_to_road_a) >= 1 or len(connected_to_road_b) >= 1:
            node_dict = self._assign_new_node_id(node_dict, target_coord, "X")
            node_id = node_dict[NODE_ID][-1]

            roads_gdf.at[index, NODE_A] = node_id
            roads_gdf.loc[connected_to_road_a[INDEX].values, FROM_NODE] = node_id
            roads_gdf.loc[connected_to_road_b[INDEX].values, TO_NODE] = node_id

        return node_dict, roads_gdf

    def _nodes_main_carriageways_to_slip_roads(self, roads_gdf: gpd.GeoDataFrame,
                                               node_dict: dict) -> (gpd.GeoDataFrame, dict):
        pass

    def _nodes_roads_to_roundabouts(self, roads_gdf: gpd.GeoDataFrame, node_dict: dict) -> (gpd.GeoDataFrame, dict):
        pass

    def _assign_nodes_to_dead_end_roads(self, roads_gdf: gpd.GeoDataFrame, node_dict: dict) -> (gpd.GeoDataFrame, dict):
        pass

    def _swap_coords(self, roads_gdf: gpd.GeoDataFrame, index: int) -> gpd.GeoDataFrame:
        """
        Swaps first_coord and last_coord
        :param roads_gdf: geodataframe of roads
        :param index: index of road feature where swap is to take place
        :return: updated roads_gdf
        """
        first_coord = roads_gdf.at[index, FIRST_COORD]
        last_coord = roads_gdf.at[index, LAST_COORD]
        roads_gdf.at[index, FIRST_COORD] = last_coord
        roads_gdf.at[index, LAST_COORD] = first_coord

        return roads_gdf
