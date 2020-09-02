"""
Miscillaneous functions important for processing geospatial dataframes
"""
import os
from math import sqrt
import geopandas as gpd
import pandas as pd
from shapely.geometry import MultiLineString
import RoadGraph.constants.StdColNames as cn
import RoadGraph.constants.StdKeyWords as kw


def filter_minor_roads_and_remove_duplicates_from_os_roads(in_path: str, out_path: str):
    """
    Function removes any potential road segments that are potentially duplicated within different shapefiles.
    Function also only considers A Roads and Motorways
    :param in_path: File path containing shapefiles of the os roads data
    :param out_path: File path to save the newly processed shapefiles
    """
    list_of_files = os.listdir(in_path)
    shp_full_paths_in = [in_path + "/" + x for x in list_of_files if ".shp" in x]
    shp_full_paths_out = [out_path + "/" + x for x in list_of_files if ".shp" in x]
    n = len(shp_full_paths_in)
    identifier = []

    for i in range(n):
        curr_gdf = gpd.read_file(shp_full_paths_in[i])
        curr_gdf = curr_gdf.loc[(curr_gdf["class"] == "Motorway") | (curr_gdf["class"] == "A Road")]
        curr_identifiers = curr_gdf.loc[:, "identifier"]
        is_already_in_identifier = curr_identifiers.apply(lambda x: x in identifier)
        index_duplicates = is_already_in_identifier.index[is_already_in_identifier == True].tolist()
        curr_gdf.drop(index=index_duplicates, inplace=True)

        new_identifiers = curr_gdf.loc[:, "identifier"].tolist()
        identifier.extend(new_identifiers)

        curr_gdf.to_file(shp_full_paths_out[i])


def euclidean_distance(coord1: tuple, coord2: tuple):
    """
    Calculates the Euclidean distance between two coordinates
    :param coord1: Tuple of numerical digits
    :param coord2: Second tupe of numerical digits
    :return: Returns the Euclidean distance between two coordinates
    """
    x1, y1 = coord1
    x2, y2 = coord2
    return sqrt(pow(x1 - x2, 2) + pow(y1 - y2, 2))


def convert_csv_to_shpfile(in_path: str, lat_name: str, long_name: str) -> gpd.GeoDataFrame:
    """
    Converts a royal mail csv file into a shapefile projected onto the British National Grid
    :param in_path:
    :return:
    """
    df = pd.read_csv(in_path, parse_dates=['Event_Dttm'])
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[long_name], df[lat_name]))

    gdf.crs = "WGS84"
    gdf.to_crs("EPSG:27700", inplace=True)
    return gdf


def create_file_path(file_path: str) -> str:
    """
    Either returns or creates and returns a directory corresponding to file_path
    :param file_path: Name of file path that needs to be created in the computer's directory tree
    :return: the file path following confirmation that it exists
    """
    if not os.path.exists(file_path):
        os.makedirs(file_path)

    return file_path


def set_speed_limits_to_criteria2(edges_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Sets the speed limit of each road segment based on the form of way of the road
    :param form_of_way: Effectively the road type
    :return: Speed in int
    """

    edges_gdf.loc[edges_gdf[cn.STD_FORMOFWAY].isin(kw.STD_DUAL_CARRIAGEWAY_LIST), cn.STD_SPEED] = kw.STD_SPEED_DC
    edges_gdf.loc[edges_gdf[cn.STD_FORMOFWAY] == kw.STD_SINGLE_CARRIAGEWAY, cn.STD_SPEED] = kw.STD_SPEED_SC
    edges_gdf.loc[(~edges_gdf[cn.STD_FORMOFWAY].isin(kw.STD_DUAL_CARRIAGEWAY_LIST)) &
                  (edges_gdf[cn.STD_FORMOFWAY] != kw.STD_SINGLE_CARRIAGEWAY), cn.STD_SPEED] = kw.STD_SPEED_DEFAULT

    return edges_gdf

def extract_list_of_coords_from_geom_object(geom_object) -> [(int, int)]:
    """
    Returns a list version of the coordinates stored in line_object
    :param geom_object: Either a LineString or MultiLineString object
    :return: list of coordinates of line_object
    """
    list_of_coords = []
    if type(geom_object) is MultiLineString:
        list_of_lines = list(geom_object)
        for line in list_of_lines:
            list_of_coords.extend(list(line.coords))
    else:
        list_of_coords = list(geom_object.coords)
    return list_of_coords

def extract_coord_at_index(geom_object, index: int) -> (float, float):
    """
    Returns the coordinates from a LineString or MultiLineString object
    :param geom_object: LineString or MultilineString object
    :param index: index of the line_object to extract coordinates from
    :return coordinates in a tuple from line_object at index
    """

    list_of_coords = extract_list_of_coords_from_geom_object(geom_object)
    return list_of_coords[index]