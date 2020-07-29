from collections import deque

import RoadGraph
from RoadGraph.constants.StdColNames import *
from RoadGraph.constants.StdKeyWords import *
from RoadGraph import create_file_path
from src.utilities.file_directories import FileDirectories as fd
from src.utilities.aux_func import parent_directory_at_level
import pandas as pd
import geopandas as gpd
import networkx as netx
from shapely.geometry import Point
import datetime

def generate_potential_motorway_junction_name_candidates(m_input: list, j_input: list) -> dict:
    junction_suffix_candidates = []

    for i in range(len(j_input)):
        junction_suffix_candidates.append(parse_junctions(j_input[i]))

    junction_candidates = {}
    for i in range(len(m_input)):
        if m_input[i][-1] == 'M':
            m_input[i] = f"{m_input[i][:-1]}({m_input[i][-1]})"
        junction_candidates.setdefault(m_input[i], []).extend([f"{m_input[i]} {junc}"
                                                               for junc in junction_suffix_candidates[i]
                                                               if junc[0] == 'J'])
        junction_candidates[m_input[i]] = list(set(junction_candidates[m_input[i]]))

    return junction_candidates

def augment_road_id_with_junc_name(road_id: str, junc_names: list) -> list:

    new_junc_names = []
    for i in range(len(junc_names)):
        new_junc_names.append(f"{road_id} {junc_names[i]}" if junc_names[i][0] == 'J' else junc_names[i])

    return new_junc_names

def parse_junctions(input: str) -> list:
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

    # Set all potential leters in the junction names as upper case
    for i in range(len(junction_candidates)):
        if junction_candidates[i][-1].isalpha():
            junction_candidates[i] = f"{junction_candidates[i][:-1]}{junction_candidates[i][-1].upper()}"

    return junction_candidates


def locate_junction_names_from_source(motorways: list, junctions_raw: list, real_junctions: list,
                                      junc_coordinates: list):
    candidates = generate_potential_motorway_junction_name_candidates(motorways, junctions_raw)
    accepted = {}
    rejected = {}
    #
    for key, val in candidates.items():
        for junction_name in val:
            if junction_name in real_junctions:
                junc_index = real_junctions.index(junction_name)
                point = junc_coordinates[junc_index]

                if len(list(point.coords)[0]) > 2:

                    point = Point([xy[0:2] for xy in list(point.coords)])

                accepted.setdefault(key, []).append((junction_name, point))
            else:
                rejected.setdefault(key, []).append(junction_name)

    return accepted, rejected

def filter_junc_candidates(junc_candidates: list, real_junctions: list, real_junc_coords: list):

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


def map_junctions_to_nearest_nodes(G: netx.DiGraph, junctions: list, tolerance: float):

    nearest_nodes = []
    nodes_in_graph = list(G.nodes)

    for road_no in junctions:
        for junction in junctions:
            coordinates = junction[1]
            for node in nodes_in_graph:
                node_coordinates = G._node[node]['coordinates']
                distance = coordinates.distance(node_coordinates)
                if distance <= tolerance:
                    nearest_nodes.append(node)

    return nearest_nodes

def find_closure_edges(G: netx.DiGraph, nearest_nodes: list, road_id: str) -> (list, list):

    edge_indices = []
    node_pairs = []
    for node in nearest_nodes:
        for neighbour, edge in G.succ[node].items():
            edge_road_id = edge['attr']['road_id'].split('_')[0]
            if edge_road_id == road_id:
                edge_indices.extend(G[node][neighbour]['attr']["road_segment_indices"])
                node_pairs.append((node, neighbour))
    return edge_indices, node_pairs

def assign_proposed_graph_closures(G: netx.DiGraph, road_ids: list, closure_descriptions: list, real_junctions: list,
                                   real_junction_coords: list) -> dict:

    closure_dict = {}

    for i in range(len(road_ids)):
        key = f"closure_{i+1}"
        closure_dict[key] = {}
        road_id = road_ids[i]

        if road_id[-1] == 'M':
            road_id = f"{road_id[:-1]}({road_id[-1]})"

        closure_dict[key]["road_id"] = road_id
        closure_dict[key]["closure_description"] = closure_descriptions[i]
        junc_candidates = parse_junctions(closure_descriptions[i])
        junc_candidates = augment_road_id_with_junc_name(road_id, junc_candidates)
        junc_candidates, _ = filter_junc_candidates(junc_candidates, real_junctions, real_junction_coords)
        closure_dict[key]['junction_nodes'] = [junction[0] for junction in junc_candidates]

        nearest_nodes = map_junctions_to_nearest_nodes(G, junc_candidates, 1000.0)
        edge_closures, node_pairs = find_closure_edges(G, nearest_nodes, road_id)
        closure_dict[key]['node_pairs'] = node_pairs
        closure_dict[key]['edge_indices'] = edge_closures

    return closure_dict

def convert_closures_to_shp(roadGraph: RoadGraph.StdRoadGraph, closure_dict: dict, out_path: str):

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

def journey_times_from_closure_dict(closure_dict: dict):
    all_node_pairs = []

    for closure in closure_dict:
        for node_pairs in closure_dict[closure]['node_pairs']:
            all_node_pairs.append(node_pairs)

    vuln_analyser = RoadGraph.VulnerabilityAnalyser(roadGraph)
    res_matrix, res_dict = vuln_analyser.vulnerability_all_sites_by_node_pairs(rm_df, 'location_n', all_node_pairs)

    res_ordered = [(key, val) for key, val in sorted(res_dict.items(), key=lambda item: item[1]['resilience_index'])]

    for site_pair in res_ordered:
        print(f"{site_pair[0]} \t {site_pair[1]['resilience_index']} \t "
              f"{datetime.timedelta(seconds=site_pair[1]['journey_time'])} \t "
              f"{datetime.timedelta(seconds=site_pair[1]['delayed_journey_time'])}")

    return res_ordered

def extract_node_pairs_from_edges_shp(edges: gpd.GeoDataFrame, sel_edges: gpd.GeoDataFrame):
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
                    que.append(next_ind)
                    if not edges.loc[edges[STD_INDEX] == next_ind, 'visited'].values[0]:
                        que.append(next_ind)

            all_node_pairs.append((from_node, to_node))

    return all_node_pairs

def convert_closures_to_csv(closure_dict: dict, out_path: str):

    rows = [row for row in closure_dict.values()]
    df = pd.DataFrame(rows)
    df.to_csv(f"{out_path}/closure_data.csv")

if __name__ == "__main__":
    closure_path = parent_directory_at_level(__file__, 4) + fd.CLOSURE_DATA.value
    junctions_path = parent_directory_at_level(__file__, 5) + fd.HE_JUNCTIONS.value
    net_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/netx/roadGraph.pickle"
    edges_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/final/edges.shp"
    nodes_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/final/nodes.shp"
    rm_path = f"{parent_directory_at_level(__file__, 4)}/Operational_Data/lbb/lbb_rm_locations/lbb_rm_locations.shp"

    edges_gdf = gpd.read_file(edges_path)
    sel_edges = gpd.read_file(parent_directory_at_level(__file__, 4) +
                              "/Operational_Data/lbb/closures/closure_1/edges.shp")

    extract_node_pairs_from_edges_shp(edges_gdf, sel_edges)

    # roadGraph = RoadGraph.StdRoadGraph(loadNetworkResults(net_path), gpd.read_file(nodes_path),
    #                                    gpd.read_file(edges_path))
    # df = pd.read_csv(closure_path)
    # junctions_df = gpd.read_file(junctions_path)
    # rm_df = gpd.read_file(rm_path)


    # real_junctions = junctions_df['number'].tolist()
    # real_junc_coordinates = junctions_df['geometry'].tolist()
    # motorways = df.loc[:, 'Road'].tolist()
    # junctions_raw = df.loc[:, 'Junctions'].tolist()
    #
    # closure_dict = assign_proposed_graph_closures(roadGraph.net, motorways, junctions_raw, real_junctions,
    #                                               real_junc_coordinates)




