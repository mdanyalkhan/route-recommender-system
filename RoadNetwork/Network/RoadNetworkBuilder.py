from math import sqrt
from shapely.geometry import MultiLineString, LineString
from abc import ABC, abstractmethod
from GeoDataFrameAux import *
from RoadNetwork.Utilities.ColumnNames import *


class RoadNetworkBuilder(ABC):

    def __init__(self, node_tag = ""):
        self.node_tag = node_tag

    def build_road_network_gdf(self, roads_gdf: gpd.GeoDataFrame) -> (gpd.GeoDataFrame, dict):
        """
        Modifies the roads_gdf with extra columns indicating edges and nodes
        :param roads_gdf: Roads geodataframe
        :return: updated roads_df containing new columns prev_ind, next_ind, from_node, to_node, and index.
        And nodes_df containing the node IDs.
         """
        print("Build gdf of the road network")
        # Insert index as column
        roads_gdf.insert(loc=0, column=INDEX, value=roads_gdf.index)
        # Set up link columns for each road segment (much like block linking)
        roads_gdf[PREV_IND] = pd.NA
        roads_gdf[NEXT_IND] = pd.NA
        # Extract first and last coordinates of each road segment
        roads_gdf[FIRST_COORD] = roads_gdf[GEOMETRY].apply(lambda x: extract_coord_at_index(x, 0))
        roads_gdf[LAST_COORD] = roads_gdf[GEOMETRY].apply(lambda x: extract_coord_at_index(x, -1))

        # Set from_node and to_node columns
        roads_gdf[FROM_NODE] = "None"
        roads_gdf[TO_NODE] = "None"

        # Set up a dict of nodes
        nodes = {}

        roads_gdf, nodes = self._connect_all_road_segments(roads_gdf, nodes)

        roads_gdf.drop([FIRST_COORD, LAST_COORD], axis=1, inplace=True)

        nodes_gdf = self._convert_points_dict_to_gdf(nodes)
        print("Finished building gdf of the road network")

        return roads_gdf, nodes_gdf

    def _assign_nodes_to_dead_end_roads(self, roads_gdf: gpd.GeoDataFrame,
                                        node_dict: dict) -> (gpd.GeoDataFrame, dict):
        """
        Assigns nodes to all other roads that have ends that are not connected
        :param he_df: roads dataframe
        :param node_dict: nodes data structure to record new nodes
        :return: updated he_df and node_dict
        """
        print("Starting assign_nodes_to_dead_end_roads")
        dead_ends = roads_gdf.loc[(roads_gdf[FROM_NODE] == HE_NONE) | (roads_gdf[TO_NODE] == HE_NONE)]
        dead_ends = dead_ends.loc[(pd.isna(roads_gdf[PREV_IND])) | (pd.isna(roads_gdf[NEXT_IND]))]
        dead_ends = dead_ends.loc[(roads_gdf[HE_FUNCT_NAME] == HE_MAIN_CARRIAGEWAY) |
                                  (roads_gdf[HE_FUNCT_NAME] == HE_SLIP_ROAD)]
        for index, dead_end in dead_ends.iterrows():
            if pd.isna(dead_end.PREV_IND) and dead_end.FROM_NODE == HE_NONE:
                coord = dead_end.FIRST_COORD
                node_dict = self._assign_new_node_id(node_dict, coord, N_DEAD_END)

                roads_gdf.at[index, FROM_NODE] = node_dict[NODE_ID][-1]
            if pd.isna(dead_end.NEXT_IND) and dead_end.TO_NODE == HE_NONE:
                coord = dead_end.LAST_COORD
                node_dict = self._assign_new_node_id(node_dict, coord, N_DEAD_END)
                roads_gdf.at[index, TO_NODE] = node_dict[NODE_ID][-1]

        print("Finishing assign_nodes_to_dead_end_roads")

        return roads_gdf, node_dict

    def _convert_points_dict_to_gdf(self, dict_structure: dict) -> gpd.GeoDataFrame:
        """
        Converts the point dict structure into a geodataframe
        :param dict_structure: dictionary structure of points
        :return: geodataframe of points
        """
        points_df = pd.DataFrame(dict_structure)
        points_df[GEOMETRY] = points_df[GEOMETRY].apply(GeoPointDataFrameBuilder()._build_geometry_object)
        points_df[GEOMETRY] = points_df[GEOMETRY].apply(wkt.loads)

        points_gdf = gpd.GeoDataFrame(points_df, geometry=GEOMETRY)
        points_gdf.crs = {'init': 'epsg:27700'}
        return points_gdf

    def _extract_coord_at_index(self, line_object, index: int) -> (float, float):
        """
        Returns the coordinates from a LineString or MultiLineString object
        :param line_object: LineString or MultilineString object
        :param index: index of the line_object to extract coordinates from
        :return coordinates in a tuple from line_object at index
        """

        list_of_coords = self._extract_list_of_coords_from_line_object(line_object)
        return list_of_coords[index]

    def _extract_list_of_coords_from_line_object(self, line_object) -> [(int, int)]:
        """
        Returns a list version of the coordinates stored in line_object
        :param line_object: Either a LineString or MultiLineString object
        :return: list of coordinates of line_object
        """
        list_of_coords = []
        if type(line_object) is MultiLineString:
            list_of_lines = list(line_object)
            for line in list_of_lines:
                list_of_coords.extend(list(line.coords))
        else:
            list_of_coords = list(line_object.coords)
        return list_of_coords

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

    def _assign_new_node_id(self, node_dict: dict, coords: tuple, node_type: str) -> dict:
        """
        Assigns a new node ID into node_dict
        :param node_dict: existing data structure containing list of nodes
        :param coords: coordinate of new node ID
        :return: updated node_dict
        """
        if not bool(node_dict):
            first_term = self.node_tag + "_" + str(0)
            node_dict[NODE_ID] = [first_term]
            node_dict[TYPE] = [node_type]
            node_dict[GEOMETRY] = [coords]
            return node_dict

        last_node_id = node_dict[NODE_ID][-1]
        last_node_id_list = last_node_id.split("_")
        next_node_id = last_node_id_list[0] + "_" + str(int(last_node_id_list[-1]) + 1)

        node_dict[NODE_ID].extend([next_node_id])
        node_dict[TYPE].extend([node_type])
        node_dict[GEOMETRY].extend([coords])

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

    @abstractmethod
    def _connect_all_road_segments(self, roads_gdf, nodes) -> (gpd.GeoDataFrame, dict):
        pass

    @abstractmethod
    def _nodes_roads_to_roundabouts(self, roads_gdf: gpd.GeoDataFrame,
                                    node_dict: dict) -> (gpd.GeoDataFrame, dict):
        pass
