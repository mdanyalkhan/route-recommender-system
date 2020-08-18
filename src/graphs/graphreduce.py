import geopandas as gpd
import RoadGraph as rg
from RoadGraph.graphreduce.routesgraph import RoutesGraph
from RoadGraph.graphreduce.roadassignment import RoadAssignment
import pickle
from src.utilities.aux_func import loadNetworkResults
from src.utilities import file_directories as fd
from src.utilities.aux_func import parent_directory_at_level

def generate_routes_graph(road_graph: rg.StdRoadGraph, isotrack_df: gpd.GeoDataFrame, out_path: str):

    RoadAssignment().assign_nearest_nodes(isotrack_df, road_graph.edges, road_graph.nodes)
    route_graph = RoutesGraph().generate_stdRoadGraph_from_isotrack(isotrack_df, road_graph)

    out_path = rg.create_file_path(f"{out_path}/road_graph")
    route_graph.edges.to_file(f"{out_path}/edges.shp")
    route_graph.nodes.to_file(f"{out_path}/nodes.shp")

    with open(f"{out_path}/roadGraph.pickle", 'wb') as target:
        pickle.dump(route_graph, target)

    return route_graph

def find_and_save_k_paths(road_graph: rg.StdRoadGraph, key_sites: gpd.GeoDataFrame, key_site_col_name: str,
                          source: str, target: str, k: int, out_path: str):
    out_path = rg.create_file_path(f"{out_path}/shortest_paths")

    i = 1
    for path in road_graph.k_shortest_paths_from_key_sites(key_sites, key_site_col_name, source, target, k):
        cur_path = rg.create_file_path(f"{out_path}/shortest_path_{i}")
        edges, nodes = road_graph.convert_path_to_gdfs(path)
        edges.to_file(f"{cur_path}/edges.shp")
        nodes.to_file(f"{cur_path}/nodes.shp")
        i += 1


if __name__ == '__main__':
    net = loadNetworkResults(fd.LbbDirectories.netx_path_criteria3)
    nodes_gdf  = gpd.read_file(fd.LbbDirectories.nodes_path)
    edges_gdf = gpd.read_file(fd.LbbDirectories.edges_path)
    hw_sw_df = gpd.read_file(f"{fd.LbbDirectories.out_path_criteria3}/HW_SW/isotrack_all_paths.shp")
    road_graph = rg.StdRoadGraph(net, nodes_gdf, edges_gdf)
    out_path = rg.create_file_path(f"{parent_directory_at_level(__file__, 4)}/Operational_Data/lbb/reduced/HW_SW")
    key_sites = gpd.read_file(fd.LbbDirectories.key_sites_path)
    key_site_col_name = 'location_n'
    hw = 'HEATHROW WORLDWIDE DC'
    sw = 'SOUTH WEST DC'
    k = 5

    hw_sw_graph = generate_routes_graph(road_graph, hw_sw_df, out_path)
    find_and_save_k_paths(hw_sw_graph, key_sites, key_site_col_name, hw, sw, k, out_path)

