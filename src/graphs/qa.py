import RoadGraph
import src.utilities.file_directories as fd
import src.graphs.shortest_path_analysis as sp
from src.utilities.aux_func import loadNetworkResults
import geopandas as gpd


def shortest_path_analysis_grouped(directories: fd.ParentDirectories, criteria=3):
    if criteria == 1:
        netx_path = directories.netx_path_criteria1
        main_out_path = directories.out_path_criteria1
    elif criteria == 2:
        netx_path = directories.netx_path_criteria2
        main_out_path = directories.out_path_criteria2
    else:
        netx_path = directories.netx_path_criteria3
        main_out_path = directories.out_path_criteria3

    net = loadNetworkResults(netx_path)
    edges = gpd.read_file(directories.edges_path)
    nodes = gpd.read_file(directories.nodes_path)
    key_sites = gpd.read_file(directories.key_sites_path)
    roadGraph = RoadGraph.StdRoadGraph(net, nodes, edges)

    RoadGraph.util.create_file_path(main_out_path)

    isotrack_list = list(directories.isotrack_dict.keys())

    for isotrack_prefix in isotrack_list:
        out_path = RoadGraph.util.create_file_path(f"{main_out_path}/{isotrack_prefix}")
        sp.shortest_path_analysis(roadGraph, key_sites, 'location_n', directories.isotrack_dict[isotrack_prefix], 0,
                                  criteria_type=1, out_path=out_path)


if __name__ == '__main__':
    directories = fd.plcrDirectories()
    shortest_path_analysis_grouped(directories, criteria=1)
    shortest_path_analysis_grouped(directories, criteria=2)
    shortest_path_analysis_grouped(directories, criteria=3)
