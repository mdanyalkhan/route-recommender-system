from src.utilities.aux_func import *
from RoadGraph.util import *
import RoadGraph
import os

if __name__ == "__main__":
    # original_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/testing/original"
    # out_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/testing"
    # built_up_path = parent_directory_at_level(__file__, 4) + "/Other_incoming_data/BuiltUpAreas/built_up_areas.shp"
    #
    # converter = RoadGraph.OSToStdGdfConverter(speed_criteria='Complex', built_up_gdf=gpd.read_file(built_up_path))
    # builder = RoadGraph.StdRoadGraphBuilder(converter)
    # builder.build_road_graph(original_path, out_path)

    edges_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/final/edges.shp"
    nodes_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/final/nodes.shp"
    net_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/netx/roadGraph.pickle"
    key_sites_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/rm_sites/rm_locations.shp"
    out_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/vulnerability"

    builder = RoadGraph.StdRoadGraphBuilder()
    net = builder.create_graph(gpd.read_file(nodes_path), gpd.read_file(edges_path))
    with open(net_path, 'wb') as target:
        pickle.dump(net, target)

    # in_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/connected"
    # out_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out"
    # builder = RoadGraph.StdRoadGraphBuilder()
    # builder._connect_edges_and_nodes_gdfs(in_path, out_path)
    # roadGraph = RoadGraph.StdRoadGraph(loadNetworkResults(net_path), gpd.read_file(nodes_path),
    #                                    gpd.read_file(edges_path))
    # key_sites_gdf = gpd.read_file(key_sites_path)
    # source, target = "HEATHROW WORLDWIDE DC", "BRISTOL MC"
    #
    # RoadGraph.VulnerabilityAnalyser(roadGraph). \
    #     srn_vulnerability_two_sites(source, target, key_sites_gdf,
    #                                 'location_n', out_path)
