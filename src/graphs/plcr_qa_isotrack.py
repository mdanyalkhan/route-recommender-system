import RoadGraph
from RoadGraph.util import create_file_path
from src.utilities.aux_func import parent_directory_at_level, loadNetworkResults
import geopandas as gpd
import pandas as pd


isotrack_path = parent_directory_at_level(__file__, 5) + "/Incoming/imperial_data/data_with_labels/20191002-" \
                                                         "20200130_isotrak_legs_excl_5km_train"

isotrack_list = [isotrack_path + '/20191002-20200130_isotrak_legs_excl_5km_TRAIN_NATIONAL DC_SHEFFIELD MC.csv',
                 isotrack_path + '/20191002-20200130_isotrak_legs_excl_5km_TRAIN_NOTTINGHAM MC_EAST MIDLANDS AIRPORT.csv']

out_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/plcr/out/compare_to_telemetry"
out_prefix = ['/ND_SH', '/NT_EM']

netx_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/plcr/out/netx/roadGraph.pickle"
edges_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/plcr/out/final/edges.shp"
nodes_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/plcr/out/final/nodes.shp"
key_sites_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/rm_sites/rm_locations.shp"

def convert_lbb_isotrack_to_shp():
    """
    Converts isotrack cluster labelled csv files into shpfiles, additionally produces the shpfile for the most used
    path.
    """

    for i in range(len(out_prefix)):
        gdf = RoadGraph.util.convert_csv_to_shpfile(isotrack_list[i], lat_name='Event_Lat', long_name='Event_Long')
        gdf_grouped = gdf.groupby(['cluster'], as_index=False).count().sort_values(by=['leg_id'], ascending=False)
        gdf_first_choice = gdf.loc[gdf['cluster'] == gdf_grouped['cluster'].values[0]]
        gdf_first_choice.to_file(f"{create_file_path(out_path + out_prefix[i])}/{out_prefix[i]}_most_used.shp")
        gdf.to_file(out_path + out_prefix[i])

def shortest_paths_in_lbb():

    net = loadNetworkResults(netx_path)
    edges = gpd.read_file(edges_path)
    nodes = gpd.read_file(nodes_path)
    key_sites = gpd.read_file(key_sites_path)
    roadGraph = RoadGraph.StdRoadGraph(net, nodes, edges)

    for i in range(len(isotrack_list)):
        isotrack_df = pd.read_csv(isotrack_list[i])
        source, target = isotrack_df['from_depot'].unique()[0], isotrack_df['to_depot'].unique()[0]
        _, _, s_edges, s_nodes=roadGraph.shortest_path_between_key_sites(source, target, key_sites,
                                                                         key_site_col_name='location_n', get_gdfs=True)
        s_edges.to_file(f"{create_file_path(out_path + out_prefix[i])}/{out_prefix[i]}_edges_shortest_path.shp")
        s_nodes.to_file(f"{out_path}{out_prefix[i]}/{out_prefix[i]}_nodes_shortest_path.shp")


if __name__ == '__main__':
    shortest_paths_in_lbb()