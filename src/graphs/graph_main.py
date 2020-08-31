import RoadGraph
from RoadGraph.analysis.closureanalysis import *
from src.utilities.aux_func import parent_directory_at_level, loadNetworkResults
import matplotlib.pyplot as plt


def generate_route_graph_example():
    route_net_path = f"{parent_directory_at_level(__file__, 4)}/Operational_Data/lbb/reduced/HW_SW/road_graph/roadGraph.pickle"
    key_sites = f"{parent_directory_at_level(__file__, 4)}/Operational_Data/rm_sites/rm_locations.shp"
    route_graph = loadNetworkResults(route_net_path)
    route_graph.set_road_closure('A_683', 'A_684')
    route_graph.set_road_closure('A_1081', 'A_1080')
    route_graph.set_road_closure('F_1510', 'F_1507')
    _, _, s_edges, s_nodes = route_graph.shortest_path_between_key_sites('HEATHROW WORLDWIDE DC', 'SOUTH WEST DC',
                                                                         gpd.read_file(key_sites), 'location_n',
                                                                         get_gdfs=True)
    s_edges.to_file(
        f"{parent_directory_at_level(__file__, 4)}/Operational_Data/lbb/reduced/HW_SW/shortest_path_sample/edges.shp")
    s_nodes.to_file(
        f"{parent_directory_at_level(__file__, 4)}/Operational_Data/lbb/reduced/HW_SW/shortest_path_sample/nodes.shp")

def generate_resilience_index_plot(fname_a: str,fname_b: str):

    with open(fname_a) as target_a:
        ri_a = target_a.readlines()

    with open(fname_b) as target_b:
        ri_b = target_b.readlines()

    ri_a_float = [float(val) for val in ri_a]
    ri_b_float = [float(val) for val in ri_b]

    fig, ax = plt.subplots()
    plt.plot(range(len(ri_a_float)), ri_a_float, ri_b_float)
    plt.title("Resilience Index Against Number of Closures", fontname='Charter')
    plt.ylabel("Resilience Index", fontname='Charter')
    plt.xlabel("Number of Closures", fontname='Charter')
    plt.legend(['Node-Based', 'Grid-Based'], prop={"family": "Charter"})
    for tick in ax.get_xticklabels():
        tick.set_fontname('Charter')

    for tick in ax.get_yticklabels():
        tick.set_fontname('Charter')


    plt.show()


if __name__ == "__main__":

    path = parent_directory_at_level(__file__, 4) + '/Operational_Data/testing/out/converted/toy_test_original.shp'
    out_path = parent_directory_at_level(__file__, 4) + '/Operational_Data/testing/out/converted'
    RoadGraph.StdNodesEdgesGdfBuilder().build_nodes_and_edges_gdf_from_path(path, out_path=out_path)
    # generate_resilience_index_plot(f"{parent_directory_at_level(__file__, 4)}"
    #                                f"/Operational_Data/lbb/vulnerability/HW_SW_temp/nodes/resilience_values.txt",
    #                                f"{parent_directory_at_level(__file__, 4)}"
    #                                f"/Operational_Data/lbb/vulnerability/HW_SW_temp/grids/resilience_values.txt"
    #                                )
    # edges = gpd.read_file(fd.LbbDirectories.edges_path)
    # nodes = gpd.read_file(fd.LbbDirectories.nodes_path)
    # net = loadNetworkResults(fd.LbbDirectories.netx_path_criteria3)
    # key_sites = gpd.read_file(fd.LbbDirectories.key_sites_path)
    # node_out_path = f"{parent_directory_at_level(__file__, 4)}/Operational_Data/lbb/vulnerability/HW_SW_temp/nodes"
    # grid_out_path = f"{parent_directory_at_level(__file__, 4)}/Operational_Data/lbb/vulnerability/HW_SW_temp/grids"
    # road_graph = RoadGraph.StdRoadGraph(net, nodes, edges)
    # # closure_path = f"{parent_directory_at_level(__file__, 4)}/Operational_Data/lbb/closures/200720"
    # # _, res_dict = journey_time_impact_closure_shp_path(road_graph,key_sites, closure_path)
    # # output_res_dict_shortest_path_as_shp(road_graph, res_dict, closure_path, no_of_paths=10)
    # # output_res_dict_to_csv(res_dict, closure_path)
    #
    # vuln_analyser = RoadGraph.VulnerabilityAnalyser(road_graph)
    #
    # # vuln_analyser.srn_vulnerability_two_sites_nodes(key_sites, 'location_n', source_site='HEATHROW WORLDWIDE DC',
    # #                                                 target_site='SOUTH WEST DC', cutoff=10, out_path=node_out_path)
    # vuln_analyser.srn_vulnerability_two_sites_grid(key_sites, 'location_n', source_site='HEATHROW WORLDWIDE DC',
    #                                                 target_site='SOUTH WEST DC', dimension_km= 2.0,
    #                                                cutoff=10, out_path=grid_out_path)
