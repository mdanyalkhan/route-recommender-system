from shapely.geometry import Point

from RoadGraph import StdRoadGraph
import pandas as pd
import geopandas as gpd
import networkx as netx

# Column Names
NUMBER = 'number'
GEOMETRY = 'geometry'
ROAD = 'Road'
JUNCTION = 'Junction'


def generate_road_closures(road_graph: StdRoadGraph, junctions_data: gpd.GeoDataFrame,
                           closure_data: pd.DataFrame) -> dict:
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

    return _assign_proposed_graph_closures(road_graph.net, closure_road_no, closure_junc_desc, real_junctions,
                                           real_junc_coordinates)


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
        key = f"closure_{i + 1}"
        closure_dict[key] = {}
        road_id = road_ids[i]

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