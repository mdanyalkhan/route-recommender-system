from src.utilities.aux_func import *
from src.utilities.file_directories import FileDirectories as fd
import geopandas as gpd
from RoadNetwork import *
import os

# TODO: Update HERoadsNetworkBuilder to consider what to do in the case where the direction is not disclosed

def connect_he_gdf():
    he_original_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/temp/clipped_roads.shp"
    he_converted_edges_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/temp/edges.shp"
    he_converted_nodes_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/temp/nodes.shp"

    he_gdf = gpd.read_file(he_original_path)
    edges, nodes = HENodesAndEdgesBuilder().build_nodes_and_edges(he_gdf, is_directional=True, node_tag="SRN")

    edges.to_file(he_converted_edges_path)
    nodes.to_file(he_converted_nodes_path)


def convert_OS_original_to_HE_compatible_dataframe():
    os_original_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/temp/OS_roads.shp"
    os_converted_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/temp/OS_roads_converted.shp"
    he_sample_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/temp/clipped_roads.shp"

    os_original_gdf = gpd.read_file(os_original_path)
    he_gdf = gpd.read_file(he_sample_path)
    roads_to_exclude = list(he_gdf[STD_ROAD_NO].unique())
    os_converted_gdf = OSToToStdConverter().convert_to_std_gdf(os_original_gdf)
    os_converted_gdf.to_file(os_converted_path)


def convert_os_original_each_to_HE_compatible_each_df():
    in_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/OS_Data/Original/"
    out_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/OS_Data/Converted/"

    OSToToStdConverter().convert_multiple_to_std_gdfs(in_path, out_path)


def connect_os_gdf():
    os_converted_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/temp/OS_roads_converted.shp"
    os_edges_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/temp/OS_edges.shp"
    os_nodes_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/temp/OS_nodes.shp"
    os_converted_gdf = gpd.read_file(os_converted_path)
    os_edges_gdf, os_nodes_gdf = OSNodesAndEdgesBuilder().build_nodes_and_edges(os_converted_gdf, is_directional=False,
                                                                                node_tag="SJCLIP")

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

    combined_edges_gdf, combined_nodes_gdf = NodesAndEdgesMerger(). \
        merge_two_network_gdfs(he_edges_gdf, he_nodes_gdf, os_edges_gdf, os_nodes_gdf)

    combined_edges_gdf.to_file(combined_edges_path)
    combined_nodes_gdf.to_file(combined_nodes_path)


def connect_all_os_dataframe_seperately():
    in_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/OS_Data/Converted"
    out_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/OS_Data/Connected"
    build_multiple_networks_from_os(in_path, out_path)


def build_multiple_networks_from_os(in_path, out_path):
    list_of_files = os.listdir(in_path)
    shp_tags = [x.split("_RoadLink.shp")[0] for x in list_of_files if ".shp" in x]
    shp_full_paths_in = [in_path + "/" + x for x in list_of_files if ".shp" in x]
    shp_full_paths_out = [out_path + "/" + x.split("_RoadLink.shp")[0] for x in list_of_files if ".shp" in x]

    n = len(shp_full_paths_in)
    builder = OSNodesAndEdgesBuilder()
    for i in range(n):
        print("iteration: " + str(i + 1) + " out of " + str(n + 1))
        os_gdf = gpd.read_file(shp_full_paths_in[i])
        edge_gdf, node_gdf = builder.build_nodes_and_edges(os_gdf, is_directional=False, node_tag=shp_tags[i])
        if not os.path.exists(shp_full_paths_out[i]):
            os.makedirs(shp_full_paths_out[i])
        edge_gdf.to_file(shp_full_paths_out[i] + "/" + shp_tags[i] + "_edges.shp")
        node_gdf.to_file(shp_full_paths_out[i] + "/" + shp_tags[i] + "_nodes.shp")


def merge_multiple_network_dataframes(base_path, aux_path, out_path):
    pass


if __name__ == "__main__":
    base_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/test/base"
    aux_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/test/aux"
    RoadNetworkBuilder(HENodesAndEdgesBuilder(), OSNodesAndEdgesBuilder()).build_network(base_path, aux_path,
                                                                                         is_base_conversion_required=False,
                                                                                         is_aux_conversion_required=True)
