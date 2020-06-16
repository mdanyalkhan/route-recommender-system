from RoadNetwork.Network.RoadNetworkBuilder import *
import numpy as np
from shapely.ops import linemerge


class OSRoadsNetworkBuilder(RoadNetworkBuilder):

    def __init__(self, node_tag=""):

        super().__init__(node_tag)

    def _connect_all_road_segments(self, roads_gdf: gpd.GeoDataFrame, nodes: dict) \
            -> (gpd.GeoDataFrame, dict):
        """
        Overriding function that calls all other function to connect each road segment
        :param roads_gdf: roads geo data frame.
        :param nodes: dictionary containing list of nodes
        :return: Returns updated roads gdf and nodes dict
        """
        roads_gdf, nodes = self._connect_and_assign_nodes_main_carriageways_slip_roads(roads_gdf, nodes)
        roads_gdf, nodes = self._nodes_roads_to_roundabouts(roads_gdf, nodes)
        roads_gdf, nodes = self._assign_nodes_to_dead_end_roads(roads_gdf, nodes)
        return roads_gdf, nodes

    def _connect_and_assign_nodes_main_carriageways_slip_roads(self, roads_gdf: gpd.GeoDataFrame, node_dict: dict) \
            -> (gpd.GeoDataFrame, dict):
        """
        Explicitly connects and assigns nodes to all road segments by function name and geometry,
        :param roads_gdf: Geodataframe of roads data
        :param node_dict: dictionary record of all nodes
        :param funct_name: name of road type to perform connection operation on
        :return: Updated roads_gdf and node_dict
        """
        funct_indices = roads_gdf.index[roads_gdf[HE_FUNCT_NAME] != HE_ROUNDABOUT]

        for i in funct_indices:
            segment = roads_gdf.iloc[i, :]
            index = int(segment.INDEX)

            first_coord = segment.FIRST_COORD
            last_coord = segment.LAST_COORD
            road_no = segment.ROA_NUMBER

            if pd.isna(segment.NEXT_IND) and segment.TO_NODE == "None":
                node_dict, roads_gdf = self._find_connections(roads_gdf, index, last_coord,
                                                              node_dict, road_no, is_last_coord=True)

            if pd.isna(segment.PREV_IND) and segment.FROM_NODE == "None":
                node_dict, roads_gdf = self._find_connections(roads_gdf, index, first_coord,
                                                              node_dict, road_no, is_last_coord=False)

        print("Finishing _connect_road_segments_based_on_funct_name")

        return roads_gdf, node_dict

    def _find_connections(self, roads_gdf: gpd.GeoDataFrame, index: int,
                          target_coord: (float, float), node_dict: dict, road_no: str,
                          is_last_coord: bool) -> (dict, gpd.GeoDataFrame):
        """
        Establishes connections between the road feature corresponding to index, and assigns nodes
        where there are either multiple connections or a connection between two different carriageways

        :param roads_gdf: Parent dataframe in which the assignments will take place
        :param index: index of the current road feature that is being examined
        :param target_coord: coordinates of the vertex of the road feature
        :param node_dict: dictionary containing list of created nodes
        :param road_no: Road ID of current road feature
        :param is_last_coord: Checks if the vertex corresponds to the last coordinate or first, and assigns parameters
        accordingly
        :return: Updated node_dict and roads_gdf
        """
        funct_gdf = roads_gdf.loc[roads_gdf[HE_FUNCT_NAME] != HE_ROUNDABOUT]
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
            node_dict = self._assign_new_node_id(node_dict, target_coord, N_JUNCTION)
            node_id = node_dict[N_NODE_ID][-1]

            roads_gdf.at[index, NODE_A] = node_id
            roads_gdf.loc[connected_to_road_a[INDEX].values, FROM_NODE] = node_id
            roads_gdf.loc[connected_to_road_b[INDEX].values, TO_NODE] = node_id

        return node_dict, roads_gdf

    def _nodes_roads_to_roundabouts(self, roads_gdf: gpd.GeoDataFrame, node_dict: dict) -> (gpd.GeoDataFrame, dict):
        """
        Assigns a roundabout node and sets this for other road segments
        :param roads_gdf: roads dataframe
        :param node_dict: Dictionary containing list of node IDs
        :return: returns updated roads gdf and node dict
        """
        roundabouts_gdf = roads_gdf.loc[roads_gdf[HE_FUNCT_NAME] == HE_ROUNDABOUT]
        other_roads_gdf = roads_gdf.loc[roads_gdf[HE_FUNCT_NAME] != HE_ROUNDABOUT]
        roundabouts_names = roundabouts_gdf[HE_ROAD_NO].unique()

        for name in roundabouts_names:
            roundabout_gdf = roundabouts_gdf.loc[roundabouts_gdf[HE_ROAD_NO] == name]

            roundabout_coords = self._coords_of_os_roundabout(roundabout_gdf)
            mean_coord = self._calculate_mean_roundabout_pos(roundabout_coords)
            roundabout_radius = self._calculate_radius_of_roundabout(roundabout_coords, mean_coord)
            node_dict = self._assign_new_node_id(node_dict, mean_coord, N_ROUNDABOUT,
                                                 roundabout_extent= roundabout_radius)

            for index, segment in roundabout_gdf.iterrows():
                first_coord = segment.FIRST_COORD
                last_coord = segment.LAST_COORD

                connected_at_start = other_roads_gdf.loc[(other_roads_gdf[FIRST_COORD] == first_coord) |
                                                         (other_roads_gdf[FIRST_COORD] == last_coord)]

                roads_gdf.loc[connected_at_start[INDEX], FROM_NODE] = node_dict[N_NODE_ID][-1]

                connected_at_end = other_roads_gdf.loc[(other_roads_gdf[LAST_COORD] == first_coord) |
                                                       (other_roads_gdf[LAST_COORD] == last_coord)]

                roads_gdf.loc[connected_at_end[INDEX], TO_NODE] = node_dict[N_NODE_ID][-1]

        return roads_gdf, node_dict

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

    def _coords_of_os_roundabout(self, roundabout_gdf):

        coords = []

        for _, segment in roundabout_gdf.iterrows():
            segment_coords = extract_list_of_coords_from_line_object(segment[GEOMETRY])
            coords.extend(segment_coords)
        return coords
