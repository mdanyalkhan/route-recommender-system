import collections
from heapq import heappush, heappop
from itertools import count, islice
import numpy as np
import geopandas as gpd
import pandas as pd
from RoadGraph.util import euclidean_distance, extract_coord_at_index
from RoadGraph.constants.StdColNames import *
from RoadGraph.constants.StdKeyWords import *
import matplotlib.pyplot as plt
import networkx as nx


class StdRoadGraph:

    def __init__(self, netx_graph, nodes_gdf, edges_gdf):
        self.net = netx_graph
        self.nodes = nodes_gdf
        self.edges = edges_gdf

    def shortest_path_between_key_sites(self, source_site: str, target_site: str, key_sites_gdf: gpd.GeoDataFrame,
                                        key_site_col_name: str, get_gdfs=False) \
            -> (gpd.GeoDataFrame, gpd.GeoDataFrame, float):
        """
        Decorator function that calls on shortest_path_between_coords based on specified key sites.
        :param source_site: Name of first Royal Mail Sites
        :param target_site: Name of target Royal Mail Sites
        :param key_sites_gdf: Database containing list of key sites and its corresponding coordinates
        :param key_site_col_name: The name of the column in key_sites_gdf that contains the name of the sites
        :param get_gdfs: If set to true, this will convert the shortest path into its equivalent nodes and edges
        GeoDataFrame
        :return: Will either return the shortest path (list)  and shortest distance (float), or shortest path (list),
        shortest distance(float), the edges and nodes GeoDataFrames depending on whether get_gdfs is set to True
        or not.
        """
        source_coord, target_coord = self._get_coordinates(key_site_col_name, key_sites_gdf, source_site, target_site)

        return self.shortest_path_between_coords(source_coord, target_coord, get_gdfs)

    def _get_coordinates(self, key_site_col_name: str, key_sites_gdf: gpd.GeoDataFrame,
                         source_site: str, target_site: str) -> tuple:
        """
        Extracts the coordinates of the sites
        :param key_site_col_name: name of column that stores sites
        :param key_sites_gdf: name of geo data frame
        :param source_site: name of source site
        :param target_site: name of target site
        :return: source and target coordinates
        """
        geom_obj = key_sites_gdf.loc[key_sites_gdf[key_site_col_name] == source_site, STD_GEOMETRY].values[0]
        source_coord = extract_coord_at_index(geom_obj, 0)
        geom_obj = key_sites_gdf.loc[key_sites_gdf[key_site_col_name] == target_site, STD_GEOMETRY].values[0]
        target_coord = extract_coord_at_index(geom_obj, 0)
        return source_coord, target_coord

    def shortest_path_between_coords(self, source_coord: tuple, target_coord: tuple, get_gdfs=False) \
            -> (gpd.GeoDataFrame, gpd.GeoDataFrame, float):
        """
        Decorator function that calls on shortest_path_between_nodes based on specified coordinates.
        :param source_coord: Tuple coordinates of the source coordinates
        :param target_coord: Tuple coordinates of the target coordinates
        :param get_gdfs: If set to true, this will convert the shortest path into its equivalent nodes and edges
        GeoDataFrame
        :return: Will either return the shortest path (list)  and shortest distance (float), or shortest path (list),
        shortest distance(float), the edges and nodes GeoDataFrames depending on whether get_gdfs is set to True
        or not.
        """
        nearest_source_node, nearest_target_node = self._get_nearest_node(source_coord, target_coord)
        return self.shortest_path_between_nodes(nearest_source_node, nearest_target_node, get_gdfs)

    def _get_nearest_node(self, source_coord: tuple, target_coord: tuple) -> tuple:
        """
        Gets the nearest nodes based on source and target coordinates
        :param source_coord: x-y coordinates of source
        :param target_coord: x-y coordinates of target
        :return: Tuple of nearest nodes to source and target
        """
        nodes_gdf = self.nodes
        COORDINATES = "coordinates"
        nodes_gdf[COORDINATES] = nodes_gdf[STD_GEOMETRY].apply(lambda x: extract_coord_at_index(x, 0))
        source_distances = nodes_gdf[COORDINATES].apply(lambda x: euclidean_distance(x, source_coord))
        min_index = source_distances.index[source_distances == source_distances.min()].values[0]
        nearest_source_node = nodes_gdf.loc[min_index][STD_NODE_ID]
        target_distances = nodes_gdf[COORDINATES].apply(lambda x: euclidean_distance(x, target_coord))
        min_index = source_distances.index[target_distances == target_distances.min()].values[0]
        nearest_target_node = nodes_gdf.loc[min_index][STD_NODE_ID]
        nodes_gdf.drop([COORDINATES], axis=1, inplace=True)

        return nearest_source_node, nearest_target_node

    def set_road_closure(self, from_node: str, to_node: str):
        """
        Sets weight of edge between nodes as infinite
        :param from_node: Name of first node
        :param to_node: Name of second node
        """
        self.net[from_node][to_node][STD_Nx_WEIGHT] = np.inf
        self.net[to_node][from_node][STD_Nx_WEIGHT] = np.inf

    def remove_road_closure(self, from_node: str, to_node: str):
        """
        Set weights of edge back to original time
        :param from_node: Name of first node
        :param to_node: Name of second node
        """

        self.net[from_node][to_node][STD_Nx_WEIGHT] = self.net[from_node][to_node] \
            .get(STD_Nx_ATTR).get(STD_Nx_TIME)
        self.net[to_node][from_node][STD_Nx_WEIGHT] = self.net[from_node][to_node] \
            .get(STD_Nx_ATTR).get(STD_Nx_TIME)

    def shortest_path_between_nodes(self, source_node: str, target_node: str, get_gdfs=False) \
            -> (list, float, gpd.GeoDataFrame, gpd.GeoDataFrame):
        """
        Finds the shortest path between two pair of nodes.
        :param source_node: Name of source node to start the shortest path algorithm from
        :param target_node: Name of Target node
        :param get_gdfs: If set to true, this will convert the shortest path into its equivalent nodes and edges
        GeoDataFrame
        :return: Will either return the shortest path (list)  and shortest distance (float), or shortest path (list),
        shortest distance(float), the edges and nodes GeoDataFrames depending on whether get_gdfs is set to True
        or not.
        """
        dist, paths = self.dijkstra(source=source_node, target=target_node)
        shortest_path = paths[target_node]
        shortest_dist = dist[target_node]

        if not get_gdfs:
            return shortest_path, shortest_dist

        shortest_edges_gdf, shortest_nodes_gdf = self.convert_path_to_gdfs(shortest_path)

        return shortest_path, shortest_dist, shortest_edges_gdf, shortest_nodes_gdf

    def convert_path_to_gdfs(self, shortest_path: list) -> tuple:
        """
        Builds the corresponding nodes and edges gdfs based on the list of nodes within the shortest_path list.

        :param shortest_path: List of nodes forming the shortest path
        :return: Tuple of nodes and edges gdf corresponding to the shortest path.
        """
        n = len(shortest_path) - 1
        graph = self.net
        edges_gdf = self.edges
        nodes_gdf = self.nodes
        shortest_edges_gdf = gpd.GeoDataFrame()
        shortest_nodes_gdf = gpd.GeoDataFrame()

        for i in range(n):
            indices = (graph[shortest_path[i]][shortest_path[i + 1]]).get(STD_Nx_ATTR).get(STD_Nx_ROAD_IND)
            shortest_edges_gdf = pd.concat([shortest_edges_gdf, edges_gdf.loc[edges_gdf[STD_INDEX].isin(indices), :]])
            shortest_nodes_gdf = pd.concat(
                [shortest_nodes_gdf, nodes_gdf.loc[nodes_gdf[STD_NODE_ID] == shortest_path[i]]])
            shortest_nodes_gdf = pd.concat(
                [shortest_nodes_gdf, nodes_gdf.loc[nodes_gdf[STD_NODE_ID] == shortest_path[i + 1]]])

        shortest_edges_gdf = self._add_roundabout_line_segments(shortest_nodes_gdf, shortest_edges_gdf)
        return shortest_edges_gdf, shortest_nodes_gdf

    def _add_roundabout_line_segments(self, shortest_nodes_gdf: gpd.GeoDataFrame, shortest_edges_gdf: gpd.GeoDataFrame):
        """
        Extracts all of the roundabout line segments corresponding to all roundabout nodes used in the shortest path
        geo-Dataframes.
        :param shortest_nodes_gdf: Geo-Dataframe of nodes forming the shortest path.
        :param shortest_edges_gdf: Geo-Dataframe of edges forming the shortest path.
        :return: Updated shortest path gdf with roundabout line segments included.
        """
        roundabout_nodes = shortest_nodes_gdf.loc[shortest_nodes_gdf[STD_N_TYPE] == STD_N_ROUNDABOUT]
        roundabout_edges = self.edges.loc[self.edges[STD_ROAD_TYPE] == STD_ROUNDABOUT]

        for _, roundabout_node in roundabout_nodes.iterrows():
            node_id = roundabout_node[STD_NODE_ID]
            sel_roundabout_segments = roundabout_edges.loc[roundabout_edges[STD_FROM_NODE] == node_id]
            shortest_edges_gdf = pd.concat([shortest_edges_gdf, sel_roundabout_segments])

        return shortest_edges_gdf

    def k_shortest_paths_from_key_sites(self, key_sites_gdf: gpd.GeoDataFrame, key_site_col_name: str,
                                        source: str, target: str, k: int):
        """
        Returns k list of nodes that form the shortest path from source to target
        :param key_sites_gdf: Key sites geo data frame
        :param key_site_col_name: Name of column containing key sites
        :param source: Name of source site
        :param target: Name of target site
        :param k: Number of shortest paths to extract
        :return: a generator: k list of nodes forming the k shortest paths
        """
        source_coord, target_coord = self._get_coordinates(key_site_col_name, key_sites_gdf, source, target)
        source_node, target_node = self._get_nearest_node(source_coord, target_coord)

        return self.k_shortest_paths_from_nodes(source_node, target_node, k)

    def k_shortest_paths_from_nodes(self, source_node: str, target_node: str, k: int) -> list:
        """
        Generator function that returns the k shortest paths from source to target.

        :param source_node: Name of the source node
        :param target_node: Name of the target node
        :param k: Number of paths to extract
        :return: List of k-shortest paths.
        """
        return list(islice(nx.shortest_simple_paths(self.net, source_node, target_node, weight=STD_Nx_WEIGHT), k))

    def dijkstra(self, source, pred=None, cutoff=None, target=None):
        """Implementation of Dijkstra's algorithm
        Original Authors:
       Aric Hagberg <hagberg@lanl.gov>
       Dan Schult <dschult@colgate.edu>
       Pieter Swart <swart@lanl.gov>

       Adapted for the roads network

        Parameters
        ----------
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
        G = self.net
        G_succ = G.succ if G.is_directed() else G.adj
        get_weight = lambda u, v, data: data.get(STD_Nx_WEIGHT)
        paths = {source: [source]}

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

    def average_degree(self, type: str = 'out') -> float:
        """
        Returns the average degree of the network
        :param type: Whether 'in' or 'out', defaults to 'out'
        :return: average degree of network
        """
        if type is 'out':
            nodes_degrees = self.net.out_degree()
        else:
            nodes_degrees = self.net.in_degree()

        degrees = [node_degree[1] for node_degree in nodes_degrees]

        return sum(degrees) / len(degrees)

    def degree_distribution_plot(self):
        """
        Generates a plot of the degree distribution of the network.
        """
        net = self.net

        degree_sequence = sorted([d for n, d in net.out_degree()], reverse=True)  # degree sequence
        degreeCount = collections.Counter(degree_sequence)
        deg, cnt = zip(*degreeCount.items())
        sum_cnt = sum(cnt)
        rel_cnt = [i / sum_cnt for i in cnt]
        fig, ax = plt.subplots()
        plt.bar(deg, rel_cnt, width=0.80, color='b')

        plt.title("Degree Distribution", fontname='Charter')
        plt.ylabel("Relative Frequency $P(k_i)$", fontname='Charter')
        plt.xlabel("Degree $k_i$", fontname='Charter')
        ax.set_xticks([d + 0.4 for d in deg])
        ax.set_xticklabels(deg)

        for tick in ax.get_xticklabels():
            tick.set_fontname('Charter')

        for tick in ax.get_yticklabels():
            tick.set_fontname('Charter')

        plt.show()
