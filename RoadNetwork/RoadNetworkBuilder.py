from math import sqrt

from shapely.geometry import MultiLineString, LineString
from abc import ABC, abstractmethod
from GeoDataFrameAux import *
from RoadNetwork.ColumnNames import *

class RoadNetworkBuilder(ABC):

    def build_road_network_gdf(self, roads_gdf: gpd.GeoDataFrame) -> (gpd.GeoDataFrame, dict):
        """
        Modifies the roads_gdf with extra columns indicating edges and nodes
        :param roads_gdf: Roads geodataframe
        :return: updated roads_df containing new columns prev_ind, next_ind, from_node, to_node, and index. And nodes_df
        containing the node IDs.
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
        # Link all main carriageways and slip roads
        roads_gdf = self._connect_road_segments_based_on_funct_name(roads_gdf, MAIN_CARRIAGEWAY)
        roads_gdf = self._connect_road_segments_based_on_funct_name(roads_gdf, SLIP_ROAD)

        # link_main_cariageways_to_slip_roads
        roads_gdf, slip_road_nodes = self._connect_main_carriageways_to_slip_roads(roads_gdf, nodes)

        # link_roundabouts_to_segments
        roads_gdf, roundabout_nodes = self._connect_roads_to_roundabouts(roads_gdf, nodes)

        # set new nodes for all remaining ends of roads that are not connected
        roads_gdf, dead_end_nodes = self._assign_nodes_to_dead_end_roads(roads_gdf, nodes)

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

    def _extract_list_of_coords_from_line_object(self, line_object) -> [(int,int)]:
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

    @abstractmethod
    def _connect_road_segments_based_on_funct_name(self, roads_gdf: gpd.GeoDataFrame,
                                                   funct_name: str) -> gpd.GeoDataFrame:
        pass

    @abstractmethod
    def _connect_main_carriageways_to_slip_roads(self, roads_gdf: gpd.GeoDataFrame,
                                                 nodes: dict) -> (gpd.GeoDataFrame, dict):
        pass

    @abstractmethod
    def _connect_roads_to_roundabouts(self, roads_gdf: gpd.GeoDataFrame,
                                      nodes: dict) -> (gpd.GeoDataFrame, dict):
        pass

    @abstractmethod
    def _assign_nodes_to_dead_end_roads(self, roads_gdf: gpd.GeoDataFrame,
                                        nodes: dict) -> (gpd.GeoDataFrame, dict):
        pass
