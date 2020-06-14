from RoadNetwork.Network.RoadNetworkBuilder import *
import numpy as np


class OSRoadsNetworkBuilder(RoadNetworkBuilder):

    def __init__(self, connection_threshold=5):

        super().__init__(connection_threshold)

    def _connect_road_segments_based_on_funct_name(self, roads_gdf: gpd.GeoDataFrame,
                                                   funct_name: str) -> gpd.GeoDataFrame:
        """
        Explicitly connects all road segments by function name and geometry
        :param he_df: Geodataframe of roads data
        :funct_name: name of road type to perform connection operation on
        :return: A GeoDataframe with extra columns that connects each road segment
        """

        funct_gdf = roads_gdf.loc[roads_gdf[HE_FUNCT_NAME] == funct_name]
        road_numbers = funct_gdf.ROA_NUMBER.unique()
        print(road_numbers)

        for road_number in road_numbers:
            carriageway = funct_gdf.loc[funct_gdf[HE_ROAD_NO] == road_number]
            carriageway_size = len(carriageway)

            for i in range(carriageway_size):

                segment = carriageway.iloc[i, :]
                index = int(segment.INDEX)

                if pd.isna(segment.NEXT_IND) == False and \
                        pd.isna(segment.PREV_IND) == False:
                    continue

                first_coord = segment.FIRST_COORD
                last_coord = segment.LAST_COORD

                #Check any connections at last_coord end
                connecting_road_last_coord_a = carriageway[carriageway[FIRST_COORD].
                    apply(lambda x: self._are_coordinates_connected(x, last_coord))]

                connecting_road_last_coord_b = carriageway[carriageway[LAST_COORD].
                    apply(lambda x: self._are_coordinates_connected(x, last_coord))]


                #Remove the index corresponding to its own
                connecting_road_last_coord_b = connecting_road_last_coord_b.loc[connecting_road_last_coord_b[INDEX] != index]

                if len(connecting_road_last_coord_a) == 1 and len(connecting_road_last_coord_b) == 0:
                    connecting_index = int(connecting_road_last_coord_a[INDEX].values[0])
                    roads_gdf.at[index, NEXT_IND] = connecting_index
                    roads_gdf.at[connecting_index, PREV_IND] = index

                elif len(connecting_road_last_coord_a) == 0 and len(connecting_road_last_coord_b) == 1:
                    connecting_index = int(connecting_road_last_coord_b[INDEX].values[0])
                    roads_gdf.at[index, NEXT_IND] = connecting_index
                    roads_gdf.at[connecting_index, PREV_IND] = index

                    #Reconfigure coordinate orientation
                    roads_gdf = self._swap_coords(roads_gdf, connecting_index)
                    funct_gdf = roads_gdf.loc[roads_gdf[HE_FUNCT_NAME] == funct_name]
                    carriageway = funct_gdf.loc[roads_gdf[HE_ROAD_NO] == road_number]

                #Check any connections at first_coord end
                connecting_road_first_coord_a = carriageway[carriageway[FIRST_COORD].
                    apply(lambda x: self._are_coordinates_connected(x, first_coord))]

                connecting_road_first_coord_b = carriageway[carriageway[LAST_COORD].
                    apply(lambda x: self._are_coordinates_connected(x, first_coord))]

                connecting_road_first_coord_a = connecting_road_first_coord_a.loc[connecting_road_first_coord_a[INDEX] != index]

                if len(connecting_road_first_coord_a) == 1 and len(connecting_road_first_coord_b) == 0:
                    connecting_index = int(connecting_road_first_coord_a[INDEX].values[0])
                    roads_gdf.at[index, PREV_IND] = connecting_index
                    roads_gdf.at[connecting_index, NEXT_IND] = index

                    roads_gdf = self._swap_coords(roads_gdf, connecting_index)

                elif len(connecting_road_first_coord_a) == 0 and len(connecting_road_first_coord_b) == 1:
                    connecting_index = int(connecting_road_first_coord_b[INDEX].values[0])
                    roads_gdf.at[index, PREV_IND] = connecting_index
                    roads_gdf.at[connecting_index, NEXT_IND] = index

                #Update dataframe prior to next iteration
                funct_gdf = roads_gdf.loc[roads_gdf[HE_FUNCT_NAME] == funct_name]
                carriageway = funct_gdf.loc[roads_gdf[HE_ROAD_NO] == road_number]

        print("Finishing _connect_road_segments_based_on_funct_name")

        return roads_gdf


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
