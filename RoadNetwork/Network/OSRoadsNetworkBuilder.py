from RoadNetwork.Network.RoadNetworkBuilder import *
import numpy as np


class OSRoadsNetworkBuilder(RoadNetworkBuilder):

    def __init__(self, connection_threshold=5):
        super().__init__(connection_threshold)

    def _connect_road_segments_based_on_funct_name(self, roads_gdf: gpd.GeoDataFrame, node_dict: dict,
                                                   funct_name: str) -> (gpd.GeoDataFrame, dict):
        """
        Explicitly connects all road segments by function name and geometry
        :param he_df: Geodataframe of roads data
        :funct_name: name of road type to perform connection operation on
        :return: A GeoDataframe with extra columns that connects each road segment
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

    def _find_connections(self, funct_gdf, roads_gdf, index, target_coord, node_dict, road_no, is_last_coord):

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

    # def _connect_road_segments_based_on_funct_name(self, roads_gdf: gpd.GeoDataFrame, node_dict: dict,
    #                                                funct_name: str) -> (gpd.GeoDataFrame, dict):
    #     """
    #     Explicitly connects all road segments by function name and geometry
    #     :param he_df: Geodataframe of roads data
    #     :funct_name: name of road type to perform connection operation on
    #     :return: A GeoDataframe with extra columns that connects each road segment
    #     """
    #
    #     list_of_multiway_connected_roads = []
    #
    #     funct_gdf = roads_gdf.loc[roads_gdf[HE_FUNCT_NAME] == funct_name]
    #     road_numbers = funct_gdf.ROA_NUMBER.unique()
    #
    #     for road_number in road_numbers:
    #         carriageway = funct_gdf.loc[funct_gdf[HE_ROAD_NO] == road_number]
    #         carriageway_size = len(carriageway)
    #
    #         for i in range(carriageway_size):
    #
    #             segment = carriageway.iloc[i, :]
    #             index = int(segment.INDEX)
    #
    #             first_coord = segment.FIRST_COORD
    #             last_coord = segment.LAST_COORD
    #
    #             if pd.isna(segment.NEXT_IND) and segment.TO_NODE == "None":
    #                 #Check any connections at last_coord end
    #                 connecting_road_last_coord_a = carriageway[carriageway[FIRST_COORD].
    #                     apply(lambda x: self._are_coordinates_connected(x, last_coord))]
    #
    #                 connecting_road_last_coord_b = carriageway[carriageway[LAST_COORD].
    #                     apply(lambda x: self._are_coordinates_connected(x, last_coord))]
    #
    #
    #                 #Remove the index corresponding to its own
    #                 connecting_road_last_coord_b = connecting_road_last_coord_b.loc[connecting_road_last_coord_b[INDEX]
    #                                                                                 != index]
    #
    #                 if len(connecting_road_last_coord_a) == 1 and len(connecting_road_last_coord_b) == 0:
    #                     connecting_index = int(connecting_road_last_coord_a[INDEX].values[0])
    #                     roads_gdf.at[index, NEXT_IND] = connecting_index
    #                     roads_gdf.at[connecting_index, PREV_IND] = index
    #
    #                 elif len(connecting_road_last_coord_a) == 0 and len(connecting_road_last_coord_b) == 1:
    #                     connecting_index = int(connecting_road_last_coord_b[INDEX].values[0])
    #                     roads_gdf.at[index, NEXT_IND] = connecting_index
    #                     roads_gdf.at[connecting_index, PREV_IND] = index
    #
    #                     #Reconfigure coordinate orientation
    #                     roads_gdf = self._swap_coords(roads_gdf, connecting_index)
    #                     funct_gdf = roads_gdf.loc[roads_gdf[HE_FUNCT_NAME] == funct_name]
    #                     carriageway = funct_gdf.loc[roads_gdf[HE_ROAD_NO] == road_number]
    #
    #                 elif len(connecting_road_last_coord_a) >= 1 or len(connecting_road_last_coord_b) >= 1:
    #                     node_dict = self._assign_new_node_id(node_dict, last_coord, "X")
    #                     node_id = node_dict[NODE_ID][-1]
    #
    #                     roads_gdf.at[index, TO_NODE] = node_id
    #                     roads_gdf.loc[connecting_road_last_coord_a[INDEX].values, FROM_NODE] = node_id
    #                     roads_gdf.loc[connecting_road_last_coord_b[INDEX].values, TO_NODE] = node_id
    #
    #             if pd.isna(segment.PREV_IND) and segment.FROM_NODE == "None":
    #                 #Check any connections at first_coord end
    #                 connecting_road_first_coord_a = carriageway[carriageway[FIRST_COORD].
    #                     apply(lambda x: self._are_coordinates_connected(x, first_coord))]
    #
    #                 connecting_road_first_coord_b = carriageway[carriageway[LAST_COORD].
    #                     apply(lambda x: self._are_coordinates_connected(x, first_coord))]
    #
    #                 connecting_road_first_coord_a = connecting_road_first_coord_a.loc[connecting_road_first_coord_a[INDEX]
    #                                                                                   != index]
    #
    #                 if len(connecting_road_first_coord_a) == 1 and len(connecting_road_first_coord_b) == 0:
    #                     connecting_index = int(connecting_road_first_coord_a[INDEX].values[0])
    #                     roads_gdf.at[index, PREV_IND] = connecting_index
    #                     roads_gdf.at[connecting_index, NEXT_IND] = index
    #
    #                     roads_gdf = self._swap_coords(roads_gdf, connecting_index)
    #
    #                 elif len(connecting_road_first_coord_a) == 0 and len(connecting_road_first_coord_b) == 1:
    #                     connecting_index = int(connecting_road_first_coord_b[INDEX].values[0])
    #                     roads_gdf.at[index, PREV_IND] = connecting_index
    #                     roads_gdf.at[connecting_index, NEXT_IND] = index
    #
    #                 elif len(connecting_road_first_coord_a) >= 1 or len(connecting_road_first_coord_b) >= 1:
    #                     node_dict = self._assign_new_node_id(node_dict, first_coord, "X")
    #                     node_id = node_dict[NODE_ID][-1]
    #
    #                     roads_gdf.at[index, FROM_NODE] = node_id
    #                     roads_gdf.loc[connecting_road_first_coord_a[INDEX].values, FROM_NODE] = node_id
    #                     roads_gdf.loc[connecting_road_first_coord_b[INDEX].values, TO_NODE] = node_id
    #
    #             #Update dataframe prior to next iteration
    #             funct_gdf = roads_gdf.loc[roads_gdf[HE_FUNCT_NAME] == funct_name]
    #             carriageway = funct_gdf.loc[roads_gdf[HE_ROAD_NO] == road_number]
    #
    #     print("Finishing _connect_road_segments_based_on_funct_name")
    #
    #     return roads_gdf, node_dict

    def _nodes_multiway_connections(self, roads_gdf: gpd.GeoDataFrame, node_dict: dict,
                                    funct_name: str) -> gpd.GeoDataFrame:

        #Filter dataframe to only include funct_name, and either PREV_IND or NEXT_IND (or both) as pd.NA
        pass

    def _nodes_main_carriageways_to_slip_roads(self, roads_gdf: gpd.GeoDataFrame, node_dict: dict) -> (
            gpd.GeoDataFrame, dict):
        pass

    def _nodes_roads_to_roundabouts(self, roads_gdf: gpd.GeoDataFrame, node_dict: dict) -> (gpd.GeoDataFrame, dict):
        pass

    def _assign_nodes_to_dead_end_roads(self, roads_gdf: gpd.GeoDataFrame, node_dict: dict) -> (gpd.GeoDataFrame, dict):
        pass

    def _swap_coords(self, roads_gdf, index):

        first_coord = roads_gdf.at[index, FIRST_COORD]
        last_coord = roads_gdf.at[index, LAST_COORD]
        roads_gdf.at[index, FIRST_COORD] = last_coord
        roads_gdf.at[index, LAST_COORD] = first_coord

        return roads_gdf
