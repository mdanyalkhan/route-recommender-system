"""
Miscillaneous functions important for processing geospatial dataframes
"""
import os
from math import sqrt
import geopandas as gpd
import pandas as pd
from pyproj import CRS
from pyproj.transformer import Transformer
from shapely import wkt
from RoadGraph.StdColNames import *
from GeoDataFrameAux import extract_coord_at_index, GeoPointDataFrameBuilder, GeoPolyDataFrameBuilder


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
    df = pd.read_csv(in_path)
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[long_name], df[lat_name]))

    gdf.crs = "WGS84"
    gdf.to_crs("EPSG:27700", inplace=True)
    return gdf



