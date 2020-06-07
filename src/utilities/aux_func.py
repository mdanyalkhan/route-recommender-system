from os.path import *
import pandas as pd
import geopandas as gpd
from shapely import wkt


def parent_directory_at_level(current_path: str, level: int):
    """
    Returns file path at the specified level.
    :param current_path: Name of the current file path
    :param level: (int) the level in which you want to return the parent path.
    :return: parent_path (str) the string file path at the specified level.
    """
    parent_path: str = current_path
    for i in range(0, level):
        parent_path = dirname(parent_path)

    return parent_path


def clip(layer: gpd.geodataframe, mask: gpd.geodataframe):
    """
    Clips layer to mask
    :param layer: geodataframe of shapefile
    :param mask: geodataframe of mask
    :return: copy of layer within boundary of mask
    """
    min_x = mask.bounds.minx.values[0]
    min_y = mask.bounds.miny.values[0]
    max_x = mask.bounds.maxx.values[0]
    max_y = mask.bounds.maxy.values[0]

    in_boundary = layer.loc[(layer.bounds['minx'] >= min_x) &
                            (layer.bounds["miny"] >= min_y) &
                            (layer.bounds["maxx"] <= max_x) &
                            (layer.bounds["maxy"] <= max_y)]

    return in_boundary.copy()

