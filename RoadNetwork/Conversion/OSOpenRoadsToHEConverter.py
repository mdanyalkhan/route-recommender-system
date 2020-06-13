from RoadNetwork.Utilities.ColumnNames import *
import geopandas as gpd
import pandas as pd
import numpy as np
import os

column_names_null = [HE_SECT_LABEL, HE_LOCATION, HE_START_DATE, HE_END_DATE, HE_AREA_NAME,
                     HE_DIRECTION, HE_PERM_LANES, HE_ENVIRONMENT, HE_AUTHORITY]


class OSOpenRoadsToHERoadsConverter(object):

    def convert_and_merge_to_HE_geoDataframe(self, folder_path: str, roads_to_exclude=None) -> gpd.GeoDataFrame:
        """
        Converts all OS geodataframes in a directory to a combined HE geodataframe
        :param folder_path: directory path containing the OS geodataframes
        :param roads_to_exclude: Any roads to exclude from from the geodataframe
        :return: HE geodataframe containing information from all the OS geodataframe
        """
        list_of_files = os.listdir(folder_path)
        list_of_shp = [folder_path + "/" + x for x in list_of_files if ".shp" in x]
        merged_df = None
        i = 0
        n = len(list_of_shp)
        for shp_path in list_of_shp:
            print("iteration: " + str(i) + " out of " + str(n))
            os_gdf = gpd.read_file(shp_path)
            converted_df = self.convert_to_HE_dataframe(os_gdf, roads_to_exclude)
            if merged_df is None:
                merged_df = converted_df
            else:
                merged_df = pd.concat([merged_df, converted_df], ignore_index=True)
            i += 1

        # Insert geometry
        merged_gdf = gpd.GeoDataFrame(merged_df, geometry=GEOMETRY)
        merged_gdf.crs = {'init': 'epsg:27700'}

        return merged_gdf

    def convert_to_HE_geoDataframe(self, os_gdf: gpd.GeoDataFrame, roads_to_exclude = None) -> pd.DataFrame:
        """
        Converts a single os geodataframe to an equivalent HE geodataframe
        :param os_gdf:
        :param roads_to_exclude:
        :return: HE geodataframe converted from the OS geodataframe
        """
        converted_df = self.convert_to_HE_dataframe(os_gdf, roads_to_exclude)

        # Insert geometry
        converted_gdf = gpd.GeoDataFrame(converted_df, geometry=GEOMETRY)
        converted_gdf.crs = {'init': 'epsg:27700'}

        return converted_df

    def convert_to_HE_dataframe(self, os_gdf: gpd.GeoDataFrame, roads_to_exclude=None) -> pd.DataFrame:
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
        sel_gdf = os_gdf.loc[(os_gdf[OS_CLASS] == OS_MOTORWAY) | (os_gdf[OS_CLASS] == OS_A_ROAD)]

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
        he_df.insert(0, HE_CLASS_NAME, class_names.values)

        # Insert Road Number
        he_df.insert(1, HE_ROAD_NO, sel_gdf[OS_ROAD_NO].values)

        # Insert funct_name
        funct_names = sel_gdf[OS_FUNCT_NAME].apply(self._insert_funct_name)
        he_df.insert(6, HE_FUNCT_NAME, funct_names.values)

        # Insert length
        he_df.insert(6, HE_LENGTH, sel_gdf[OS_LENGTH].values)

        # Insert carriageway type
        he_df.insert(he_df.columns.tolist().index(HE_ENVIRONMENT), HE_CARRIAGEWAY_TYPE,
                     sel_gdf[OS_FUNCT_NAME].values)

        # Insert reference
        he_df.insert(len(he_df.columns.tolist()), HE_REFERENCE,
                     sel_gdf[OS_ID].values)

        #Insert geometry
        he_df.insert(len(he_df.columns.tolist()), GEOMETRY, sel_gdf[GEOMETRY].values)

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
            return HE_NONE

    def _insert_funct_name(self, funct_name: str) -> str:
        """
        Returns HE key funct name
        :param funct_name: OS funct name
        :return: Either HE main carriageway, slip road, or roundabout, otherwise None
        """
        if funct_name in OS_MAIN_CARRIAGEWAY_LIST:
            return HE_MAIN_CARRIAGEWAY
        elif funct_name == OS_SLIP_ROAD:
            return HE_SLIP_ROAD
        elif funct_name == OS_ROUNDABOUT:
            return HE_ROUNDABOUT
        else:
            return HE_NONE