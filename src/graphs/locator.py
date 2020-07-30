from collections import deque

import RoadGraph
from RoadGraph.analysis import closureanalysis as ca
from src.utilities.file_directories import FileDirectories as fd
from src.utilities.aux_func import parent_directory_at_level, loadNetworkResults
import pandas as pd
import geopandas as gpd
import datetime


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



if __name__ == "__main__":
    closure_path = parent_directory_at_level(__file__, 4) + fd.CLOSURE_DATA.value
    junctions_path = parent_directory_at_level(__file__, 5) + fd.HE_JUNCTIONS.value
    net_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/netx/roadGraph.pickle"
    edges_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/final/edges.shp"
    nodes_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/final/nodes.shp"
    rm_path = f"{parent_directory_at_level(__file__, 4)}/Operational_Data/lbb/lbb_rm_locations/lbb_rm_locations.shp"
    lbb_closure_path = f"{parent_directory_at_level(__file__, 4)}/Operational_Data/lbb/closures"
    # edges_gdf = gpd.read_file(edges_path)
    # sel_edges = gpd.read_file(parent_directory_at_level(__file__, 4) +
    #                           "/Operational_Data/lbb/closures/closure_1/edges.shp")
    #
    # extract_node_pairs_from_edges_shp(edges_gdf, sel_edges)

    roadGraph = RoadGraph.StdRoadGraph(loadNetworkResults(net_path), gpd.read_file(nodes_path),
                                       gpd.read_file(edges_path))
    df = pd.read_csv(closure_path)
    junctions_df = gpd.read_file(junctions_path)
    rm_df = gpd.read_file(rm_path)

    ca.journey_time_impact_closure_shp_path(roadGraph, rm_df, lbb_closure_path)
    #
    # closure_dict = ca.generate_road_closures(roadGraph, junctions_df, df, f"{parent_directory_at_level(__file__, 4)}"
    #                                                        f"/Operational_Data/lbb/closures")
    # ca.journey_time_impact_closure_dict(roadGraph, gpd.read_file(rm_path), closure_dict)

    # real_junctions = junctions_df['number'].tolist()
    # real_junc_coordinates = junctions_df['geometry'].tolist()
    # motorways = df.loc[:, 'Road'].tolist()
    # junctions_raw = df.loc[:, 'Junctions'].tolist()
    #
    # closure_dict = assign_proposed_graph_closures(roadGraph.net, motorways, junctions_raw, real_junctions,
    #                                               real_junc_coordinates)




