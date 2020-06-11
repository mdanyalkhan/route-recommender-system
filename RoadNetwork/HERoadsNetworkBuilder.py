from RoadNetwork.RoadNetworkBuilder import *

class HERoadsNetworkBuilder(RoadNetworkBuilder):

    def __init__(self, connection_threshold = 10):
        self.THRESHOLD = connection_threshold

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

                    if (len(connecting_road) == 1):
                        roads_gdf.loc[index, NEXT_IND] = connecting_road[0]
                        roads_gdf.loc[connecting_road[0], PREV_IND] = index

        print("Finishing link_based_on_funct_name")

        return roads_gdf

    def _connect_main_carriageways_to_slip_roads(self, roads_gdf: gpd.GeoDataFrame,
                                                 nodes: dict) -> (gpd.GeoDataFrame, dict):
        pass

    def _connect_roads_to_roundabouts(self, roads_gdf: gpd.GeoDataFrame,
                                      nodes: dict) -> (gpd.GeoDataFrame, dict):
        pass

    def _assign_nodes_to_dead_end_roads(self, roads_gdf: gpd.GeoDataFrame,
                                        nodes: dict) -> (gpd.GeoDataFrame, dict):
        pass

    def _are_coordinates_connected(self, coord1: tuple, coord2: tuple) -> (float, float):
        """
        Determines whether two coordinates in space are sufficiently close
        :param coord1: 
        :param coord2:
        :return: true if the euclidean distance is less than some pre-defined threshold, false otherwise
        """
        return self._euclidean_distance(coord1, coord2) <= self.THRESHOLD
