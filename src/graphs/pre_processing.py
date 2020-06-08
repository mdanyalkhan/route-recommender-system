import geopandas as gpd
import pandas as pd
import src.graphs.SRN_column_names as srn_cn
from src.graphs.geo_frame_builder.geo_line_data_frame_builder import *
from shapely.geometry import LineString

def extract_coord(line_object: LineString, index: int):

    list_of_coords = list(line_object.coords)
    return list_of_coords[index]

def is_coord_equal(coord1: tuple, coord2: tuple):
    return (abs(coord1[0]-coord2[0]) < 1.0) and (abs(coord1[1]-coord2[1]) < 1.0)

def filter_to_slip_roads_and_roundabouts(he_data):
    return he_data.loc[
        (he_data[srn_cn.FUNCT_NAME] == "Slip Road") & (he_data[srn_cn.FUNCT_NAME] == "Roundabout")].copy()


def filter_to_main_carriageway(he_data):
    return he_data.loc[he_data[srn_cn.FUNCT_NAME] == "Main Carriageway"].copy()


def link_main_carriageway_segments(carriageway_df):
    """
    Adds extra columns to link each road segment
    :param carriageway_df:
    :return: A GeoDataframe with extra columns that links each road segment
    """
    #Insert index as column
    carriageway_df.insert(loc = 0, column = "INDEX", value = carriageway_df.index)
    #Set up link columns for each road segment (much like block linking)
    carriageway_df["PREV_IND"] = pd.NA
    carriageway_df["NEXT_IND"] = pd.NA

    #Extract first and last coordinates of each road segment
    carriageway_df["FIRST_COORD"] = carriageway_df["geometry"].apply(lambda x: extract_coord(x,0))
    carriageway_df["LAST_COORD"] = carriageway_df["geometry"].apply(lambda x: extract_coord(x,-1))

    road_numbers = carriageway_df.ROA_NUMBER.unique()
    directions = carriageway_df.DIREC_CODE.unique()

    for road_number in road_numbers:
        for direction in directions:
            carriageway = carriageway_df.loc[(carriageway_df["ROA_NUMBER"] == road_number) &
                                             (carriageway_df["DIREC_CODE"] == direction)]

            for index, segment in carriageway.iterrows():

                last_coord = segment.LAST_COORD
                connecting_road = carriageway.index[carriageway["FIRST_COORD"].
                    apply(lambda x: is_coord_equal(x, last_coord))].tolist()

                if (len(connecting_road) == 1):
                    carriageway_df.loc[index,"NEXT_IND"] = connecting_road[0]
                    carriageway_df.loc[connecting_road[0],"PREV_IND"] = index

    carriageway_df.drop(['FIRST_COORD','LAST_COORD'], axis=1, inplace= True)

    return carriageway_df

def merge_road_segments(carriageway_df):
    """
    Merges all linked road segments
    :param carriageway_df: Linked Road segments geodataframe
    :return: gdf: a new dataframe of all roads merged.
    """
    d = {}
    start_segments = carriageway_df.loc[pd.isna(carriageway_df["PREV_IND"])]


    print(len(start_segments))
    for _, segment in start_segments.iterrows():
        coords = list(segment.geometry.coords)
        length = segment.SEC_LENGTH
        current_segment = segment

        while not pd.isna(current_segment.NEXT_IND):
            current_segment = carriageway_df.loc[carriageway_df.INDEX == current_segment.NEXT_IND]
            current_segment = current_segment.iloc[0]
            coords += list(current_segment.geometry.coords)
            length += current_segment.SEC_LENGTH

        road_id = segment.ROA_NUMBER + "_" + segment.DIREC_CODE
        d.setdefault("ROAD_ID",[]).extend([road_id])
        d.setdefault("LENGTH",[]).extend([length])
        d.setdefault("geometry",[]).extend([coords])

    merge_road_df = pd.DataFrame(d)
    merge_road_df["geometry"] = merge_road_df["geometry"].apply(GeoLineDataFrameBuilder()._build_geometry_object)
    merge_road_df['geometry'] = merge_road_df['geometry'].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(merge_road_df, geometry='geometry')
    gdf.crs = {'init': "epsg:27700"}
    return gdf