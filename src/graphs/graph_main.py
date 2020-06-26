from src.utilities.aux_func import *
from src.utilities.file_directories import FileDirectories as fd
import geopandas as gpd
from RoadNetwork import *
from RoadGraph.util import *
import RoadGraph
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


def remove_duplicates_from_os():
    in_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/test_os/original"
    out_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/test_os"
    filter_minor_roads_and_remove_duplicates_from_os_roads(in_path, out_path)


def build_std_gdf_from_os_gdf():
    SD_in_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/test_os/SD_RoadLink.shp"
    SD_out_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/test_os/SD_STD_RoadLink.shp"
    SJ_in_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/test_os/SJ_RoadLink.shp"
    SJ_out_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/test_os/SJ_STD_RoadLink.shp"

    RoadGraph.OSToStdGdfConverter().convert_to_std_gdf_from_path(SD_in_path, SD_out_path)
    RoadGraph.OSToStdGdfConverter().convert_to_std_gdf_from_path(SJ_in_path, SJ_out_path)


def build_nodes_edges_from_std_gdf():
    SD_in_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/test_os/SD_STD_RoadLink.shp"
    SD_out_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/test_os/SD"
    SJ_in_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/test_os/SJ_STD_RoadLink.shp"
    SJ_out_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/test_os/SJ"

    RoadGraph.StdNodesEdgesGdfBuilder().build_nodes_and_edges_gdf_from_path(SD_in_path, SD_out_path, 'SD')
    RoadGraph.StdNodesEdgesGdfBuilder().build_nodes_and_edges_gdf_from_path(SJ_in_path, SJ_out_path, 'SJ')


def connect_both_node_edges_std_gdfs():
    SD_in_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/test_os/SD"
    SJ_in_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/test_os/SJ"
    out_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/test_os/final"
    RoadGraph.StdNodesEdgesGdfConnector().connect_two_nodeEdges_std_gdfs_from_paths(SD_in_path, SJ_in_path, out_path)


def loadNetworkResults(file_name):
    with open(file_name, 'rb') as target:
        network_results = pickle.load(target)
    return network_results


def count_no_of_line_features(in_path):
    list_of_files = os.listdir(in_path)
    shp_full_paths_in = [in_path + "/" + x for x in list_of_files if "_RoadLink.shp" in x]

    no = 0
    x = 0
    for shp in shp_full_paths_in:
        print(x)
        x += 1
        gdf = gpd.read_file(shp)
        no += len(gdf)
    print(no)


if __name__ == "__main__":

    # in_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/original"
    # target_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb"
    #
    # RoadGraph.StdRoadGraphBuilder().build_road_graph(in_path, target_path, is_conversion_required=True)
    in_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/netx/roadGraph.pickle"
    gdf_path_edges = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/final/edges.shp"
    gdf_path_nodes = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/final/nodes.shp"

    edges_gdf = gpd.read_file(gdf_path_edges)
    nodes_gdf = gpd.read_file(gdf_path_nodes)

    net = loadNetworkResults(in_path)
    roadGraph = RoadGraph.StdRoadGraph(net, nodes_gdf, edges_gdf)

    source_node = 'F_3085'
    target_node = 'D_146'
    #
    source_coord = (429686, 193786)
    target_coord = (348161, 276721)


    roadGraph.set_road_closure('G_1399', 'G_1401')
    s_edges_gdf, s_nodes_gdf = roadGraph.shortest_path_betwen_nodes(source_node, target_node)

    s_edges_gdf.to_file(parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/London_Bristol_e.shp")
    s_nodes_gdf.to_file(
        parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/shortest_paths/London_Bristol_n.shp")
    #
    # in_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/converted"
    # out_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out"
    # #
    # in_path = RoadGraph.StdRoadGraphBuilder()._build_edges_nodes_gdfs(in_path, out_path)
    # curr_path = RoadGraph.StdRoadGraphBuilder()._connect_edges_and_nodes_gdfs(in_path, out_path)
    # edges_gdf = gpd.read_file(curr_path + "/edges.shp")
    # nodes_gdf = gpd.read_file(curr_path + "/nodes.shp")
    #
    # net = RoadGraph.StdRoadGraphBuilder().create_graph(nodes_gdf, edges_gdf)
    # target_path = RoadGraph.StdRoadGraphBuilder()._create_file_path(out_path + "/netx")
    # target_file = target_path + "/roadGraph.pickle"
    #
    # with open(target_file, 'wb') as target:
    #     pickle.dump(net, target)

    # in_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/converted/SP_RoadLink.shp"
    # out_nodes_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/temp/sp_nodes.shp"
    # out_edges_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/temp/sp_edges.shp"
    # gdf = gpd.read_file(in_path)
    # edges, nodes = RoadGraph.StdNodesEdgesGdfBuilder().build_nodes_and_edges_gdf(gdf, node_tag='G')
    # edges.to_file(out_edges_path)
    # nodes.to_file(out_nodes_path)

    # in_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/original/SP_RoadLink.shp"
    # out_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/temp/sp_converted.shp"
    # gdf = gpd.read_file(in_path)
    # sp_converted = RoadGraph.OSToStdGdfConverter().convert_to_std_gdf(gdf)
    # sp_converted.to_file(out_path)
