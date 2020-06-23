from heapq import heappush, heappop
from itertools import count

import geopandas as gpd
import pandas as pd
from RoadGraph.StdColNames import *
from RoadGraph import euclidean_distance


class StdRoadGraph:

    def __init__(self, netx_graph, nodes_gdf, edges_gdf):
        self.net = netx_graph
        self.nodes = nodes_gdf
        self.edges = edges_gdf

    def shortest_path_between_sites(self, source_coord: tuple, target_coord: tuple):
        nodes_gdf = self.nodes

        source_distances = nodes_gdf['coordinates'].apply(lambda x: euclidean_distance(x, source_coord))
        min_index = source_distances.index[source_distances == source_distances.min()].values[0]
        nearest_source_node = nodes_gdf.loc[min_index][STD_NODE_ID]

        target_distances = nodes_gdf['coordinates'].apply(lambda x: euclidean_distance(x, target_coord))
        min_index = source_distances.index[target_distances == target_distances.min()].values[0]
        nearest_target_node = nodes_gdf.loc[min_index][STD_NODE_ID]

        return self.shortest_path_betwen_nodes(nearest_source_node, nearest_target_node)

    def shortest_path_betwen_nodes(self, source_node: str, target_node: str):

        get_weight = lambda u, v, data: data.get('attr').get('Length')
        graph = self.net
        edges_gdf = self.edges
        nodes_gdf = self.nodes
        paths = {source_node: [source_node]}

        _, paths = self.dijkstra(graph, source_node, get_weight, paths=paths)

        shortest_path = paths[target_node]

        n = len(shortest_path) - 1
        shortest_edges_gdf = gpd.GeoDataFrame()
        shortest_nodes_gdf = gpd.GeoDataFrame()

        for i in range(n):
            indices = (graph[shortest_path[i]][shortest_path[i + 1]]).get('attr').get('Road_segment_indices')
            shortest_edges_gdf = pd.concat([shortest_edges_gdf, edges_gdf.loc[indices, :]])
            shortest_nodes_gdf = pd.concat(
                [shortest_nodes_gdf, nodes_gdf.loc[nodes_gdf["node_id"] == shortest_path[i]]])
            shortest_nodes_gdf = pd.concat(
                [shortest_nodes_gdf, nodes_gdf.loc[nodes_gdf["node_id"] == shortest_path[i + 1]]])

        return shortest_edges_gdf, shortest_nodes_gdf

    def dijkstra(self, G, source, get_weight, pred=None, paths=None, cutoff=None,
                 target=None):
        """Implementation of Dijkstra's algorithm
        Original Authors:
       Aric Hagberg <hagberg@lanl.gov>
       Dan Schult <dschult@colgate.edu>
       Pieter Swart <swart@lanl.gov>

       Adapted for the roads network

        Parameters
        ----------
        G : NetworkX graph

        source : node label
           Starting node for path

        get_weight: function
            Function for getting edge weight

        pred: list, optional(default=None)
            List of predecessors of a node

        paths: dict, optional (default=None)
            Path from the source to a target node.

        target : node label, optional
           Ending node for path

        cutoff : integer or float, optional
           Depth to stop the search. Only paths of length <= cutoff are returned.

        Returns
        -------
        distance,path : dictionaries
           Returns a tuple of two dictionaries keyed by node.
           The first dictionary stores distance from the source.
           The second stores the path from the source to that node.

        pred,distance : dictionaries
           Returns two dictionaries representing a list of predecessors
           of a node and the distance to each node.

        distance : dictionary
           Dictionary of shortest lengths keyed by target.
        """
        G_succ = G.succ if G.is_directed() else G.adj

        push = heappush
        pop = heappop
        dist = {}  # dictionary of final distances
        seen = {source: 0}
        c = count()
        fringe = []  # use heapq with (distance,label) tuples
        push(fringe, (0, next(c), source))
        while fringe:
            (d, _, v) = pop(fringe)
            if v in dist:
                continue  # already searched this node.
            dist[v] = d
            if v == target:
                break

            for u, e in G_succ[v].items():
                cost = get_weight(v, u, e)
                if cost is None:
                    continue
                vu_dist = dist[v] + get_weight(v, u, e)
                if cutoff is not None:
                    if vu_dist > cutoff:
                        continue
                if u in dist:
                    if vu_dist < dist[u]:
                        raise ValueError('Contradictory paths found:',
                                         'negative weights?')
                elif u not in seen or vu_dist < seen[u]:
                    seen[u] = vu_dist
                    push(fringe, (vu_dist, next(c), u))
                    if paths is not None:
                        paths[u] = paths[v] + [u]
                    if pred is not None:
                        pred[u] = [v]
                elif vu_dist == seen[u]:
                    if pred is not None:
                        pred[u].append(v)

        if paths is not None:
            return (dist, paths)
        if pred is not None:
            return (pred, dist)
        return dist
