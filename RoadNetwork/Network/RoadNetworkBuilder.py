from math import sqrt

from shapely.geometry import MultiLineString
from abc import ABC, abstractmethod
from GeoDataFrameAux import *
from RoadNetwork.Utilities.ColumnNames import *


class RoadNetworkBuilder(ABC):

    def __init__(self, connection_threshold=10):
        self.THRESHOLD = connection_threshold

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
        roads_gdf[FIRST_COORD] = roads_gdf[GEOMETRY].apply(lambda x: self._extract_coord_at_index(x, 0))
        roads_gdf[LAST_COORD] = roads_gdf[GEOMETRY].apply(lambda x: self._extract_coord_at_index(x, -1))

        # Set from_node and to_node columns
        roads_gdf[FROM_NODE] = "None"
        roads_gdf[TO_NODE] = "None"

        # Set up a dict of nodes
        nodes = {}
        # Connect all main carriageways and slip roads
        roads_gdf = self._connect_road_segments_based_on_funct_name(roads_gdf, HE_MAIN_CARRIAGEWAY)
        roads_gdf = self._connect_road_segments_based_on_funct_name(roads_gdf, HE_SLIP_ROAD)

        # Assign nodes between multi-way connected carriageways
        # roads_gdf, nodes = self._nodes_main_carriageways_multiway(roads_gdf, nodes)
        # Assign nodes between main carriageways and slip roads
        roads_gdf, nodes = self._nodes_main_carriageways_to_slip_roads(roads_gdf, nodes)

        # Assign nodes between all roundabouts and nodes
        roads_gdf, nodes = self._nodes_roads_to_roundabouts(roads_gdf, nodes)

        # set new nodes for all remaining ends of roads that are not connected
        roads_gdf, nodes = self._assign_nodes_to_dead_end_roads(roads_gdf, nodes)

        roads_gdf.drop([FIRST_COORD, LAST_COORD], axis=1, inplace=True)

        nodes_gdf = self._convert_points_dict_to_gdf(nodes)
        print("Finished building gdf of the road network")

        return roads_gdf, nodes_gdf

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

    def _are_coordinates_connected(self, coord1: tuple, coord2: tuple) -> (float, float):
        """
        Determines whether two coordinates in space are sufficiently close
        :param coord1:
        :param coord2:
        :return: true if the euclidean distance is less than some pre-defined threshold, false otherwise
        """
        return self._euclidean_distance(coord1, coord2) <= self.THRESHOLD

    def _assign_new_node_id(self, node_dict: dict, coords: tuple, prefix: str) -> dict:
        """
        Assigns a new node ID into node_dict
        :param node_dict: existing data structure containing list of nodes
        :param coords: coordinate of new node ID
        :return: updated node_dict
        """
        # Set node_dict with coordinates of FIRST_COORD

        if not bool(node_dict):
            first_term = prefix + str(1)
            node_dict[NODE_ID] = [first_term]
        elif node_dict[NODE_ID][-1][0] != prefix:
            first_term = prefix + str(1)
            node_dict[NODE_ID].extend([first_term])

        else:
            node_dict[NODE_ID].extend([node_dict[NODE_ID][-1][0] +
                                       str(int(node_dict[NODE_ID][-1][1:]) + 1)])

        node_dict.setdefault(GEOMETRY, []).extend([coords])
        return node_dict

    # def _nodes_main_carriageways_multiway(self, roads_gdf, nodes):
    #
    #     sel_gdf = roads_gdf.loc[roads_gdf[HE_FUNCT_NAME] == HE_MAIN_CARRIAGEWAY]
    #     sel_gdf = roads_gdf.loc[(pd.isna(roads_gdf[PREV_IND])) | (pd.isna(roads_gdf[NEXT_IND]))]
    #
    #     for index, segment in sel_gdf.iterrows():
    #         roadNumber = segment.HE_ROAD_NO
    #         #Filter sel_gdf to include only rows that have the same road_no
    #         #Calculate whether the FIRST_COORD of these rows are connected to the LAST_COORD of segment
    #         #Calculate whether
    #         roads_gdf["is_prev_connected"] = roads_gdf.loc[(pd.isna(roads_gdf[PREV_IND]) == False) &
    #                                                        (pd.isna(roads_gdf[NEXT_IND]) == False), FIRST_COORD]\
    #             .apply(lambda x: self._are_coordinates_connected(x, ))
    #     pass

    @abstractmethod
    def _connect_road_segments_based_on_funct_name(self, roads_gdf: gpd.GeoDataFrame,
                                                   funct_name: str) -> gpd.GeoDataFrame:
        pass

    @abstractmethod
    def _nodes_main_carriageways_to_slip_roads(self, roads_gdf: gpd.GeoDataFrame,
                                               node_dict: dict) -> (gpd.GeoDataFrame, dict):
        pass

    @abstractmethod
    def _nodes_roads_to_roundabouts(self, roads_gdf: gpd.GeoDataFrame,
                                    node_dict: dict) -> (gpd.GeoDataFrame, dict):
        pass

    @abstractmethod
    def _assign_nodes_to_dead_end_roads(self, roads_gdf: gpd.GeoDataFrame,
                                        node_dict: dict) -> (gpd.GeoDataFrame, dict):
        pass
