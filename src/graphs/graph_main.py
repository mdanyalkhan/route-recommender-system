from GeoDataFrameAux import extract_list_of_coords_from_geom_object
from RoadGraph.util import *
import RoadGraph
import src.utilities.file_directories as fd
from src.utilities.aux_func import parent_directory_at_level, loadNetworkResults
from scipy.spatial import cKDTree
import numpy as np


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


if __name__ == "__main__":
    edges = gpd.read_file(fd.LbbDirectories.edges_path)
    nodes = gpd.read_file(fd.LbbDirectories.nodes_path)
    net = loadNetworkResults(fd.LbbDirectories.netx_path_criteria3)
    key_sites = gpd.read_file(fd.LbbDirectories.key_sites_path)
    node_out_path = f"{parent_directory_at_level(__file__, 4)}/Operational_Data/lbb/vulnerability/HW_SW/nodes"
    grid_out_path = f"{parent_directory_at_level(__file__, 4)}/Operational_Data/lbb/vulnerability/HW_SW/grids"
    road_graph = RoadGraph.StdRoadGraph(net, nodes, edges)
    vuln_analyser = RoadGraph.VulnerabilityAnalyser(road_graph)

    # vuln_analyser.srn_vulnerability_two_sites_nodes(key_sites, 'location_n', source_site='HEATHROW WORLDWIDE DC',
    #                                                 target_site='SOUTH WEST DC', cutoff=10, out_path=node_out_path)
    vuln_analyser.srn_vulnerability_two_sites_grid(key_sites, 'location_n', source_site='HEATHROW WORLDWIDE DC',
                                                    target_site='SOUTH WEST DC', dimension_km= 2.0,
                                                   cutoff=10, out_path=grid_out_path)
