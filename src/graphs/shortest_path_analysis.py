import RoadGraph
import geopandas as gpd
import numpy as np
from scipy.spatial import cKDTree
from GeoDataFrameAux import extract_list_of_coords_from_geom_object
import matplotlib.pyplot as plt
from pylab import *

from src.utilities.aux_func import parent_directory_at_level, loadNetworkResults

LAT = 'Event_Lat'
LON = 'Event_Long'
CLUSTER = 'cluster'
LEG_ID = 'leg_id'
FROM_DEPOT = 'from_depot'
TO_DEPOT = 'to_depot'


def convert_isotrack_to_shpfile(in_path: str):
    return RoadGraph.util.convert_csv_to_shpfile(in_path, lat_name=LAT, long_name=LON)


def get_kth_most_used_isotrack_path(isotrack_gdf: gpd.GeoDataFrame, k: int):
    gdf_grouped = isotrack_gdf.groupby([CLUSTER], as_index=False).count().sort_values(by=[LEG_ID], ascending=False)
    return isotrack_gdf.loc[isotrack_gdf[CLUSTER] == gdf_grouped[CLUSTER].values[k]]


def get_key_site_pair_names(isotrack_gdf: gpd.GeoDataFrame):
    return isotrack_gdf[FROM_DEPOT].unique()[0], isotrack_gdf[TO_DEPOT].unique()[0]


def distance_distribution(shortest_path_gdf: gpd.GeoDataFrame, isotrack_most_used_gdf: gpd.GeoDataFrame):
    points = []
    for index, line in shortest_path_gdf.iterrows():
        points.extend(RoadGraph.extract_list_of_coords_from_geom_object(line['geometry']))

    points_x = [point[0] for point in points]
    points_y = [point[1] for point in points]

    shortest_path_coords = np.dstack([points_x, points_y])[0]
    tree = cKDTree(shortest_path_coords)

    isotrack_coords = []
    for _, point in isotrack_most_used_gdf.iterrows():
        isotrack_coords.extend(extract_list_of_coords_from_geom_object(point['geometry']))
    isotrack_x = [coord[0] for coord in isotrack_coords]
    isotrack_y = [coord[1] for coord in isotrack_coords]
    isotrack_coords = np.dstack([isotrack_x, isotrack_y])[0]

    dist, _ = tree.query(isotrack_coords, k=1)

    return dist


def generate_distance_histogram(dist):
    # An "interface" to matplotlib.axes.Axes.hist() method
    n, bins, patches = plt.hist(x=dist, bins=int(np.max(dist) / 10), color='#0504aa',
                               alpha=0.7, rwidth=0.85)

    plt.grid(axis='y', alpha=0.75)
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    plt.title('My Very Own Histogram')
    # plt.text(23, 45, r'$\mu=15, b=3$')
    maxfreq = n.max()
    # Set a clean upper y-axis limit.
    plt.ylim(ymax=np.ceil(maxfreq / 10) * 10 if maxfreq % 10 else maxfreq + 10)
    plt.xlim(xmax=6000)

    return plt


def shortest_path_analysis(roadGraph: RoadGraph.StdRoadGraph, key_sites_gdf: gpd.GeoDataFrame, key_sites_col_name: str,
                           isotrack_path: str, k, out_path: str):
    isotrack_gdf = convert_isotrack_to_shpfile(isotrack_path)
    most_used_isotrack_path_gdf = get_kth_most_used_isotrack_path(isotrack_gdf, k)
    source, target = get_key_site_pair_names(most_used_isotrack_path_gdf)
    _, _, s_edges, s_nodes = roadGraph.shortest_path_between_key_sites(source, target, key_sites_gdf,
                                                                       key_sites_col_name, get_gdfs=True)

    distances_differences = distance_distribution(s_edges, most_used_isotrack_path_gdf)
    mean_difference = np.mean(distances_differences)
    std_difference = np.std(mean_difference)
    plot = generate_distance_histogram(distances_differences)
    plot.show()
if __name__ == "__main__":
    netx_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/plcr/out/netx/roadGraph.pickle"
    edges_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/plcr/out/final/edges.shp"
    nodes_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/plcr/out/final/nodes.shp"
    key_sites_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/rm_sites/rm_locations.shp"
    isotrack_path = parent_directory_at_level(__file__, 5) + "/Incoming/imperial_data/data_with_labels/20191002-" \
                                                             "20200130_isotrak_legs_excl_5km_train"
    isotrack_list = [isotrack_path + '/20191002-20200130_isotrak_legs_excl_5km_TRAIN_NATIONAL DC_SHEFFIELD MC.csv',
                     isotrack_path + '/20191002-20200130_isotrak_legs_excl_5km_TRAIN_NOTTINGHAM MC_EAST '
                                     'MIDLANDS AIRPORT.csv']

    roadGraph = RoadGraph.StdRoadGraph(loadNetworkResults(netx_path),gpd.read_file(nodes_path),
                                       gpd.read_file(edges_path))
    key_sites_gdf = gpd.read_file(key_sites_path)
    shortest_path_analysis(roadGraph, key_sites_gdf, 'location_n', isotrack_list[0], 0, None)
