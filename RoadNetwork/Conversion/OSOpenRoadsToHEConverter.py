from RoadNetwork.Utilities.ColumnNames import *
import geopandas as gpd
import pandas as pd
import numpy as np

column_names_null = [HE_SECT_LABEL, HE_LOCATION, HE_START_DATE, HE_END_DATE, HE_AREA_NAME,
                     HE_DIRECTION, HE_PERM_LANES, HE_ENVIRONMENT, HE_AUTHORITY]


class OSOpenRoadsToHERoadsConverter(object):

    def convert_to_HE_dataframe(self, os_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:

        # Select features that are only motorways and A roads
        sel_gdf = os_gdf.loc[(os_gdf[OS_CLASS] == OS_MOTORWAY) | (os_gdf[OS_CLASS] == OS_A_ROAD)]

        # OPTIONALLY select features that are not a duplicate of roads already in SRN

        # Set up a geodataframe with with columns that will be NULL values (such as AREA_NAME)
        null_list = [pd.NA] * len(sel_gdf)
        list_of_null_lists = [null_list] * len(column_names_null)
        he_df = pd.DataFrame(np.array(list_of_null_lists).transpose(), columns=column_names_null)

        # Insert Class Name
        class_names = sel_gdf[OS_CLASS].apply(self._insert_class_name)
        he_df.insert(0, HE_CLASS_NAME, class_names)

        # Insert Road Number
        he_df.insert(1, HE_ROAD_NO, sel_gdf[OS_ROAD_NO])

        # Insert funct_name
        funct_names = sel_gdf[OS_FUNCT_NAME].apply(self._insert_funct_name)
        he_df.insert(6, HE_FUNCT_NAME, funct_names)
        
        # Insert carriageway builder
        # Insert reference
        print(he_df)
        print(he_df.columns.tolist())
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
