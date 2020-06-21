from queue import Queue

from shapely.geometry import LineString

from GeoDataFrameAux import extract_coord_at_index
from RoadGraph.StdGdfConverter import *
from RoadGraph.StdKeyWords import *
import pandas as pd
import numpy as np

# Column names pertaining to the OS geodataframe
OS_ID = "identifier"
OS_CLASS = "class"
OS_ROAD_NO = "roadNumber"
OS_LENGTH = "length"
OS_ROAD_TYPE = "formOfWay"
OS_GEOMETRY = "geometry"

# Key words pertaining to the OS geodataframe
OS_MOTORWAY = "Motorway"
OS_A_ROAD = "A Road"
OS_SLIP_ROAD = "Slip Road"
OS_ROUNDABOUT = "Roundabout"
OS_MAIN_CARRIAGEWAY_LIST = ["Single Carriageway", "Dual Carriageway",
                            "Collapsed Dual Carriageway", "Shared User Carriageway"]


class OSToStdGdfConverter(StdGdfConverter):
    def _build_std_gdf(self, orig_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Converts a single os geodataframe to an equivalent HE geodataframe
        :param gdf:
        :param roads_to_exclude:
        :return: HE geodataframe converted from the OS geodataframe
        """
        converted_df = self.convert_to_std_df(orig_gdf)

        # Insert geometry
        converted_gdf = gpd.GeoDataFrame(converted_df, geometry=STD_GEOMETRY)
        converted_gdf.crs = {'init': 'epsg:27700'}

        return converted_gdf

    def convert_to_std_df(self, orig_gdf: gpd.GeoDataFrame) -> pd.DataFrame:
        """
        Converts the OS geodataframe to a dataframe compatible to HE's dataframe
        :param orig_gdf: OS_open roads geodataframe
        :param roads_to_exclude: any road numbers to exclude, usually in list form
        :return: OS open roads equivalent data converted to HE-style dataframe
        """
        pd.options.mode.chained_assignment = None

        # Select features that are only motorways and A roads
        sel_gdf = orig_gdf.loc[(orig_gdf[OS_CLASS] == OS_MOTORWAY) | (orig_gdf[OS_CLASS] == OS_A_ROAD)].copy()
        sel_gdf.reset_index(drop=True, inplace=True)

        # Set up a geodataframe with with columns that will be NULL values (such as AREA_NAME)
        null_list = [pd.NA] * len(sel_gdf)
        list_of_null_lists = [null_list] * len(self.std_column_names)
        std_df = pd.DataFrame(np.array(list_of_null_lists).transpose(), columns=self.std_column_names)

        # Insert Road Number
        std_df.loc[:, STD_ROAD_NO] = sel_gdf[OS_ROAD_NO].values

        # Insert Road Type
        road_types = sel_gdf[OS_ROAD_TYPE].apply(self._convert_to_std_road_type)
        std_df.loc[:, STD_ROAD_TYPE] = road_types.values

        # Insert length
        std_df.loc[:, STD_LENGTH] = sel_gdf[OS_LENGTH].values

        # Insert whether is directional:
        std_df.loc[:, STD_IS_DIREC] = False

        #Insert whether road segment is SRN
        if self.srn_list is not None:
            std_df.loc[:, STD_IS_SRN] = std_df.loc[:, STD_ROAD_NO].apply(lambda x: x in self.srn_list)

        # Insert geometry
        geometry_2D = self._convert_LineString_to_2D(sel_gdf[OS_GEOMETRY].values)
        std_df[STD_GEOMETRY] = geometry_2D

        # Rename roundabouts to unique roundabout IDs
        std_df = self._rename_roundabouts(std_df)

        pd.options.mode.chained_assignment = 'warn'
        return std_df

    def _convert_to_std_road_type(self, funct_name: str) -> str:
        """
        Returns HE key funct name
        :param funct_name: OS funct name
        :return: Either HE main carriageway, slip road, or roundabout, otherwise None
        """
        if funct_name in OS_MAIN_CARRIAGEWAY_LIST:
            return STD_MAIN_CARRIAGEWAY
        elif funct_name == OS_SLIP_ROAD:
            return STD_SLIP_ROAD
        elif funct_name == OS_ROUNDABOUT:
            return STD_ROUNDABOUT
        else:
            return STD_NONE

    def _convert_LineString_to_2D(self, coords_3D) -> list:
        """
        Converts LineString Z object types to LineString types
        :param coords_3D: LineString Z list of objects
        :return: list of LineString object
        """
        list_of_2D_lines = []

        for coord_3D in coords_3D:
            line_2D = LineString([xy[0:2] for xy in list(coord_3D.coords)])
            list_of_2D_lines.append(line_2D)

        return list_of_2D_lines

    def _rename_roundabouts(self, std_df: pd.DataFrame) -> pd.DataFrame:
        """
        Identifies and assigns unique roundabout IDs to each roundabout from the OS
        dataset. This ensures each roundabout does not have the same road number (as
        was the case in the original dataset).

        :param std_df: OS Dataset converted to HE format
        :return: Updated he_gdf with roundabout segments sets uniquely named
        """
        FIRST_COORD = "first_coord"
        LAST_COORD = "last_coord"
        INDEX = "INDEX"
        IS_RENAMED = "IS_RENAMED"

        #Temporarily assign  FIRST_COORD, LAST_COORD, and INDEX
        std_df[FIRST_COORD] = std_df[STD_GEOMETRY].apply(lambda x: extract_coord_at_index(x, 0))
        std_df[LAST_COORD] = std_df[STD_GEOMETRY].apply(lambda x: extract_coord_at_index(x, -1))
        std_df.insert(loc=0, column=INDEX, value=std_df.index)

        std_df[IS_RENAMED] = False
        roundabout_df = std_df.loc[std_df[STD_ROAD_TYPE] == STD_ROUNDABOUT]
        roundabout_names = {}
        roundabout_df_size = len(roundabout_df)

        for i in range(roundabout_df_size):
            segment = roundabout_df.iloc[i, :]
            index = segment[INDEX]

            if segment[IS_RENAMED]:
                continue

            roundabout_names = self._set_roundabout_name(roundabout_names, segment[STD_ROAD_NO])
            std_df.at[index, STD_ROAD_NO] = roundabout_names[segment[STD_ROAD_NO]][-1]
            std_df.at[index, IS_RENAMED] = True

            roundabout_queue = Queue()
            roundabout_queue.put(index)

            while not roundabout_queue.empty():
                current_index = roundabout_queue.get()
                current_segment = roundabout_df.loc[current_index, :]
                first_coord = current_segment[FIRST_COORD]
                last_coord = current_segment[LAST_COORD]
                set_of_target_coords = [first_coord, last_coord]

                for target_coords in set_of_target_coords:
                    connected_segments = roundabout_df.loc[(roundabout_df[FIRST_COORD] == target_coords) |
                                                           (roundabout_df[LAST_COORD] == target_coords)]
                    connected_segments = connected_segments[connected_segments[INDEX] != current_index]

                    if len(connected_segments) == 1:
                        if not connected_segments[IS_RENAMED].values[0]:
                            connecting_index = connected_segments[INDEX].values[0]

                            road_ref = std_df.at[connecting_index, STD_ROAD_NO]
                            std_df.at[connecting_index, STD_ROAD_NO] = roundabout_names[road_ref][-1]
                            std_df.at[connecting_index, IS_RENAMED] = True

                            roundabout_queue.put(connecting_index)

                    roundabout_df = std_df.loc[std_df[STD_ROAD_TYPE] == STD_ROUNDABOUT]

        std_df.drop([INDEX, FIRST_COORD, LAST_COORD, IS_RENAMED], axis=1, inplace=True)

        return std_df

    def _set_roundabout_name(self, roundabout_names, road_ref):
        """
        Inserts and updated roundabout names into the dictionary.
        :param roundabout_names: Dictonary which keeps a record of existing roundabout name
        :param road_ref: Road reference to give a unique ID for
        :return: Updated roundabout_names
        """
        if road_ref in roundabout_names:
            split_text = roundabout_names[road_ref][-1].split("_")

            number = str(int(split_text[1]) + 1)
            roundabout_names[road_ref].extend([split_text[0] + "_" + number])
        else:
            roundabout_names[road_ref] = [road_ref + "_" + "0"]

        return roundabout_names
