from heapq import heappush, heappop
from math import sqrt
from queue import Queue

import geopandas as gpd
import pandas as pd
from shapely import wkt

from GeoDataFrameAux import GeoPointDataFrameBuilder, extract_list_of_coords_from_geom_object, extract_coord_at_index
from RoadGraph.StdColNames import *
from RoadGraph.StdKeyWords import *

# Constants used in this class
from RoadGraph.util import euclidean_distance

FIRST_COORD = "FIRST_COORD"
LAST_COORD = "LAST_COORD"


class StdNodesEdgesGdfBuilder:

    def build_nodes_and_edges_gdf_from_path(self, in_path: str, out_path: str = None,
                                            node_tag: str = "") -> (gpd.GeoDataFrame, gpd.GeoDataFrame):
        """
        Decorator function that builds nodes and edges via a file path instead
        :param in_path: File path containing shapefile
        :param out_path: Optional parameter of file path where edges and nodes geodataframes will be saved
        :param node_tag: Optional node prefix to be added for every new node ID
        :return: The nodes and edges geodataframe
        """
        std_gdf = gpd.read_file(in_path)
        return self.build_nodes_and_edges_gdf(std_gdf, out_path, node_tag)

    def build_nodes_and_edges_gdf(self, std_gdf: gpd.GeoDataFrame, out_path: str = None,
                                  node_tag: str = "") -> (gpd.GeoDataFrame, gpd.GeoDataFrame):
        """
        Builds the nodes geodataframe and edges geodataframe based on the information provided within the
        std_gdf.

        :param std_gdf: Geodataframe containing details of the road segments, must be standardised
        :param out_path: Optional parameter of file path where the edges and nodes geodataframe can be saved.
        :param node_tag: Optional prefix added to each new node ID
        :return: Nodes and edges geodataframe structures
        """
        self.node_tag = node_tag
        std_gdf.insert(loc=0, column=STD_INDEX, value=std_gdf.index)

        # Set up link columns for each road segment (much like block linking)
        std_gdf[STD_PREV_IND] = pd.NA
        std_gdf[STD_NEXT_IND] = pd.NA

        # Extract first and last coordinates of each road segment
        std_gdf[FIRST_COORD] = std_gdf[STD_GEOMETRY].apply(lambda x: extract_coord_at_index(x, 0))
        std_gdf[LAST_COORD] = std_gdf[STD_GEOMETRY].apply(lambda x: extract_coord_at_index(x, -1))

        # Set from_node and to_node columns
        std_gdf[STD_FROM_NODE] = "None"
        std_gdf[STD_TO_NODE] = "None"

        # Set up a dict of nodes
        nodes = {}

        std_gdf, nodes = self._assign_roundabout_nodes(std_gdf, nodes)
        std_gdf, nodes = self._assign_junction_nodes(std_gdf, nodes)
        std_gdf, nodes = self._assign_terminal_nodes(std_gdf, nodes)

        std_gdf.drop([FIRST_COORD, LAST_COORD], axis=1, inplace=True)

        nodes_gdf = self._convert_points_dict_to_gdf(nodes)
        std_gdf = self._remove_redundant_roads(std_gdf, nodes_gdf)

        print("Finished building gdf of the road network")

        if out_path is not None and type(out_path) == str:
            std_gdf.to_file(out_path + "/edges.shp")
            nodes_gdf.to_file(out_path + "/nodes.shp")

        return std_gdf, nodes_gdf

    def _convert_points_dict_to_gdf(self, dict_structure: dict) -> gpd.GeoDataFrame:
        """
        Converts the point dict structure into a geodataframe
        :param dict_structure: dictionary structure of points
        :return: geodataframe of points
        """
        points_df = pd.DataFrame(dict_structure)
        points_df[STD_GEOMETRY] = points_df[STD_GEOMETRY].apply(GeoPointDataFrameBuilder()._build_geometry_object)
        points_df[STD_GEOMETRY] = points_df[STD_GEOMETRY].apply(wkt.loads)

        points_gdf = gpd.GeoDataFrame(points_df, geometry=STD_GEOMETRY)
        points_gdf.crs = {'init': 'epsg:27700'}
        return points_gdf

    def _assign_junction_nodes(self, roads_gdf: gpd.GeoDataFrame, node_dict: dict) -> (gpd.GeoDataFrame, dict):
        """
        Explicitly connects and assigns nodes to all road segments by function name and geometry,
        :param roads_gdf: Geodataframe of roads data
        :param node_dict: dictionary record of all nodes
        :param funct_name: name of road type to perform connection operation on
        :return: Updated roads_gdf and node_dict
        """
        VISITED = 'visited'
        roads_gdf[VISITED] = False
        funct_indices = roads_gdf.index[roads_gdf[STD_ROAD_TYPE] != STD_ROUNDABOUT]

        for i in funct_indices:

            if not roads_gdf.iloc[i][VISITED]:
                segment_queue = Queue()
                connections_queue = Queue()
                segment_queue.put(i)

                while not segment_queue.empty() or not connections_queue.empty():

                    if not segment_queue.empty():
                        current_i = segment_queue.get()
                    else:
                        current_i = connections_queue.get()

                    segment = roads_gdf.iloc[current_i, :]
                    index = int(segment[STD_INDEX])

                    first_coord = segment[FIRST_COORD]
                    last_coord = segment[LAST_COORD]
                    road_no = segment[STD_ROAD_NO]

                    if pd.isna(segment[STD_NEXT_IND]) and segment[STD_TO_NODE] == "None":
                        node_dict, roads_gdf, segment_queue = self._find_connections(roads_gdf, index, last_coord,
                                                                                     node_dict, road_no, segment_queue,
                                                                                     connections_queue,
                                                                                     is_last_coord=True)

                    if pd.isna(segment[STD_PREV_IND]) and segment[STD_FROM_NODE] == "None":
                        node_dict, roads_gdf, segment_queue = self._find_connections(roads_gdf, index, first_coord,
                                                                                     node_dict, road_no, segment_queue,
                                                                                     connections_queue,
                                                                                     is_last_coord=False)
                    roads_gdf.at[index, VISITED] = True

        print("Finishing _connect_road_segments_based_on_funct_name")

        roads_gdf.drop(VISITED, axis=1, inplace=True)
        return roads_gdf, node_dict

    def _find_connections(self, roads_gdf: gpd.GeoDataFrame, index: int,
                          target_coord: (float, float), node_dict: dict, road_no: str, seg_queue: Queue,
                          con_queue: Queue, is_last_coord: bool) -> (dict, gpd.GeoDataFrame):
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
        funct_gdf = roads_gdf.loc[roads_gdf[STD_ROAD_TYPE] != STD_ROUNDABOUT]
        connected_to_road_a = funct_gdf.loc[funct_gdf[FIRST_COORD] == target_coord]
        connected_to_road_b = funct_gdf.loc[funct_gdf[LAST_COORD] == target_coord]

        if is_last_coord:
            connected_to_road_b = connected_to_road_b.loc[connected_to_road_b[STD_INDEX] != index]
            INDEX_A = STD_NEXT_IND
            INDEX_B = STD_PREV_IND
            NODE_A = STD_TO_NODE
        else:
            connected_to_road_a = connected_to_road_a.loc[connected_to_road_a[STD_INDEX] != index]
            INDEX_A = STD_PREV_IND
            INDEX_B = STD_NEXT_IND
            NODE_A = STD_FROM_NODE

        if len(connected_to_road_a) == 1 and len(connected_to_road_b) == 0 \
                and connected_to_road_a[STD_ROAD_NO].values[0] == road_no:

            connecting_index = int(connected_to_road_a[STD_INDEX].values[0])
            roads_gdf.at[index, INDEX_A] = connecting_index
            roads_gdf.at[connecting_index, INDEX_B] = index

            if not is_last_coord:
                roads_gdf = self._swap(roads_gdf, connecting_index, FIRST_COORD, LAST_COORD)
                roads_gdf = self._swap(roads_gdf, connecting_index, STD_FROM_NODE, STD_TO_NODE)

            seg_queue.put(connecting_index)

        elif len(connected_to_road_a) == 0 and len(connected_to_road_b) == 1 \
                and connected_to_road_b[STD_ROAD_NO].values[0] == road_no:

            connecting_index = int(connected_to_road_b[STD_INDEX].values[0])
            roads_gdf.at[index, INDEX_A] = connecting_index
            roads_gdf.at[connecting_index, INDEX_B] = index

            # Reconfigure coordinate orientation
            if is_last_coord:
                roads_gdf = self._swap(roads_gdf, connecting_index, FIRST_COORD, LAST_COORD)
                roads_gdf = self._swap(roads_gdf, connecting_index, STD_FROM_NODE, STD_TO_NODE)

            seg_queue.put(connecting_index)

        elif len(connected_to_road_a) >= 1 or len(connected_to_road_b) >= 1:
            node_dict = self._assign_new_node_id(node_dict, target_coord, STD_N_JUNCTION)
            node_id = node_dict[STD_NODE_ID][-1]

            roads_gdf.at[index, NODE_A] = node_id
            roads_gdf.loc[connected_to_road_a[STD_INDEX].values, STD_FROM_NODE] = node_id
            roads_gdf.loc[connected_to_road_b[STD_INDEX].values, STD_TO_NODE] = node_id

            for i in connected_to_road_a[STD_INDEX].values:
                con_queue.put(i)

        return node_dict, roads_gdf, seg_queue

    def _assign_terminal_nodes(self, roads_gdf: gpd.GeoDataFrame,
                               node_dict: dict) -> (gpd.GeoDataFrame, dict):
        """
        Assigns nodes to all other roads that have ends that are not connected
        :param he_df: roads dataframe
        :param node_dict: nodes data structure to record new nodes
        :return: updated he_df and node_dict
        """
        print("Starting assign_nodes_to_dead_end_roads")
        terminal_roads = roads_gdf.loc[(roads_gdf[STD_FROM_NODE] == STD_NONE) | (roads_gdf[STD_TO_NODE] == STD_NONE)]
        terminal_roads = terminal_roads.loc[(pd.isna(roads_gdf[STD_PREV_IND])) | (pd.isna(roads_gdf[STD_NEXT_IND]))]
        terminal_roads = terminal_roads.loc[(roads_gdf[STD_ROAD_TYPE] == STD_MAIN_CARRIAGEWAY) |
                                            (roads_gdf[STD_ROAD_TYPE] == STD_SLIP_ROAD)]

        for index, terminal_road in terminal_roads.iterrows():
            if pd.isna(terminal_road[STD_PREV_IND]) and terminal_road[STD_FROM_NODE] == STD_NONE:
                coord = terminal_road[FIRST_COORD]
                node_dict = self._assign_new_node_id(node_dict, coord, STD_N_TERMINAL)
                roads_gdf.at[index, STD_FROM_NODE] = node_dict[STD_NODE_ID][-1]

            if pd.isna(terminal_road[STD_NEXT_IND]) and terminal_road[STD_TO_NODE] == STD_NONE:
                coord = terminal_road[LAST_COORD]
                node_dict = self._assign_new_node_id(node_dict, coord, STD_N_TERMINAL)
                roads_gdf.at[index, STD_TO_NODE] = node_dict[STD_NODE_ID][-1]

        print("Finishing assign_nodes_to_dead_end_roads")

        return roads_gdf, node_dict

    def _assign_roundabout_nodes(self, roads_gdf: gpd.GeoDataFrame, node_dict: dict) -> (gpd.GeoDataFrame, dict):
        """
        Assigns a roundabout node and sets this for other road segments
        :param roads_gdf: roads dataframe
        :param node_dict: Dictionary containing list of node IDs
        :return: returns updated roads gdf and node dict
        """
        roundabouts_gdf = roads_gdf.loc[roads_gdf[STD_ROAD_TYPE] == STD_ROUNDABOUT]
        other_roads_gdf = roads_gdf.loc[roads_gdf[STD_ROAD_TYPE] != STD_ROUNDABOUT]
        roundabouts_names = roundabouts_gdf[STD_ROAD_NO].unique()

        for name in roundabouts_names:
            roundabout_gdf = roundabouts_gdf.loc[roundabouts_gdf[STD_ROAD_NO] == name]

            roundabout_coords = self._coords_of_roundabout(roundabout_gdf)
            mean_coord = self._calculate_mean_roundabout_pos(roundabout_coords)
            roundabout_radius = self._calculate_radius_of_roundabout(roundabout_coords, mean_coord)
            node_dict = self._assign_new_node_id(node_dict, mean_coord, STD_N_ROUNDABOUT,
                                                 roundabout_extent=roundabout_radius)

            for index, segment in roundabout_gdf.iterrows():
                first_coord = segment.FIRST_COORD
                last_coord = segment.LAST_COORD

                roads_gdf.loc[roads_gdf[STD_INDEX] == index, STD_FROM_NODE] = node_dict[STD_NODE_ID][-1]
                roads_gdf.loc[roads_gdf[STD_INDEX] == index, STD_TO_NODE] = node_dict[STD_NODE_ID][-1]

                connected_at_start = other_roads_gdf.loc[(other_roads_gdf[FIRST_COORD] == first_coord) |
                                                         (other_roads_gdf[FIRST_COORD] == last_coord)]

                roads_gdf.loc[connected_at_start[STD_INDEX], STD_FROM_NODE] = node_dict[STD_NODE_ID][-1]

                connected_at_end = other_roads_gdf.loc[(other_roads_gdf[LAST_COORD] == first_coord) |
                                                       (other_roads_gdf[LAST_COORD] == last_coord)]

                roads_gdf.loc[connected_at_end[STD_INDEX], STD_TO_NODE] = node_dict[STD_NODE_ID][-1]

        return roads_gdf, node_dict

    def _remove_redundant_roads(self, edges_gdf, nodes_gdf):
        """
        Function not used yet, TO BE TESTED
        :param edges_gdf:
        :param nodes_gdf:
        :return:
        """
        roundabout_nodes = nodes_gdf.loc[nodes_gdf[STD_N_TYPE] == STD_N_ROUNDABOUT]

        roundabout_nodes_list = roundabout_nodes[STD_NODE_ID].tolist()

        redundant_indices = edges_gdf.index[(edges_gdf[STD_ROAD_TYPE] != STD_ROUNDABOUT) &
                                            (edges_gdf[STD_FROM_NODE].isin(roundabout_nodes_list)) &
                                            (edges_gdf[STD_TO_NODE].isin(roundabout_nodes_list)) &
                                            (edges_gdf[STD_FROM_NODE] == edges_gdf[STD_TO_NODE])]

        edges_gdf.drop(index=redundant_indices, inplace=True)

        edges_gdf = self._reindex(edges_gdf)

        return edges_gdf

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

    def _assign_new_node_id(self, node_dict: dict, coords: tuple, node_type: str,
                            roundabout_extent=pd.NA) -> dict:
        """
        Assigns a new node ID into node_dict
        :param node_dict: existing data structure containing list of nodes
        :param coords: coordinate of new node ID
        :return: updated node_dict
        """
        if not bool(node_dict):
            first_term = self.node_tag + "_" + str(0)
            node_dict[STD_NODE_ID] = [first_term]
            node_dict[STD_N_TYPE] = [node_type]
            node_dict[STD_GEOMETRY] = [coords]
            node_dict[STD_N_ROUNDABOUT_EXTENT] = [roundabout_extent]
            return node_dict

        last_node_id = node_dict[STD_NODE_ID][-1]
        last_node_id_list = last_node_id.split("_")
        next_node_id = last_node_id_list[0] + "_" + str(int(last_node_id_list[-1]) + 1)

        node_dict[STD_NODE_ID].extend([next_node_id])
        node_dict[STD_N_TYPE].extend([node_type])
        node_dict[STD_GEOMETRY].extend([coords])
        node_dict[STD_N_ROUNDABOUT_EXTENT].extend([roundabout_extent])

        return node_dict

    def _calculate_mean_roundabout_pos(self, coords: list) -> (float, float):
        """
        Calculates the mean coordinates of the roundabout
        :param roundabout: geodataframe of roundabout
        :return: mean coordinates of roundabout
        """

        n = len(coords)
        x_sum = 0
        y_sum = 0

        for coord in coords:
            x_sum += coord[0]
            y_sum += coord[1]
        x_ave = x_sum / n
        y_ave = y_sum / n

        return x_ave, y_ave

    def _calculate_radius_of_roundabout(self, line_coords: list, central_point: tuple) -> float:
        """
        Calculates the maximum proximity of the roundabout relative to its central point
        :param line_coords: List of coordinates outlining the perimeter of the roundabout
        :param central_point: Central coordinate of the roundabout
        :return: Returns the maximal distance of the roundabout's perimeter to it central point
        """
        radius = 0

        for line_coord in line_coords:
            temp_distance = euclidean_distance(line_coord, central_point)
            if temp_distance > radius:
                radius = temp_distance

        return radius

    def _swap(self, roads_gdf: gpd.GeoDataFrame, index: int, colA: str, colB: str) -> gpd.GeoDataFrame:
        """
        Swaps first_coord and last_coord
        :param roads_gdf: geodataframe of roads
        :param index: index of road feature where swap is to take place
        :return: updated roads_gdf
        """
        first = roads_gdf.at[index, colA]
        second = roads_gdf.at[index, colB]
        roads_gdf.at[index, colA] = second
        roads_gdf.at[index, colB] = first

        return roads_gdf



    def _coords_of_roundabout(self, roundabout_gdf):

        coords = []

        for _, segment in roundabout_gdf.iterrows():
            segment_coords = extract_list_of_coords_from_geom_object(segment[STD_GEOMETRY])
            coords.extend(segment_coords)
        return coords
