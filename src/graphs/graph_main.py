from src.utilities.aux_func import *
from src.utilities.file_directories import FileDirectories as fd
import geopandas as gpd
from RoadNetwork import *
import os


def connect_he_gdf():
    he_original_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/temp/clipped_roads.shp"
    he_converted_edges_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/temp/edges.shp"
    he_converted_nodes_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/temp/nodes.shp"

    he_gdf = gpd.read_file(he_original_path)
    edges, nodes = HERoadsNetworkBuilder(node_tag="SRN").build_road_network_gdf(he_gdf)

    edges.to_file(he_converted_edges_path)
    nodes.to_file(he_converted_nodes_path)


def convert_OS_original_to_HE_compatible_dataframe():
    os_original_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/temp/OS_roads.shp"
    os_converted_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/temp/OS_roads_converted.shp"
    he_sample_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/temp/clipped_roads.shp"

    os_original_gdf = gpd.read_file(os_original_path)
    he_gdf = gpd.read_file(he_sample_path)
    roads_to_exclude = list(he_gdf[HE_ROAD_NO].unique())
    os_converted_gdf = OSOpenRoadsToHERoadsConverter().convert_to_HE_geoDataframe(os_original_gdf)
    os_converted_gdf.to_file(os_converted_path)


def connect_os_gdf():
    os_converted_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/temp/OS_roads_converted.shp"
    os_edges_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/temp/OS_edges.shp"
    os_nodes_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/temp/OS_nodes.shp"
    os_converted_gdf = gpd.read_file(os_converted_path)
    os_edges_gdf, os_nodes_gdf = OSRoadsNetworkBuilder(node_tag="SJCLIP").build_road_network_gdf(os_converted_gdf)

    os_edges_gdf.to_file(os_edges_path)
    os_nodes_gdf.to_file(os_nodes_path)

def merge_HE_and_OS_gdf():
    he_connected_edges_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/temp/edges.shp"
    he_connected_nodes_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/temp/nodes.shp"
    os_edges_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/temp/OS_edges.shp"
    os_nodes_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/temp/OS_nodes.shp"

    combined_edges_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/temp/combined_edges.shp"
    combined_nodes_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/temp/combined_nodes.shp"

    he_edges_gdf = gpd.read_file(he_connected_edges_path)
    he_nodes_gdf = gpd.read_file(he_connected_nodes_path)
    os_edges_gdf = gpd.read_file(os_edges_path)
    os_nodes_gdf = gpd.read_file(os_nodes_path)

    combined_edges_gdf, combined_nodes_gdf = MergeNetworkDataFrames().\
        merge_two_network_dataframes(he_edges_gdf, he_nodes_gdf, os_edges_gdf, os_nodes_gdf)

    combined_edges_gdf.to_file(combined_edges_path)
    combined_nodes_gdf.to_file(combined_nodes_path)


if __name__ == "__main__":
    connect_he_gdf()