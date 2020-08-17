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
    net_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/plcr/out/netx/roadGraph_criteria1.pickle"

    edges = gpd.read_file(edges_path)
    nodes = gpd.read_file(nodes_path)


    net = RoadGraph.StdRoadGraphBuilder().create_graph(nodes, edges, weight_type='distance')

    with open(net_path, 'wb') as target:
        pickle.dump(net, target)