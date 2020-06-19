from GeoDataFrameAux import *
from RoadNetwork.Utilities.ColumnNames import *
from RoadNetwork.Conversion.ToStdConverter import *
from shapely.geometry import LineString
import geopandas as gpd
import pandas as pd
import numpy as np
import os
from queue import Queue

column_names_null = [STD_SECT_LABEL, STD_LOCATION, STD_START_DATE, STD_END_DATE, STD_AREA_NAME,
                     STD_DIRECTION, STD_PERM_LANES, STD_ENVIRONMENT, STD_AUTHORITY]


class OSToToStdConverter(ToStdConverter):

    def convert_multiple_and_merge_to_single_std_gdf(self, folder_path: str, roads_to_exclude=None) -> gpd.GeoDataFrame:
        """
        Converts all OS geodataframes in a directory to a combined standard geodataframe
        :param folder_path: directory path containing the OS geodataframes
        :param roads_to_exclude: Any roads to exclude from from the geodataframe
        :return: A standardised geodataframe containing information from all the OS geodataframe
        """
        list_of_files = os.listdir(folder_path)
        list_of_shp = [folder_path + "/" + x for x in list_of_files if ".shp" in x]
        merged_df = None
        i = 0
        n = len(list_of_shp)
        for shp_path in list_of_shp:
            print("iteration: " + str(i+1) + " out of " + str(n+1))
            os_gdf = gpd.read_file(shp_path)
            converted_df = self.convert_to_std_df(os_gdf, roads_to_exclude)
            if merged_df is None:
                merged_df = converted_df
            else:
                merged_df = pd.concat([merged_df, converted_df], ignore_index=True)
            i += 1

        # Insert geometry
        merged_gdf = gpd.GeoDataFrame(merged_df, geometry=GEOMETRY)
        merged_gdf.crs = {'init': 'epsg:27700'}

        return merged_gdf

    def convert_multiple_to_std_gdfs(self, in_path: str, out_path: str, roads_to_exclude=None) -> None:
        """
        Converts multiple shp geospatial roads dataframes into the standard GeoDataFrame used for this project.
        The results are saved in the out_path directory
        :param in_path: File path containing all shp files that are to be converted
        :param out_path: File path in which the converted standard dataframes are to be saved
        :param roads_to_exclude: Any roads to be excluded (should be in list form)
        """
        list_of_files = os.listdir(in_path)
        shp_full_paths_in = [in_path + "/" + x for x in list_of_files if ".shp" in x]
        shp_full_paths_out = [out_path + "/" + x for x in list_of_files if ".shp" in x]

        n = len(shp_full_paths_in)
        for i in range(n):
            print("iteration: " + str(i+1) + " out of " + str(n+1))
            os_gdf = gpd.read_file(shp_full_paths_in[i])
            converted_df = self.convert_to_std_gdf(os_gdf, roads_to_exclude)
            converted_df.to_file(shp_full_paths_out[i])

    def convert_to_std_gdf(self, gdf: gpd.GeoDataFrame, roads_to_exclude = None) -> gpd.GeoDataFrame:
        """
        Converts a single os geodataframe to an equivalent HE geodataframe
        :param gdf:
        :param roads_to_exclude:
        :return: HE geodataframe converted from the OS geodataframe
        """
        converted_df = self.convert_to_std_df(gdf, roads_to_exclude)

        # Insert geometry
        converted_gdf = gpd.GeoDataFrame(converted_df, geometry=GEOMETRY)
        converted_gdf.crs = {'init': 'epsg:27700'}

        return converted_gdf

    def convert_to_std_df(self, os_gdf: gpd.GeoDataFrame, roads_to_exclude=None) -> pd.DataFrame:
        """
        Converts the OS geodataframe to a dataframe compatible to HE's dataframe
        :param os_gdf: OS_open roads geodataframe
        :param roads_to_exclude: any road numbers to exclude, usually in list form
        :return: OS open roads equivalent data converted to HE-style dataframe
        """
        if roads_to_exclude is None:
            roads_to_exclude = []

        pd.options.mode.chained_assignment = None

        # Select features that are only motorways and A roads
        sel_gdf = os_gdf.loc[(os_gdf[OS_CLASS] == OS_MOTORWAY) | (os_gdf[OS_CLASS] == OS_A_ROAD)].copy()
        sel_gdf.reset_index(drop=True, inplace=True)


        # # OPTIONALLY select features that are not a duplicate of roads already in SRN
        if roads_to_exclude:
            sel_gdf["is_in_list"] = sel_gdf[OS_ROAD_NO].apply(lambda x: x in roads_to_exclude)
            sel_gdf = sel_gdf.loc[sel_gdf["is_in_list"] == False]
            sel_gdf.drop("is_in_list", axis=1, inplace=True)

        # Set up a geodataframe with with columns that will be NULL values (such as AREA_NAME)
        null_list = [pd.NA] * len(sel_gdf)
        list_of_null_lists = [null_list] * len(column_names_null)
        he_df = pd.DataFrame(np.array(list_of_null_lists).transpose(), columns=column_names_null)

        # Insert Class Name
        class_names = sel_gdf[OS_CLASS].apply(self._insert_class_name)
        he_df.insert(0, STD_CLASS_NAME, class_names.values)

        # Insert Road Number
        he_df.insert(1, STD_ROAD_NO, sel_gdf[OS_ROAD_NO].values)

        # Insert funct_name
        funct_names = sel_gdf[OS_FUNCT_NAME].apply(self._insert_funct_name)
        he_df.insert(6, STD_FUNCT_NAME, funct_names.values)

        # Insert length
        he_df.insert(6, STD_LENGTH, sel_gdf[OS_LENGTH].values)

        # Insert carriageway type
        he_df.insert(he_df.columns.tolist().index(STD_ENVIRONMENT), STD_CARRIAGEWAY_TYPE,
                     sel_gdf[OS_FUNCT_NAME].values)

        # Insert reference
        he_df.insert(len(he_df.columns.tolist()), STD_REFERENCE,
                     sel_gdf[OS_ID].values)

        #Insert geometry
        geometry_2D = self._convert_LineString_to_2D(sel_gdf[GEOMETRY].values)
        he_df.insert(len(he_df.columns.tolist()), GEOMETRY, geometry_2D)

        #Rename roundabouts to unique roundabout IDs
        he_df = self._rename_roundabouts(he_df)

        pd.options.mode.chained_assignment = 'warn'

        return he_df

    def _insert_class_name(self, class_name: str) -> str:
        """
        Returns the key class name value corresponding to the HE roads data
       :param class_name: class value stored in OS dataframe
       :return: "M" or "A" class name values
       """
        if class_name == OS_MOTORWAY:
            return "M"
        elif class_name == OS_A_ROAD:
            return "A"
        else:
            return STD_NONE

    def _insert_funct_name(self, funct_name: str) -> str:
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

    def _rename_roundabouts(self, he_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Identifies and assigns unique roundabout IDs to each roundabout from the OS
        dataset. This ensures each roundabout does not have the same road number (as
        was the case in the original dataset).

        :param he_gdf: OS Dataset converted to HE format
        :return: Updated he_gdf with roundabout segments sets uniquely named
        """
        #Temporarily assign  FIRST_COORD, LAST_COORD, and INDEX
        he_gdf[FIRST_COORD] = he_gdf[GEOMETRY].apply(lambda x: extract_coord_at_index(x, 0))
        he_gdf[LAST_COORD] = he_gdf[GEOMETRY].apply(lambda x: extract_coord_at_index(x, -1))
        he_gdf.insert(loc=0, column=INDEX, value=he_gdf.index)

        he_gdf["IS_RENAMED"] = False
        roundabout_df = he_gdf.loc[he_gdf[STD_FUNCT_NAME] == STD_ROUNDABOUT]
        roundabout_names = {}
        roundabout_df_size = len(roundabout_df)

        for i in range(roundabout_df_size):
            segment = roundabout_df.iloc[i, :]
            index = segment.INDEX

            if segment.IS_RENAMED:
                continue

            roundabout_names = self._set_roundabout_name(roundabout_names, segment.ROA_NUMBER)
            he_gdf.at[index, STD_ROAD_NO] = roundabout_names[segment.ROA_NUMBER][-1]
            he_gdf.at[index, "IS_RENAMED"] = True

            roundabout_queue = Queue()
            roundabout_queue.put(index)

            while not roundabout_queue.empty():
                current_index = roundabout_queue.get()
                current_segment = roundabout_df.loc[current_index, :]
                first_coord = current_segment.FIRST_COORD
                last_coord = current_segment.LAST_COORD
                set_of_target_coords = [first_coord, last_coord]

                for target_coords in set_of_target_coords:
                    connected_segments = roundabout_df.loc[(roundabout_df[FIRST_COORD] == target_coords) |
                                                           (roundabout_df[LAST_COORD] == target_coords)]
                    connected_segments = connected_segments[connected_segments[INDEX] != current_index]

                    if len(connected_segments) == 1:
                        if not connected_segments["IS_RENAMED"].values[0]:
                            connecting_index = connected_segments[INDEX].values[0]

                            road_ref = he_gdf.at[connecting_index, STD_ROAD_NO]
                            he_gdf.at[connecting_index, STD_ROAD_NO] = roundabout_names[road_ref][-1]
                            he_gdf.at[connecting_index, "IS_RENAMED"] = True

                            roundabout_queue.put(connecting_index)

                    roundabout_df = he_gdf.loc[he_gdf[STD_FUNCT_NAME] == STD_ROUNDABOUT]

        he_gdf.drop([INDEX, FIRST_COORD, LAST_COORD, "IS_RENAMED"], axis=1, inplace=True)

        return he_gdf

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