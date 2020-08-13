from collections import deque

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


def generate_point_line_dict(edges_gdf: gpd.GeoDataFrame):

    points = edges_gdf['geometry'].apply(rg.extract_list_of_coords_from_geom_object).tolist()
    std_index = edges_gdf[rg.STD_INDEX].tolist()

    d = {}

    for i in range(len(points)):
        cur_line = std_index[i]
        line_of_points = points[i]
        for point in line_of_points:
            d[point] = cur_line

    return d


def find_edges_corresponding_to_isotrack_data(graph_point_map: dict, edges_gdf: gpd.GeoDataFrame,
                                              isotrack_data: gpd.GeoDataFrame):
    points = list(graph_point_map.keys())
    points_x = [point[0] for point in points]
    points_y = [point[1] for point in points]

    shortest_path_coords = np.dstack([points_x, points_y])[0]
    tree = cKDTree(shortest_path_coords)

    isotrack_coords = []
    for _, point in isotrack_data.iterrows():
        isotrack_coords.extend(rg.extract_list_of_coords_from_geom_object(point['geometry']))
    isotrack_x = [coord[0] for coord in isotrack_coords]
    isotrack_y = [coord[1] for coord in isotrack_coords]
    isotrack_coords = np.dstack([isotrack_x, isotrack_y])[0]

    _, indices = tree.query(isotrack_coords, k=1)
    indices = list(set(indices))

    std_index = []
    for index in indices:
        sel_point = points[index]
        std_index.append(graph_point_map[sel_point])

    sel_edges = edges_gdf.loc[edges_gdf[rg.STD_INDEX].isin(std_index)].copy()

    return sel_edges


def reduce_nodes_edges_dataframes_to_isotrack(edges: gpd.GeoDataFrame,
                                              sel_edges: gpd.GeoDataFrame):
    edges['visited'] = False
    node_ids = []
    edge_ind = []
    sel_edges = sel_edges.loc[sel_edges[rg.STD_ROAD_TYPE] != rg.STD_ROUNDABOUT]

    for i in range(len(sel_edges)):
        index = sel_edges.iloc[i][rg.STD_INDEX]
        if not edges.loc[edges[rg.STD_INDEX] == index, 'visited'].values[0]:
            que = deque()
            que.append(index)
            while que:
                sel_ind = que.popleft()
                edges.at[edges[rg.STD_INDEX] == sel_ind, 'visited'] = True
                if edges.loc[edges[rg.STD_INDEX] == sel_ind, rg.STD_FROM_NODE].values[0] != rg.STD_NONE:
                    node_ids.append(edges.loc[edges[rg.STD_INDEX] == sel_ind, rg.STD_FROM_NODE].values[0])
                else:
                    prev_ind = int(edges.loc[edges[rg.STD_INDEX] == sel_ind, rg.STD_PREV_IND].values[0])
                    if not edges.loc[edges[rg.STD_INDEX] == prev_ind, 'visited'].values[0]:
                        que.append(prev_ind)

                if edges.loc[edges[rg.STD_INDEX] == sel_ind, rg.STD_TO_NODE].values[0] != rg.STD_NONE:
                    node_ids.append(edges.loc[edges[rg.STD_INDEX] == sel_ind, rg.STD_TO_NODE].values[0])
                else:
                    next_ind = int(edges.loc[edges[rg.STD_INDEX] == sel_ind, rg.STD_NEXT_IND].values[0])
                    if not edges.loc[edges[rg.STD_INDEX] == next_ind, 'visited'].values[0]:
                        que.append(next_ind)
                edge_ind.append(sel_ind)

    edge_ind = list(set(edge_ind))
    edge_sel = edges.loc[edges[rg.STD_INDEX].isin(edge_ind)]
    edge_sel.to_file(f"{rg.parent_directory_at_level(__file__, 4)}/Operational_Data/lbb/reduced/HW_SW/isotrack_edges_raw.shp")
    node_ids = list(set(node_ids))
    edges.drop(['visited'], axis=1, inplace=True)

    return node_ids


def find_remaining_nodes(road_graph: rg.StdRoadGraph, node_ids, source, target):
    all_nodes = []

    visited = [False for _ in range(len(node_ids))]
    for i in range(len(node_ids)):
        if not visited[i]:
            _, path_to_source = road_graph.dijkstra(source=node_ids[i], target=source)
            _, path_to_target = road_graph.dijkstra(source=node_ids[i], target=target)
            all_nodes += path_to_source[source] + path_to_target[target]

            for j in range(i + 1, len(node_ids)):
                if node_ids[j] in all_nodes:
                    visited[j] = True

    all_nodes = list(set(all_nodes))
    return all_nodes


def find_connecting_edges(road_graph: rg.StdRoadGraph, node_ids):
    all_nodes = []

    for i in range(len(node_ids) - 1):
        print(f"iteration: {i}")
        source = node_ids[i]
        visited = [False for _ in range(len(node_ids))]

        for j in range(i + 1, len(node_ids)):
            if not visited[j]:
                target = node_ids[j]
                _, paths = road_graph.dijkstra(source, target=target)
                all_nodes += paths[target]
                visited[j] = True

                for k in range(j + 1, len(node_ids)):
                    if node_ids[k] in paths:
                        all_nodes += paths[node_ids[k]]
                        visited[k] = True

    all_nodes = list(set(all_nodes))
    return all_nodes


def extract_edge_shp_from_node_set(road_graph: rg.StdRoadGraph, node_ids):
    edge_ind = []

    node_queue = [node_id for node_id in node_ids]
    while node_queue:
        node_id = node_queue.pop()
        for neighbour, _ in road_graph.net.succ[node_id].items():
            if neighbour in node_queue:
                edge_ind += road_graph.net[node_id][neighbour][rg.STD_Nx_ATTR][rg.STD_Nx_ROAD_IND]

    isotrack_edges = road_graph.edges.loc[road_graph.edges[rg.STD_INDEX].isin(edge_ind)].copy()
    isotrack_nodes = road_graph.nodes.loc[road_graph.nodes[rg.STD_NODE_ID].isin(node_ids)].copy()

    return isotrack_edges, isotrack_nodes


if __name__ == '__main__':
    net = loadNetworkResults(net_path)
    nodes_gdf  = gpd.read_file(nodes_path)
    edges_gdf = gpd.read_file(edges_path)
    road_graph = rg.StdRoadGraph(net, nodes_gdf, edges_gdf)

    # isotrack_data = gpd.read_file(isotrack_path)
    # ra.RoadAssignment().assign_node_pairs(isotrack_data, edges_gdf)
    #
    # with open(f"{rg.parent_directory_at_level(__file__, 4)}/Operational_Data/temp/isotrack_gdf_3.pickle", 'wb') as target:
    #     pickle.dump(isotrack_data, target)
    # fname = f"{rg.parent_directory_at_level(__file__, 4)}/Operational_Data/temp/isotrack_gdf_3.pickle"
    # isotrack_gdf = loadNetworkResults(fname)
    #
    # cluster_gdfs = routesgraph.RoutesGraph().generate_routes_graph(isotrack_gdf, road_graph)
    # edges, nodes = cluster_gdfs[1.0]
    # edges.to_file(f"{rg.parent_directory_at_level(__file__, 4)}/Operational_Data/temp/cluster_edges_{1.0}_v3.shp")
    # nodes.to_file(f"{rg.parent_directory_at_level(__file__, 4)}/Operational_Data/temp/cluster_nodes_{1.0}_v3.shp")

    # for cluster_id in cluster_gdfs:
    #     edges, nodes = cluster_gdfs[cluster_id]
    #
    #     edges.to_file(f"{rg.parent_directory_at_level(__file__, 4)}/Operational_Data/temp/cluster_edges_{cluster_id}.shp")
    #     nodes.to_file(f"{rg.parent_directory_at_level(__file__, 4)}/Operational_Data/temp/cluster_nodes_{cluster_id}.shp")