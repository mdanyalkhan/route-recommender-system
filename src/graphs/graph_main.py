import collections
from operator import itemgetter
import networkx as nx
from src.utilities.aux_func import *
from RoadGraph.util import *
import RoadGraph
import os
import matplotlib.pyplot as plt

if __name__ == "__main__":
    edges_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/plcr/out/final/edges.shp"
    nodes_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/plcr/out/final/nodes.shp"
    net_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/plcr/out/netx/roadGraph.pickle"
    key_sites_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/rm_sites/rm_locations.shp"
    out_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/vulnerability"

    net = loadNetworkResults(net_path)
    print(net.number_of_edges())
    print(net.number_of_nodes())
    # road_graph = RoadGraph.StdRoadGraph(net, gpd.read_file(nodes_path), gpd.read_file(edges_path))
    # print(road_graph.average_degree())
    # road_graph.degree_distribution_plot()
