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


def convert_rm_sites_to_shpfile(in_path: str) -> gpd.GeoDataFrame:
    """
    Converts a royal mail csv file into a shapefile projected onto the British National Grid
    :param in_path:
    :return:
    """
    df = pd.read_csv(in_path)
    df['lat_lon'] = df[['lat', 'lon']].values.tolist()
    df['geometry'] = df['lat_lon'].apply(project_to_british_national_grid)
    df.drop('lat_lon', axis=1, inplace=True)
    df['geometry'] = df['geometry'].apply(GeoPointDataFrameBuilder()._build_geometry_object)
    df['geometry'] = df['geometry'].apply(wkt.loads)

    gdf = gpd.GeoDataFrame(df, geometry='geometry')
    gdf.crs = {'init': 'epsg:27700'}

    return gdf


def project_to_british_national_grid(coords: list):
    """
    Projects a list of coordinates into british national grid
    :param coords: Latitude and longitude in a list
    :return: Tuple of coordinates converted to british national grid
    """
    crs_4326 = CRS("WGS84")
    crs_proj = CRS("EPSG:27700")

    transformer = Transformer.from_crs(crs_4326, crs_proj)
    return transformer.transform(coords[0], coords[1])

def bounds_of_shpfile(shpfile: gpd.GeoDataFrame):

    bounds = list(shpfile.total_bounds)
    minx, miny, maxx, maxy = bounds[0], bounds[1], bounds[2], bounds[3]
    coordinates = [(minx, miny), (minx, maxy), (maxx, maxy), (maxx, miny)]
    return GeoPolyDataFrameBuilder().build_geo_frame(coordinates, 'epsg:27700')

def grid_for_shpfile(shpfile: gpd.GeoDataFrame, size_km: float):

    bounds = list(shpfile.total_bounds)
    minx, miny, maxx, maxy = bounds[0], bounds[1], bounds[2], bounds[3]
    size_m = size_km * 1000
    y = miny
    gdf = gpd.GeoDataFrame()

    while y < maxy:
        x = minx
        while x < maxx:
            coordinates = [(x, y), (x, y + size_m), (x + size_m, y + size_m), (x + size_m, y)]
            polygon = GeoPolyDataFrameBuilder().build_geo_frame(coordinates, 'epsg:27700')
            gdf = pd.concat([gdf, polygon])
            x += size_m
        y += size_m

    return gdf