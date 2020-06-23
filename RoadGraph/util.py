"""
Miscillaneous functions important for processing geospatial dataframes
"""
import os
from heapq import heappush, heappop
from itertools import count
from math import sqrt
import networkx as nx
import geopandas as gpd
import pandas as pd


def filter_minor_roads_and_remove_duplicates_from_os_roads(in_path: str, out_path: str):
    """
    Function removes any potential road segments that are potentially duplicated within different shapefiles.
    Function also only considers A Roads and Motorways
    :param in_path: File path containing shapefiles of the os roads data
    :param out_path: File path to save the newly processed shapefiles
    """
    list_of_files = os.listdir(in_path)
    shp_full_paths_in = [in_path + "/" + x for x in list_of_files if ".shp" in x]
    shp_full_paths_out = [out_path + "/" + x for x in list_of_files if ".shp" in x]
    n = len(shp_full_paths_in)
    identifier = []

    for i in range(n):
        curr_gdf = gpd.read_file(shp_full_paths_in[i])
        curr_gdf = curr_gdf.loc[(curr_gdf["class"] == "Motorway") | (curr_gdf["class"] == "A Road")]
        curr_identifiers = curr_gdf.loc[:, "identifier"]
        is_already_in_identifier = curr_identifiers.apply(lambda x: x in identifier)
        index_duplicates = is_already_in_identifier.index[is_already_in_identifier == True].tolist()
        curr_gdf.drop(index=index_duplicates, inplace=True)

        new_identifiers = curr_gdf.loc[:, "identifier"].tolist()
        identifier.extend(new_identifiers)

        curr_gdf.to_file(shp_full_paths_out[i])


def euclidean_distance(coord1: tuple, coord2: tuple):
    """
    Calculates the Euclidean distance between two coordinates
    :param coord1: Tuple of numerical digits
    :param coord2: Second tupe of numerical digits
    :return: Returns the Euclidean distance between two coordinates
    """
    x1, y1 = coord1
    x2, y2 = coord2
    return sqrt(pow(x1 - x2, 2) + pow(y1 - y2, 2))


def shortest_path_gdf(graph: nx.Graph, edges_gdf: gpd.GeoDataFrame, nodes_gdf: gpd.GeoDataFrame,
                      source_node: str, target_node: str):

    get_weight = lambda u, v, data: data.get('attr').get('Length')
    paths = {source_node: [source_node]}
    _, paths = dijkstra(graph, source_node, get_weight, paths=paths)

    shortest_path = paths[target_node]

    n = len(shortest_path) - 1
    shortest_edges_gdf = gpd.GeoDataFrame()
    shortest_nodes_gdf = gpd.GeoDataFrame()

    for i in range(n):
        indices = (graph[shortest_path[i]][shortest_path[i + 1]]).get('attr').get('Road_segment_indices')
        shortest_edges_gdf = pd.concat([shortest_edges_gdf, edges_gdf.loc[indices, :]])
        shortest_nodes_gdf = pd.concat([shortest_nodes_gdf, nodes_gdf.loc[nodes_gdf["node_id"] == shortest_path[i]]])
        shortest_nodes_gdf = pd.concat(
            [shortest_nodes_gdf, nodes_gdf.loc[nodes_gdf["node_id"] == shortest_path[i + 1]]])

    return shortest_edges_gdf, shortest_nodes_gdf


def shortest_path_gdf_all_paths(graph: nx.Graph, edges_gdf: gpd.GeoDataFrame, nodes_gdf: gpd.GeoDataFrame,
                                source_node: str, target_node: str):

    get_weight = lambda u, v, data: data.get('attr').get('Length')
    paths = {source_node: [source_node]}
    _, paths = dijkstra(graph, source_node, get_weight, paths=paths)

    edge_list = []
    node_list = []
    count = 0
    for key in paths.keys():
        shortest_path = paths[key]
        n = len(paths[key]) - 1
        for i in range(n):
            edge_list.extend((graph[shortest_path[i]][shortest_path[i + 1]]).get('attr').get('Road_segment_indices'))

            node_list.extend([shortest_path[i]])
            node_list.extend([shortest_path[i+1]])

    edge_list = list(set(edge_list))
    node_list = list(set(node_list))
    s_edges_gdf = edges_gdf.loc[edge_list, :].copy()
    s_nodes_gdf = nodes_gdf.loc[nodes_gdf['node_id'].isin(node_list)].copy()

    return s_edges_gdf, s_nodes_gdf

def dijkstra(G, source, get_weight, pred=None, paths=None, cutoff=None,
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
