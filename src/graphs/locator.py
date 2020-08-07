import RoadGraph
from RoadGraph.analysis import closureanalysis as ca
from src.utilities.file_directories import FileDirectories as fd
from src.utilities.aux_func import parent_directory_at_level, loadNetworkResults
import pandas as pd
import geopandas as gpd
import os

# Relevant file paths
closure_path = f"{parent_directory_at_level(__file__, 4)}/Operational_Data/closures"
junctions_path = parent_directory_at_level(__file__, 5) + fd.HE_JUNCTIONS.value
net_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/netx/roadGraph.pickle"
edges_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/final/edges.shp"
nodes_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/final/nodes.shp"
rm_path = f"{parent_directory_at_level(__file__, 4)}/Operational_Data/lbb/lbb_rm_locations/lbb_rm_locations.shp"
lbb_closure_path = f"{parent_directory_at_level(__file__, 4)}/Operational_Data/lbb/closures"
closure_fnames = [fname for fname in os.listdir(closure_path) if fname.startswith('closure') and
                  not fname.endswith('210720.csv')]
lbb_closure_fpaths = [fpath for fpath in os.listdir(lbb_closure_path) if not fpath.startswith('.')]


def generate_closure_edges(closure_path, closure_fnames, road_graph, junctions_gdf):
    for fname in closure_fnames:
        closure_fname_path = f'{closure_path}/{fname}'
        print(fname)
        out_path = RoadGraph.create_file_path(f'{lbb_closure_path}/{fname.split("_")[2][:-4]}')
        closure_df = pd.read_csv(closure_fname_path)

        ca.generate_road_closures(road_graph, junctions_gdf, closure_df, out_path)


def generate_merged_closure_shps(directory_names, path_prefix):
    for directory_name in directory_names:
        full_path = f"{path_prefix}/{directory_name}"
        ca.merge_road_closure_shp_into_single_shp(full_path)


if __name__ == "__main__":

    road_graph = RoadGraph.StdRoadGraph(loadNetworkResults(net_path), gpd.read_file(nodes_path),
                                        gpd.read_file(edges_path))
    key_sites_gdf = gpd.read_file(rm_path)

    for dir_name in lbb_closure_fpaths:
        full_path = f'{lbb_closure_path}/{dir_name}'
        print(dir_name)
        _, res_dict = ca.journey_time_impact_closure_shp_path(road_graph, key_sites_gdf, full_path)
        ca.output_res_dict_to_csv(res_dict, full_path)
        ca.output_res_dict_shortest_path_as_shp(road_graph, res_dict, full_path, no_of_paths=10)