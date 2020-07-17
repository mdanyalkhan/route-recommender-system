import RoadGraph
from GeoDataFrameAux import extract_list_of_coords_from_geom_object
from RoadGraph.util import create_file_path
from src.utilities.aux_func import parent_directory_at_level, loadNetworkResults
import geopandas as gpd
import pandas as pd
import numpy as np
from scipy.spatial.distance import directed_hausdorff
from scipy.spatial import cKDTree
import matplotlib.pyplot as plt



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
        gdf_second_choice = gdf.loc[gdf['cluster'] == gdf_grouped['cluster'].values[1]]
        gdf_first_choice.to_file(f"{create_file_path(out_path + out_prefix[i])}/{out_prefix[i]}_most_used.shp")
        gdf_second_choice.to_file(f"{out_path}{out_prefix[i]}/{out_prefix[i]}_second_most_used.shp")
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
        _, _, s_edges, s_nodes = roadGraph.shortest_path_between_key_sites(source, target, key_sites,
                                                                           key_site_col_name='location_n',
                                                                           get_gdfs=True)
        s_edges.to_file(f"{create_file_path(out_path + out_prefix[i])}/{out_prefix[i]}_edges_shortest_path.shp")
        s_nodes.to_file(f"{out_path}{out_prefix[i]}/{out_prefix[i]}_nodes_shortest_path.shp")


def calculate_hausdorff(graph_path: gpd.GeoDataFrame, isotrack_path: gpd.GeoDataFrame):
    shortest_path_coords = []

    for _, line in graph_path.iterrows():
        shortest_path_coords.extend(extract_list_of_coords_from_geom_object(line['geometry']))
    shortest_path_coords = np.array(shortest_path_coords)

    isotrack_coords = []

    for _, point in isotrack_path.iterrows():
        isotrack_coords.extend(extract_list_of_coords_from_geom_object(point['geometry']))
    isotrack_coords = np.array(isotrack_coords)

    dist, _, _ = directed_hausdorff(shortest_path_coords, isotrack_coords)
    print(dist)

def measure_similarity(isotrack_path: gpd.GeoDataFrame, shortest_path: gpd.GeoDataFrame):

    points=[]
    for index, line in shortest_path.iterrows():
        points.extend(extract_list_of_coords_from_geom_object(line['geometry']))

    points_x = [point[0] for point in points]
    points_y = [point[1] for point in points]

    shortest_path_coords = np.dstack([points_x, points_y])[0]
    tree = cKDTree(shortest_path_coords)


    isotrack_coords = []

    for _, point in isotrack_path.iterrows():
        isotrack_coords.extend(extract_list_of_coords_from_geom_object(point['geometry']))
    isotrack_x = [coord[0] for coord in isotrack_coords]
    isotrack_y = [coord[1] for coord in isotrack_coords]
    isotrack_coords = np.dstack([isotrack_x, isotrack_y])[0]

    dist, ind = tree.query(isotrack_coords, k=1)

    print(np.mean(dist))
    print(np.std(dist))

    # An "interface" to matplotlib.axes.Axes.hist() method
    n, bins, patches = plt.hist(x=dist, bins=int(np.max(dist)/10), color='#0504aa',
                                alpha=0.7, rwidth=0.85)
    plt.grid(axis='y', alpha=0.75)
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    plt.title('My Very Own Histogram')
    plt.text(23, 45, r'$\mu=15, b=3$')
    maxfreq = n.max()
    # Set a clean upper y-axis limit.
    plt.ylim(ymax=np.ceil(maxfreq / 10) * 10 if maxfreq % 10 else maxfreq + 10)
    plt.xlim(xmax=6000)
    plt.show()


if __name__ == '__main__':

    shortest_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/plcr/out/compare_to_telemetry/" \
                                                             "ND_SH/ND_SH_edges_shortest_path.shp"
    isotrack_path = parent_directory_at_level(__file__,
                                              4) + "/Operational_Data/plcr/out/compare_to_telemetry/ND_SH/ND_SH_most_used.shp"
    isotrack_gdf = gpd.read_file(isotrack_path)
    shortest_path_gdf = gpd.read_file(shortest_path)
    measure_similarity(isotrack_gdf, shortest_path_gdf)