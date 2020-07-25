from src.utilities.file_directories import FileDirectories as fd
from src.utilities.aux_func import parent_directory_at_level, loadNetworkResults
import pandas as pd
import geopandas as gpd
import networkx as netx
from shapely.geometry import Point

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
                print(node)
                print(G._node[node])
                node_coordinates = G._node[node]['coordinates']
                distance = coordinates.distance(node_coordinates)
                if distance <= tolerance:
                    nearest_nodes.append(node)

    return nearest_nodes

def assign_proposed_graph_closures(G: netx.DiGraph, road_ids: list, closure_descriptions: list, real_junctions: list,
                                   real_junction_coords: list) -> dict:

    closure_dict = {}

    for i in range(len(road_ids)):
        key = f"closure_{i+1}"
        closure_dict[key] = {}
        road_id = road_ids[i]

        if road_id[-1] == 'M':
            road_id[i] = f"{road_id[i][:-1]}({road_id[i][-1]})"

        closure_dict[key]["road_id"] = road_ids[i]
        closure_dict[key]["closure_description"] = closure_descriptions[i]
        junc_candidates = parse_junctions(closure_descriptions[i])
        junc_candidates = augment_road_id_with_junc_name(road_id, junc_candidates)
        junc_candidates, _ = filter_junc_candidates(junc_candidates, real_junctions, real_junction_coords)
        closure_dict[key]['junction_nodes'] = [junction[0] for junction in junc_candidates]

        nearest_nodes = map_junctions_to_nearest_nodes(G, junc_candidates, 1000.0)
        closure_dict[key]['Graph Nodes'] = nearest_nodes

    return closure_dict

if __name__ == "__main__":
    closure_path = parent_directory_at_level(__file__, 4) + fd.CLOSURE_DATA.value
    junctions_path = parent_directory_at_level(__file__, 5) + fd.HE_JUNCTIONS.value
    net_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/netx/roadGraph.pickle"

    df = pd.read_csv(closure_path)
    junctions_df = gpd.read_file(junctions_path)
    net = loadNetworkResults(net_path)

    print(net._node['G_15'])
    # real_junctions = junctions_df['number'].tolist()
    # real_junc_coordinates = junctions_df['geometry'].tolist()
    # motorways = df.loc[:, 'Road'].tolist()
    # junctions_raw = df.loc[:, 'Junctions'].tolist()
    #
    # accepted, rejected = locate_junction_names_from_source(motorways, junctions_raw, real_junctions,
    #                                                        real_junc_coordinates)
    #
    # nearest_nodes = map_junctions_to_nearest_nodes(net, accepted, 1000)
    # # accepted_junctions = [junctions for values in accepted.values() for junctions in values]
