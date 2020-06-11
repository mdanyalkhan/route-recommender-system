from RoadNetwork.RoadNetworkBuilder import *
import numpy as np

class HERoadsNetworkBuilder(RoadNetworkBuilder):

    def __init__(self, connection_threshold=10, min_spacing_for_roundabout_resolution=2):
        self.THRESHOLD = connection_threshold
        self.MIN_SPACING = min_spacing_for_roundabout_resolution

    def _connect_road_segments_based_on_funct_name(self, roads_gdf: gpd.GeoDataFrame,
                                                   funct_name: str) -> gpd.GeoDataFrame:
        """
        Explicitly connects all road segments by function name and geometry
        :param he_df: Geodataframe of roads data
        :funct_name: name of road type to perform connection operation on
        :return: A GeoDataframe with extra columns that connects each road segment
        """
        print("Starting _connect_road_segments_based_on_funct_name")

        funct_gdf = roads_gdf.loc[roads_gdf[FUNCT_NAME] == funct_name]
        road_numbers = funct_gdf.ROA_NUMBER.unique()
        directions = funct_gdf.DIREC_CODE.unique()

        for road_number in road_numbers:
            for direction in directions:
                carriageway = funct_gdf.loc[(funct_gdf[ROAD_NO] == road_number) &
                                            (funct_gdf[DIRECTION] == direction)]

                for index, segment in carriageway.iterrows():

                    last_coord = segment.LAST_COORD
                    connecting_road = carriageway.index[carriageway[FIRST_COORD].
                        apply(lambda x: self._are_coordinates_connected(x, last_coord))].tolist()

                    if len(connecting_road) == 1:
                        roads_gdf.loc[index, NEXT_IND] = connecting_road[0]
                        roads_gdf.loc[connecting_road[0], PREV_IND] = index

        print("Finishing _connect_road_segments_based_on_funct_name")

        return roads_gdf

    def _connect_main_carriageways_to_slip_roads(self, roads_gdf: gpd.GeoDataFrame,
                                                 node_dict: dict) -> (gpd.GeoDataFrame, dict):
        """
        Identfies and establishes connections between slip roads and main carriageways. Where
        connections are identified, a new node is generated and incorporated into the roads
        geospatial data structure.

        :param he_df: roads geospatial datastructure containing the main carriageways and slip roads
        :param node_dict: existing data structure containing the list of nodes
        :return: updated he_df and node_dict
        """

        print("Starting _connect_main_carriageways_to_slip_roads")

        slip_roads_df = roads_gdf.loc[roads_gdf[FUNCT_NAME] == SLIP_ROAD]
        slip_roads_df = slip_roads_df.loc[(pd.isna(roads_gdf[PREV_IND])) | (pd.isna(roads_gdf[NEXT_IND]))]

        for _, slip_road in slip_roads_df.iterrows():
            index = slip_road.INDEX

            if pd.isna(slip_road.PREV_IND):  # If PREV_IND is <NA> then:
                first_coord = slip_road.FIRST_COORD
                min_index, min_dist = self._find_closest_main_carriageway(roads_gdf, first_coord,
                                                                          use_first_coord_of_main_carriageway=False)
                roads_gdf = self._update_connections_and_assign_nodes(roads_gdf, node_dict, first_coord,
                                                                      index, min_index, min_dist)

            if pd.isna(slip_road.NEXT_IND):
                last_coord = slip_road.LAST_COORD
                min_index, min_dist = self._find_closest_main_carriageway(roads_gdf, last_coord)
                roads_gdf = self._update_connections_and_assign_nodes(roads_gdf, node_dict, last_coord, index,
                                                                      min_index, min_dist, is_prev=False)

        print("Finishing link_main_carriageways_to_slip_roads")
        return roads_gdf, node_dict

    def _connect_roads_to_roundabouts(self, roads_gdf: gpd.GeoDataFrame,
                                      node_dict: dict) -> (gpd.GeoDataFrame, dict):
        """
        Identifies and establishes connections between all road segments and connections. Where
        connections are identified, a new node is generated and incorporated into the roads
        geospatial data structure.

        :param roads_gdf: geospatial data structure containing the main carriageways, slip roads, and roundabouts
        :param node_dict: Existing data structure containing list of roundabout nodes
        :return: updated roads_gdf and node_dict
        """
        print("Starting link_roundabouts_to_segments")
        # Select all roundabouts
        roundabout_df = roads_gdf.loc[roads_gdf[FUNCT_NAME] == ROUNDABOUT]
        # For every roundabout do the following:
        for _, roundabout in roundabout_df.iterrows():
            # Set representative coordinate of roundabout and set up node into node_dict
            node_coord = self._calculate_mean_roundabout_pos(roundabout)
            roundabout_coords = self._extract_list_of_coords_from_line_object(roundabout[GEOMETRY])
            roundabout_refined_coords = self._increase_resolution_of_line(roundabout_coords)
            node_dict = self._assign_new_node_id(node_dict, node_coord, "R")

            # Identify the closest of distances between the roundabout and
            # the FIRST_COORD and LAST_COORD of each road segment.
            roads_gdf["distance_first"] = roads_gdf.loc[(roads_gdf[FUNCT_NAME] == MAIN_CARRIAGEWAY) |
                                                        (roads_gdf[FUNCT_NAME] == SLIP_ROAD), FIRST_COORD] \
                .apply(lambda x: self._proximity_of_road_to_roundabout(roundabout_refined_coords, x))

            roads_gdf["distance_last"] = roads_gdf.loc[(roads_gdf[FUNCT_NAME] == MAIN_CARRIAGEWAY) |
                                                       (roads_gdf[FUNCT_NAME] == SLIP_ROAD), LAST_COORD] \
                .apply(lambda x: self._proximity_of_road_to_roundabout(roundabout_refined_coords, x))

            roads_gdf.loc[roads_gdf["distance_first"] <= self.THRESHOLD, FROM_NODE] = node_dict[NODE_ID][-1]
            roads_gdf.loc[roads_gdf["distance_first"] <= self.THRESHOLD, PREV_IND] = pd.NA

            roads_gdf.loc[roads_gdf["distance_last"] <= self.THRESHOLD, TO_NODE] = node_dict[NODE_ID][-1]
            roads_gdf.loc[roads_gdf["distance_last"] <= self.THRESHOLD, NEXT_IND] = pd.NA
            roads_gdf.drop(['distance_last', 'distance_first'], axis=1, inplace=True)

        print("Finishing link_roundabouts_to_segments")

        return roads_gdf, node_dict

    def _assign_nodes_to_dead_end_roads(self, roads_gdf: gpd.GeoDataFrame,
                                        node_dict: dict) -> (gpd.GeoDataFrame, dict):
        """
        Assigns nodes to all other roads that have ends that are not connected
        :param he_df: roads dataframe
        :param node_dict: nodes data structure to record new nodes
        :return: updated he_df and node_dict
        """
        print("Starting assign_nodes_to_dead_end_roads")
        dead_ends = roads_gdf.loc[(roads_gdf[FROM_NODE] == NONE) | (roads_gdf[TO_NODE] == NONE)]
        dead_ends = dead_ends.loc[(pd.isna(roads_gdf[PREV_IND])) | (pd.isna(roads_gdf[NEXT_IND]))]
        dead_ends = dead_ends.loc[(roads_gdf[FUNCT_NAME] == MAIN_CARRIAGEWAY) |
                                  (roads_gdf[FUNCT_NAME] == SLIP_ROAD)]
        for index, dead_end in dead_ends.iterrows():
            if pd.isna(dead_end.PREV_IND) and dead_end.FROM_NODE == NONE:
                coord = dead_end.FIRST_COORD
                node_dict = self._assign_new_node_id(node_dict, coord, "D")

                roads_gdf.at[index, FROM_NODE] = node_dict[NODE_ID][-1]
            if pd.isna(dead_end.NEXT_IND) and dead_end.TO_NODE == NONE:
                coord = dead_end.LAST_COORD
                node_dict = self._assign_new_node_id(node_dict, coord, "D")
                roads_gdf.at[index, TO_NODE] = node_dict[NODE_ID][-1]

        print("Finishing assign_nodes_to_dead_end_roads")

        return roads_gdf, node_dict

    def _are_coordinates_connected(self, coord1: tuple, coord2: tuple) -> (float, float):
        """
        Determines whether two coordinates in space are sufficiently close
        :param coord1:
        :param coord2:
        :return: true if the euclidean distance is less than some pre-defined threshold, false otherwise
        """
        return self._euclidean_distance(coord1, coord2) <= self.THRESHOLD

    def _find_closest_main_carriageway(self, roads_gdf: gpd.GeoDataFrame, target_coord: tuple,
                                       use_first_coord_of_main_carriageway: bool = True) -> (int, float):
        """
        Finds the closest main carriageway segment to the target coordinate specified in the argument of the function
        :param roads_gdf: geodataframe containing all main carriageways
        :param target_coord: target coordinates to compare all main carriageways to
        :param use_first_coord_of_main_carriageway: Use FIRST_COORD of main carriageway if true, LAST_COORD otherwise
        :return: the index of the closest main carriageway, and its distance with respect to the target coordinates
        """
        # Set up a temporary column of distances in he_df
        roads_gdf["distances"] = np.inf

        if use_first_coord_of_main_carriageway:
            COORD = FIRST_COORD
        else:
            COORD = LAST_COORD

        carriageway_df = roads_gdf.loc[roads_gdf[FUNCT_NAME] == MAIN_CARRIAGEWAY]
        distances = carriageway_df[COORD].apply(lambda x: self._euclidean_distance(x, target_coord))
        min_dist = distances.min()
        index = distances.index[distances == distances.min()][0]
        min_index = carriageway_df.loc[index, "INDEX"]
        roads_gdf.drop("distances", axis=1, inplace=True)

        return min_index, min_dist

    def _update_connections_and_assign_nodes(self, roads_gdf: gpd.GeoDataFrame, node_dict: dict, target_coord: tuple,
                                             slip_road_index: int, min_index: int, min_dist: float,
                                             is_prev: bool = True) -> gpd.GeoDataFrame:
        """
        Re-assigns the main carriageway's link with a slip road and sets the corresponding nodes
        :param
         roads_gdf: The roads geodataframe containing the main carriageway and slip roads
        :param node_dict: Dictionary of node IDs and their corresponding coordinates
        :param min_index: Index of the carriageway closest to the slip road
        :param min_dist: Distance of the carriageway with respect to the slip road
        :param is_prev: Establishes whether connection is with respect to the beginning or end of slip road
        :return: roads_gdf with updates to reflect connectivity and nodal connection between slip road and carriageways
        """
        if is_prev:
            ind_a = NEXT_IND
            ind_b = PREV_IND
            node_a = FROM_NODE
            node_b = TO_NODE
        else:
            ind_a = PREV_IND
            ind_b = NEXT_IND
            node_a = TO_NODE
            node_b = FROM_NODE

        if min_dist < self.THRESHOLD:
            node_dict = self._assign_new_node_id(node_dict, target_coord, "S")
            # Update connections to adjacent carriageway segment (if there is one)
            if not pd.isna(roads_gdf.loc[roads_gdf[INDEX] == min_index, ind_a].values[0]):
                index = roads_gdf.loc[roads_gdf[INDEX] == min_index, ind_a].values[0]
                roads_gdf.loc[roads_gdf[INDEX] == index, ind_b] = pd.NA
                roads_gdf.loc[roads_gdf[INDEX] == index, node_a] = node_dict[NODE_ID][-1]
            # update connection to current carriageway
            roads_gdf.loc[roads_gdf[INDEX] == min_index, ind_a] = pd.NA
            roads_gdf.loc[roads_gdf[INDEX] == min_index, node_b] = node_dict[NODE_ID][-1]
            roads_gdf.loc[roads_gdf[INDEX] == slip_road_index, node_a] = node_dict[NODE_ID][-1]

        return roads_gdf

    def _calculate_mean_roundabout_pos(self, roundabout: gpd.GeoDataFrame) -> (float, float):
        """
        Calculates the mean coordinates of the roundabout
        :param roundabout: geodataframe of roundabout
        :return: mean coordinates of roundabout
        """
        coords = list(roundabout[GEOMETRY].coords)
        n = len(coords)
        x_sum = 0
        y_sum = 0

        for coord in coords:
            x_sum += coord[0]
            y_sum += coord[1]
        x_ave = x_sum / n
        y_ave = y_sum / n

        return x_ave, y_ave

    def _increase_resolution_of_line(self, line_coords: list) -> list:
        """
        Increases the number of points in the line object
        :param line_coords: current number of points in the line object
        :return: Increased number of points within line_coords
        """
        n = len(line_coords)
        index = 1

        while index < n:
            coord_a = line_coords[index - 1]
            coord_b = line_coords[index]

            if self._euclidean_distance(coord_a, coord_b) > self.MIN_SPACING:

                midpoint = self._calculate_midpoint(coord_a, coord_b)
                line_coords.insert(index, midpoint)
                n += 1
            else:
                index += 1

        return line_coords

    def _calculate_midpoint(self, coord_a: tuple, coord_b: tuple) -> (float, float):
        """
        Calculates the midpoint between two coordinates
        :param coord_a:
        :param coord_b:
        :return: midpoint in tuple
        """
        x1, y1 = coord_a
        x2, y2 = coord_b

        return (x1 + x2) / 2, (y1 + y2) / 2

    def _proximity_of_road_to_roundabout(self, roundabout_coords: list, target_coord: tuple) -> float:
        """
        Calculates the distance of the road segment relative to roundabout
        :param roundabout_coords: geodataframe of roundabout
        :param target_coord: coordinates tuple
        :return nearest_distance: closest distance from roundabout to road segment
        """
        distance = []
        for coord in roundabout_coords:
            distance.append(self._euclidean_distance(coord, target_coord))
        return min(distance)
