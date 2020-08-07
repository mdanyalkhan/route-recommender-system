from collections import deque

from shapely.geometry import Point
import os
from RoadGraph import StdRoadGraph, create_file_path
from RoadGraph.constants.StdColNames import *
from RoadGraph.constants.StdKeyWords import *
from RoadGraph.analysis import VulnerabilityAnalyser as va
import pandas as pd
import geopandas as gpd
import networkx as netx
import re

# Column Names
NUMBER = 'number'
GEOMETRY = 'geometry'
ROAD = 'Road'
JUNCTION = 'Junctions'


def output_res_dict_to_csv(res_dict: dict, out_path: str):
    """
    Outputs values pertaining to variables for every site pair. In order of worst affected.
    :param res_dict: Dictionary of journey times for each site pair
    :param out_path: Folder path in which to save the results
    """
    excluded_keys = [va.SHORTEST_PATH, va.DELAYED_SHORTEST_PATH]
    out_path = create_file_path(f"{out_path}/results")

    filtered_res_dict = {key: res_dict[key] for key in res_dict if key not in excluded_keys}
    df = pd.DataFrame(filtered_res_dict, columns=list(filtered_res_dict.keys()))
    df.sort_values(va.RES_INDEX, inplace=True)
    df.to_csv(f"{out_path}/results.csv")


def output_res_dict_shortest_path_as_shp(road_graph: StdRoadGraph, res_dict: dict, out_path: str,
                                         no_of_paths: int = None):
    """
    Outputs no_of_paths shortest paths as shapefiles in out_path
    :param road_graph: road graph that the shortest paths are based on.
    :param res_dict: Dictionary of journey times for each site pair.
    :param out_path: Folder path in which to save the results
    :param no_of_paths: No of journey times to save as shapefile, saved in accordance with worst affected time.
    """
    out_path = create_file_path(f"{out_path}/results")
    df = pd.DataFrame(res_dict, columns=list(res_dict.keys()))
    df.sort_values(va.RES_INDEX, inplace=True)

    if not no_of_paths:
        no_of_paths = len(df)

    for i in range(no_of_paths):
        fname = re.sub('\s+', '_', df.iloc[i][va.SITE_PAIRS])
        file_path = create_file_path(f"{out_path}/{fname}")
        s_edges_gdf, s_nodes_gdf = road_graph.convert_path_to_gdfs(df.iloc[i][va.SHORTEST_PATH])
        n_edges_gdf, n_nodes_gdf = road_graph.convert_path_to_gdfs(df.iloc[i][va.DELAYED_SHORTEST_PATH])

        s_edges_gdf.to_file(f"{file_path}/s_edges.shp")
        s_nodes_gdf.to_file(f"{file_path}/s_nodes.shp")
        n_edges_gdf.to_file(f"{file_path}/c_edges.shp")
        n_nodes_gdf.to_file(f"{file_path}/c_nodes.shp")


def merge_road_closure_shp_into_single_shp(closure_shp_path: str):
    list_of_files = os.listdir(closure_shp_path)

    # Only consider directories with the prefix 'closure'
    shp_full_paths_in = [closure_shp_path + "/" + x for x in list_of_files if x.startswith("closure") and not \
        x.endswith('.csv')]

    merged_gdf = gpd.GeoDataFrame()
    for shp_path in shp_full_paths_in:
        edges_gdf = gpd.read_file(f"{shp_path}/edges.shp")
        merged_gdf = gpd.GeoDataFrame(pd.concat([merged_gdf, edges_gdf]))
    merged_gdf.crs = {'init': 'epsg:27700'}
    merged_gdf.to_file(f"{closure_shp_path}/full_closures.shp")

def journey_time_impact_closure_shp_path(road_graph: StdRoadGraph, key_sites: gpd.GeoDataFrame, closure_shp_path: str):
    """
    Examines the potential increase to journey times given the proposed closure of roads via shapefiles
    :param road_graph: Road graph object that is representational of the UK road network
    :param key_sites: Key sites to examine journey times between
    :param closure_shp_path: Path where closure shapefile data is saved
    :return:
        A matrix of the resilience index for each site pair
        A dictionary of the change in resilience index, as well as journey times before and after closure for impacted
        sites.
    """
    list_of_files = os.listdir(closure_shp_path)

    # Only consider directories with the prefix 'closure'
    shp_full_paths_in = [closure_shp_path + "/" + x for x in list_of_files if x.startswith("closure") and not \
        x.endswith('.csv')]

    # Deduce node pairs corresponding to the proposed closure of the edges.
    all_node_pairs = []
    for shp_path in shp_full_paths_in:
        print(shp_path)
        edges_gdf = gpd.read_file(f'{shp_path}/edges.shp')
        node_pairs = _extract_node_pairs_from_edges_shp(road_graph.edges, edges_gdf)
        all_node_pairs.extend(node_pairs)

    vuln_analyser = va.VulnerabilityAnalyser(road_graph)

    return vuln_analyser.vulnerability_all_sites_by_node_pairs(key_sites, 'location_n', all_node_pairs)


def journey_time_impact_closure_dict(road_graph: StdRoadGraph, key_sites: gpd.GeoDataFrame, closure_dict: dict):
    """
    Examines the potential increase in journey times given the provided closures of roads.
    :param road_graph: Road graph object that is representational of the UK road network
    :param key_sites: Key sites to examine journey times between
    :param closure_dict: Data structure containing proposed closure of roads
    :return:
        A matrix of the resilience index for each site pair
        A dictionary of the change in resilience index, as well as journey times before and after closure for impacted
        sites.
    """
    vuln_analyser = va.VulnerabilityAnalyser(road_graph)
    node_pairs = [node_pair for closure in closure_dict for node_pair in closure_dict[closure]['node_pairs']]
    return vuln_analyser.vulnerability_all_sites_by_node_pairs(key_sites, 'location_n', node_pairs)


def _extract_node_pairs_from_edges_shp(edges: gpd.GeoDataFrame, sel_edges: gpd.GeoDataFrame):
    """
    Extracts the nodes between the edges.
    :param edges: Geo-Data Frame of the line segments that form the edges of the road network
    :param sel_edges: Geo-Data Frame of the edges selected for closure
    :return: List of tuples, each tuple containing the pair nodes that are connected to the proposed line segment to be
    closed.
    """
    all_node_pairs = []

    edges['visited'] = False
    sel_edges = sel_edges.loc[sel_edges[STD_ROAD_TYPE] != STD_ROUNDABOUT]
    for i in range(len(sel_edges)):
        index = sel_edges.iloc[i][STD_INDEX]
        if not edges.loc[edges[STD_INDEX] == index, 'visited'].values[0]:
            que = deque()
            que.append(index)
            while que:
                sel_ind = que.popleft()
                edges.at[edges[STD_INDEX] == sel_ind, 'visited'] = True
                if edges.loc[edges[STD_INDEX] == sel_ind, STD_FROM_NODE].values[0] != STD_NONE:
                    from_node = edges.loc[edges[STD_INDEX] == sel_ind, STD_FROM_NODE].values[0]
                else:
                    prev_ind = int(edges.loc[edges[STD_INDEX] == sel_ind, STD_PREV_IND].values[0])
                    if not edges.loc[edges[STD_INDEX] == prev_ind, 'visited'].values[0]:
                        que.append(prev_ind)

                if edges.loc[edges[STD_INDEX] == sel_ind, STD_TO_NODE].values[0] != STD_NONE:
                    to_node = edges.loc[edges[STD_INDEX] == sel_ind, STD_TO_NODE].values[0]
                else:
                    next_ind = int(edges.loc[edges[STD_INDEX] == sel_ind, STD_NEXT_IND].values[0])
                    if not edges.loc[edges[STD_INDEX] == next_ind, 'visited'].values[0]:
                        que.append(next_ind)

            all_node_pairs.append((from_node, to_node))
    edges.drop(['visited'], axis=1, inplace=True)
    return all_node_pairs


def generate_road_closures(road_graph: StdRoadGraph, junctions_data: gpd.GeoDataFrame,
                           closure_data: pd.DataFrame, out_path: str = None) -> dict:
    """
    Generates a dictionary of edges and nodes to be closed based on each closure.

    :param road_graph: StdRoadGraph object representative of a road network in the UK
    :param junctions_data: Geo-Data Frame of points representing known junctions
    :param closure_data: Dataframe of closure data, generally indicating the road in which the closure is proposed
    to occur, and a description of the closure
    :return: A dictionary with the following:
        {<Closure number>:
                            {'road_id' : <road id of road to be closed>,
                             'closure description' : <Description of closure based on closure data>,
                             'junction nodes': <The known junctions associated with this closure, based on
                                                junction data>,
                             'node_pairs : <The pair of nodes encasing the edge that will be closed>',
                             'edge_indices': <Description of edges to be closed>}
        }
    """
    real_junctions = junctions_data[NUMBER].tolist()
    real_junc_coordinates = junctions_data[GEOMETRY].tolist()
    closure_road_no = closure_data.loc[:, ROAD].tolist()
    closure_junc_desc = closure_data.loc[:, JUNCTION].tolist()

    closure_dict = _assign_proposed_graph_closures(road_graph.net, closure_road_no, closure_junc_desc, real_junctions,
                                                   real_junc_coordinates)

    if out_path:
        _convert_closures_to_csv(closure_dict, out_path)
        _convert_closures_to_shp(road_graph, closure_dict, out_path)

    return closure_dict


def _convert_closures_to_csv(closure_dict: dict, out_path: str):
    """
    Saves closure_dict to csv through out_path
    :param closure_dict: Data structure containing proposed closure data
    :param out_path: Path in which to save the closure data to
    """
    rows = [row for row in closure_dict.values()]
    df = pd.DataFrame(rows)
    df.to_csv(f"{out_path}/closure_data.csv")


def _convert_closures_to_shp(roadGraph: StdRoadGraph, closure_dict: dict, out_path: str):
    """
    Saves proposed closure of edges and nodes to a series of shapefiles.
    :param roadGraph: Road graph representative of the UK road network
    :param closure_dict: Data structure containing proposed road closures
    :param out_path: Path in which to save the shapefiles to.
    """
    for closure in closure_dict:
        node_pairs = closure_dict[closure]['node_pairs']
        edge_ind = closure_dict[closure]['edge_indices']

        if node_pairs and edge_ind:
            path = create_file_path(f"{out_path}/{closure}")
            node_set = [node for node_pair in node_pairs for node in node_pair]
            node_set = list(set(node_set))
            sel_edges_gdf = roadGraph.edges.loc[roadGraph.edges[STD_INDEX].isin(edge_ind)]
            sel_nodes_gdf = roadGraph.nodes.loc[roadGraph.nodes[STD_NODE_ID].isin(node_set)]

            sel_edges_gdf.to_file(f'{path}/edges.shp')
            sel_nodes_gdf.to_file(f'{path}/nodes.shp')


def _assign_proposed_graph_closures(G: netx.DiGraph, road_ids: list, closure_descriptions: list, real_junctions: list,
                                    real_junction_coords: list) -> dict:
    """
    Generates dictionary of edges and nodes to be closed based on closure data
    :param G: Networkx graph object of the road network
    :param road_ids: List of road numbers in which the closures are proposed
    :param closure_descriptions: List of descriptions of each closure
    :param real_junctions: List of recognised junction objects
    :param real_junction_coords: Coordinates of the junction objects
    :return:  A dictionary with the following:
        {<Closure number>:
                            {'road_id' : <road id of road to be closed>,
                             'closure description' : <Description of closure based on closure data>,
                             'junction nodes': <The known junctions associated with this closure, based on
                                                junction data>,
                             'node_pairs : <The pair of nodes encasing the edge that will be closed>',
                             'edge_indices': <Description of edges to be closed>}
        }
    """
    closure_dict = {}

    for i in range(len(road_ids)):
        road_id = road_ids[i]

        #Check if its empty row, if empty row then skip
        if pd.isna(road_id):
            continue

        key = f"closure_{i + 1}_{road_id}"
        closure_dict[key] = {}

        if road_id[-1] == 'M':
            road_id = f"{road_id[:-1]}({road_id[-1]})"

        closure_dict[key]["road_id"] = road_id
        closure_dict[key]["closure_description"] = closure_descriptions[i]
        junc_candidates = _parse_closure_description_for_junctions(closure_descriptions[i])
        junc_candidates = _augment_road_id_with_junc_name(road_id, junc_candidates)
        junc_candidates, _ = _filter_junc_candidates(junc_candidates, real_junctions, real_junction_coords)
        closure_dict[key]['junction_nodes'] = [junction[0] for junction in junc_candidates]

        nearest_nodes = _map_junctions_to_nearest_nodes(G, junc_candidates, 1000.0)
        edge_closures, node_pairs = _find_closure_edges(G, nearest_nodes, road_id)
        closure_dict[key]['node_pairs'] = node_pairs
        closure_dict[key]['edge_indices'] = edge_closures

    return closure_dict


def _parse_closure_description_for_junctions(input: str) -> list:
    """
    Parses through the closure description input to find a list of potential junction names that may be closed.
    :param input: Closure description
    :return: list of potential junctions that will be closed based on the closure description
    """

    input_list = input.split()

    junction_candidates = []

    # Insert junction range
    for i in range(1, len(input_list) - 1):
        if input_list[i] == '-':
            if input_list[i - 1][0] == 'J' and input_list[i + 1][0] == 'J':
                first_junc = int(input_list[i - 1][1:]) if input_list[i - 1][1:].isdigit() else None
                second_junc = int(input_list[i + 1][1:]) if input_list[i + 1][1:].isdigit() else None

                if first_junc and second_junc:
                    first, last = (first_junc, second_junc) if first_junc < second_junc else (second_junc, first_junc)
                    while first <= last:
                        junction_candidates.append(f"J{first}")
                        first += 1

    # Add in any other outstanding junctions
    junction_candidates += [junction for junction in input_list if junction[0] == 'J' and
                            junction not in junction_candidates]

    # Add in possible junctions with Motorway Nos added as potential prefix
    for i in range(len(input_list) - 1):
        if input_list[i][0] == 'M' or input_list[i][0] == 'A':
            if input_list[i + 1][0] == 'J':
                junction_candidates.append(f"{input_list[i]} {input_list[i + 1]}")

    # Set all potential letters in the junction names as upper case
    for i in range(len(junction_candidates)):
        if junction_candidates[i][-1].isalpha():
            junction_candidates[i] = f"{junction_candidates[i][:-1]}{junction_candidates[i][-1].upper()}"

    return junction_candidates


def _augment_road_id_with_junc_name(road_id: str, junc_names: list) -> list:
    """
    Assigns the road id as the prefix of junction names, with the exception of junction names that already have
    a road number prefixed.
    :param road_id: road number
    :param junc_names: list of junction names
    :return: list of junction names with the road number prefixed.
    """
    new_junc_names = []
    for i in range(len(junc_names)):
        new_junc_names.append(f"{road_id} {junc_names[i]}" if junc_names[i][0] == 'J' else junc_names[i])

    return new_junc_names


def _filter_junc_candidates(junc_candidates: list, real_junctions: list, real_junc_coords: list):
    """
    Verifies which of the possible junction candidates exists within the list of recognised junctions

    :param junc_candidates: list of junction candidates
    :param real_junctions: list of real junctions
    :param real_junc_coords: corresponding list of coordinates of real junctions
    :return:
            accepted - list of tuples of real junctions to be closed, along with its corresponding coordinate
            rejected - list of junctions candidates that do not exist in the list of known junctions.
    """
    accepted = []
    rejected = []

    for junc_candidate in junc_candidates:
        if junc_candidate in real_junctions:
            real_junc_ind = real_junctions.index(junc_candidate)
            point = real_junc_coords[real_junc_ind]

            if len(list(point.coords)) > 2:
                point = Point([xy[0:2] for xy in list(point.coords)])

            accepted.append((junc_candidate, point))
        else:
            rejected.append(junc_candidate)

    return accepted, rejected


def _map_junctions_to_nearest_nodes(G: netx.DiGraph, junctions: list, tolerance: float):
    """
    Finds the nearest set of nodes within G to the junction node in junctions
    :param G: NetworkX object of road networks
    :param junctions: List of junction nodes, containing a tuple of the junction ID and corresponding coordinates
    :param tolerance: The search radius, if above this value, then node is not considered, otherwise it is considered
    :return: List of nearest nodes.
    """
    nearest_nodes = []
    nodes_in_graph = list(G.nodes)

    for junction in junctions:
        coordinates = junction[1]
        for node in nodes_in_graph:
            node_coordinates = G._node[node]['coordinates']
            distance = coordinates.distance(node_coordinates)
            if distance <= tolerance:
                nearest_nodes.append(node)

    return nearest_nodes


def _find_closure_edges(G: netx.DiGraph, nearest_nodes: list, road_id: str) -> (list, list):
    """
    Finds the edges to close based on road number and nodes
    :param G: NetworkX object of road network
    :param nearest_nodes: The nodes in the graph that are close to closure junction
    :param road_id: road number tha tis propsed to be closed.
    :return:
            edge_indices - the indices of the edges that are proposed to be closed
            node_pairs - tuple of node pairs in between each group of edge indices to be closed.
    """
    edge_indices = []
    node_pairs = []
    for node in nearest_nodes:
        for neighbour, edge in G.succ[node].items():
            edge_road_id = edge['attr']['road_id'].split('_')[0]
            if edge_road_id == road_id:
                edge_indices.extend(G[node][neighbour]['attr']["road_segment_indices"])
                node_pairs.append((node, neighbour))
    return edge_indices, node_pairs
