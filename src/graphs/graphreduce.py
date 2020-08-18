from collections import deque

import pandas as pd
import geopandas as gpd
from scipy.spatial import cKDTree
import pickle
import RoadGraph as rg
import numpy as np
import networkx as nx
import RoadGraph.graphreduce.roadassignment as ra
import RoadGraph.graphreduce.routesgraph as routesgraph
from src.utilities.aux_func import loadNetworkResults

edges_path = rg.parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/final/edges.shp"
nodes_path = rg.parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/final/nodes.shp"
isotrack_path = f'{rg.parent_directory_at_level(__file__, 4)}/Operational_Data/lbb/out/compare_to_telemetry/' \
                f'HW_SW/isotrack_all_paths.shp'
net_path = rg.parent_directory_at_level(__file__, 4) + '/Operational_Data/lbb/out/netx/roadGraph.pickle'

isotrack_edge_path = f'{rg.parent_directory_at_level(__file__, 4)}/Operational_Data/lbb/reduced/HW_SW/isotrack_edges.shp'
isotrack_node_path = f'{rg.parent_directory_at_level(__file__, 4)}/Operational_Data/lbb/reduced/HW_SW/isotrack_nodes.shp'
isotrack_net_path = f'{rg.parent_directory_at_level(__file__, 4)}/Operational_Data/lbb/reduced/HW_SW/isotrack_net.pickle'
key_sites_path = rg.parent_directory_at_level(__file__, 4) + "/Operational_Data/rm_sites/rm_locations.shp"


if __name__ == '__main__':
    net = loadNetworkResults(net_path)
    nodes_gdf  = gpd.read_file(nodes_path)
    edges_gdf = gpd.read_file(edges_path)
    road_graph = rg.StdRoadGraph(net, nodes_gdf, edges_gdf)

    # isotrack_data = gpd.read_file(isotrack_path)
    # ra.RoadAssignment().assign_nearest_nodes(isotrack_data, edges_gdf, nodes_gdf)

    # with open(f"{rg.parent_directory_at_level(__file__, 4)}/Operational_Data/temp/isotrack_gdf_4.pickle", 'wb') as target:
    #     pickle.dump(isotrack_data, target)
    fname = f"{rg.parent_directory_at_level(__file__, 4)}/Operational_Data/temp/isotrack_gdf_4.pickle"
    isotrack_gdf = loadNetworkResults(fname)


    out_path = f"{rg.parent_directory_at_level(__file__, 4)}/Operational_Data/temp"
    heathrow_worldwide = 'HEATHROW WORLDWIDE'
    south_west = 'SOUTH WEST DC'
    routesgraph.RoutesGraph().generate_stdRoadGraph_from_isotrack(isotrack_gdf, road_graph, out_path=out_path)
    # route_graph = rg.StdRoadGraph(loadNetworkResults(f"{out_path}/route_graph.pickle"),
    #                               gpd.read_file(f"{out_path}/nodes.shp"),gpd.read_file(f"{out_path}/edges.shp"))
    #
    # i = 1
    # for path in route_graph.k_shortest_paths(south_west, heathrow_worldwide, 50):
    #     print(i)
    #     edges, nodes = route_graph.convert_path_to_gdfs(path)
    #     edges.to_file(f"{out_path}/routes/edges_{i}.shp")
    #     i += 1

