import RoadGraph
import pickle
from RoadGraph.StdColNames import *
from RoadGraph.StdKeyWords import *
from RoadGraph.util import create_file_path
from src.utilities.aux_func import parent_directory_at_level, loadNetworkResults
import geopandas as gpd
import pandas as pd


isotrack_path = parent_directory_at_level(__file__, 5) + "/Incoming/imperial_data/data_with_labels/20191002-" \
                                                         "20200130_isotrak_legs_excl_5km_train"

isotrack_list = [isotrack_path + '/20191002-20200130_isotrak_legs_excl_5km_TRAIN_MEDWAY MC_PRINCESS ROYAL DC.csv',
                 isotrack_path + '/20191002-20200130_isotrak_legs_excl_5km_TRAIN_PRINCESS ROYAL DC_SOUTH WEST DC.csv',
                 isotrack_path + '/20191002-20200130_isotrak_legs_excl_5km_TRAIN_NATIONAL DC_BRISTOL MC.csv',
                 isotrack_path + '/20191002-20200130_isotrak_legs_excl_5km_TRAIN_SOUTH WEST DC_HEATHROW WORLDWIDE DC.csv']

out_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/compare_to_telemetry"
out_prefix = ['/MD_PR', '/PR_SW', '/ND_BM', '/HW_SW']

netx_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/netx/roadGraph.pickle"
edges_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/final/edges.shp"
nodes_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/final/nodes.shp"
key_sites_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/rm_sites/rm_locations.shp"


def change_speed_limit(roadGraph: RoadGraph.StdRoadGraph, new_speed_kph: float):
    roadGraph.edges.loc[(roadGraph.edges[STD_ROAD_NO].str.startswith('A', na=False)) &
                        (roadGraph.edges[STD_FORMOFWAY].isin(STD_DUAL_CARRIAGEWAY_LIST)) &
                        (roadGraph.edges[STD_SPEED] == STD_SPEED_BUILT_UP), STD_SPEED] = new_speed_kph
    builder = RoadGraph.StdRoadGraphBuilder()
    net = builder.create_graph(roadGraph.nodes, roadGraph.edges)
    roadGraph.net = net

    return roadGraph

def change_back_to_old_speed_limit(roadGraph: RoadGraph.StdRoadGraph, new_speed_kph: float):

    roadGraph.edges.loc[(roadGraph.edges[STD_ROAD_NO].str.startswith('A', na=False)) &
                        (roadGraph.edges[STD_SPEED] == STD_SPEED_BUILT_UP), STD_SPEED] = new_speed_kph
    builder = RoadGraph.StdRoadGraphBuilder()
    net = builder.create_graph(roadGraph.nodes, roadGraph.edges)
    roadGraph.net = net

    return roadGraph

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

    # edges_gdf = gpd.read_file(edges_path)
    nodes_gdf = gpd.read_file(nodes_path)
    # net = loadNetworkResults(netx_path)
    # roadGraph = RoadGraph.StdRoadGraph(net, nodes_gdf, edges_gdf)
    #
    # change_back_to_old_speed_limit(roadGraph, 30.0)
    #
    # roadGraph.edges.to_file(edges_path)
    # with open(netx_path, 'wb') as target:
    #     pickle.dump(roadGraph.net, target)
    #
    # net = loadNetworkResults(netx_path)

    print(nodes_gdf.loc[nodes_gdf[STD_N_TYPE] == STD_N_TERMINAL])


    # for neighbour in net.neighbors('G_196'):
    #     print(neighbour)

    # net = loadNetworkResults(netx_path)
    # edges = gpd.read_file(edges_path)
    # nodes = gpd.read_file(nodes_path)
    # key_sites = gpd.read_file(key_sites_path)
    # roadGraph = RoadGraph.StdRoadGraph(net, nodes, edges)
    # # _, dist, s_edges, s_nodes = roadGraph.shortest_path_between_nodes('G_1386', 'E_702', get_gdfs=True)
    # # print(dist)
    #
    # _, dist_2, s_edges_2, s_nodes_2 = roadGraph.shortest_path_between_nodes('G_1386', 'G_2774', get_gdfs=True)
    # print(sum(s_edges_2[STD_LENGTH].tolist())/(96.0*1000.0/3600.0))
    # print(dist_2)
    #
    # print(net['G_2774']['G_595'])
    # s_edges.to_file(parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/s_edges_2.shp")
    # s_nodes.to_file(parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/s_nodes.shp")


