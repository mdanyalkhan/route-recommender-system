from src.utilities.aux_func import *
from RoadGraph.util import *
import RoadGraph
import os
import networkx as nx

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


def build_road_graph_lbb():
    in_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/original"
    target_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb"
    RoadGraph.StdRoadGraphBuilder().build_road_graph(in_path, target_path, is_conversion_required=True)


def shortest_path_london_southampton():
    in_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/netx/roadGraph.pickle"
    gdf_path_edges = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/final/edges.shp"
    gdf_path_nodes = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/final/nodes.shp"
    rm_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/rm_sites/new_rm_lbb.shp"
    edges_gdf = gpd.read_file(gdf_path_edges)
    nodes_gdf = gpd.read_file(gdf_path_nodes)
    net = loadNetworkResults(in_path)
    key_sites = gpd.read_file(rm_path)
    roadGraph = RoadGraph.StdRoadGraph(net, nodes_gdf, edges_gdf, key_sites=key_sites)
    s_edges, s_nodes = roadGraph.shortest_path_between_key_sites('LONDON CENTRAL MC', 'SOUTHAMPTON MC')
    s_edges.to_file(
        parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/shortest_paths/London_Southampton_e.shp")
    s_nodes.to_file(
        parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/shortest_paths/London_Southampton_n.shp")


if __name__ == "__main__":

    edges_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/plcr/out/final/edges.shp"
    nodes_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/plcr/out/final/nodes.shp"
    out = parent_directory_at_level(__file__, 4) + "/Operational_Data/plcr/out/netx/roadGraph.pickle"
    edges_gdf = gpd.read_file(edges_path)
    nodes_gdf = gpd.read_file(nodes_path)

    builder = RoadGraph.StdRoadGraphBuilder()

    net = builder.create_graph(nodes_gdf, edges_gdf)

    with open(out, 'wb') as target:
        pickle.dump(net, target)









