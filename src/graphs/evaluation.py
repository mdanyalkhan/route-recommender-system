from scipy.spatial.distance import directed_hausdorff
import RoadGraph
from RoadGraph.graphreduce import *
from RoadGraph.constants import *
import geopandas as gpd
from scipy.spatial import cKDTree
from RoadGraph.util import extract_list_of_coords_from_geom_object
from pylab import *
import datetime
from src.utilities.aux_func import loadNetworkResults
import src.utilities.file_directories as fd

LAT = 'Event_Lat'
LON = 'Event_Long'
CLUSTER = 'cluster'
LEG_ID = 'leg_id'
FROM_DEPOT = 'from_depot'
TO_DEPOT = 'to_depot'


def convert_isotrack_to_shpfile(in_path: str) -> gpd.GeoDataFrame:
    """
    Converts the isotrack file from in_path into a geopandas dataframe.

    :param in_path: path containing the isotrack file
    :return: converted geopandas dataframe of isotrack file from in_path
    """
    return RoadGraph.util.convert_csv_to_shpfile(in_path, lat_name=LAT, long_name=LON)


def get_kth_most_used_isotrack_path(isotrack_gdf: gpd.GeoDataFrame, k: int) -> gpd.GeoDataFrame:
    """
    Extracts the kth (starting from 0) most used route from the isotrack data set.

    :param isotrack_gdf: Geo-DataFrame containing all routes.
    :param k: value indicating which most-used route to select
    :return: Geo-DataFrame of kth most used route.
    """
    gdf_grouped = isotrack_gdf.groupby([CLUSTER], as_index=False).count().sort_values(by=[LEG_ID], ascending=False)
    kth_most_used_gdf = isotrack_gdf.loc[isotrack_gdf[CLUSTER] == gdf_grouped[CLUSTER].values[k]].copy()
    return kth_most_used_gdf.reset_index(drop=True)


def get_key_site_pair_names(isotrack_gdf: gpd.GeoDataFrame) -> (str, str):
    """
    Returns the site names the isotrack Geo-DataFrame pertains to.

    :param isotrack_gdf: Isotrack Geo-Dataframe
    :return: The depot pair name that the isotrack data refers to
    """
    return isotrack_gdf[FROM_DEPOT].unique()[0], isotrack_gdf[TO_DEPOT].unique()[0]


def distance_distribution(shortest_path_gdf: gpd.GeoDataFrame, isotrack_most_used_gdf: gpd.GeoDataFrame):
    """
    Calculates the proximity of the paths betweeen 'shortest_path_gdf' and 'isotrack_most_used_gdf'

    :param shortest_path_gdf: Recommended path as a Geo-DataFrame.
    :param isotrack_most_used_gdf: Most frequently used path in accordance with the isotrack data.
    :return: List of distances (float) representing the smallest distance between every point in isotrack_most_used_gdf
    and shortest_path_gdf.
    """
    points = []
    for index, line in shortest_path_gdf.iterrows():
        points.extend(RoadGraph.util.extract_list_of_coords_from_geom_object(line['geometry']))

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
    """
    Generates a histogram of the distances.

    :param dist: list recording the proximity of the most frequently used path with the recommended route
    :return: histogram plot.
    """
    # An "interface" to matplotlib.axes.Axes.hist() method
    n, bins, patches = plt.hist(x=dist, bins=int(np.max(dist) / 10), color='#0504aa',
                                alpha=0.7, rwidth=0.85)

    plt.grid(axis='y', alpha=0.75)
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    plt.title('My Very Own Histogram')
    maxfreq = n.max()
    # Set a clean upper y-axis limit.
    plt.ylim(ymax=np.ceil(maxfreq / 10) * 10 if maxfreq % 10 else maxfreq + 10)
    plt.xlim(xmax=6000)

    return plt


def assign_isotrack_path_to_graph_segments(roadGraph: RoadGraph.stdroadgraph, isotrack_path_gdf: gpd.GeoDataFrame,
                                           out_path: str = None):
    """
    Generates the set of edges and nodes corresponding to the pings in isotrack_path_gdf

    :param roadGraph: road graph object in which the pings will be mapped to.
    :param isotrack_path_gdf: Data set containing the pings.
    :param out_path: Optional outpath in which to save the mapped edges and nodes
    :return: the nodes and edges geopandas DataFrames.
    """
    if out_path:
        out_path = RoadGraph.util.create_file_path(f'{out_path}/graph_rep')

    RoadAssignment().assign_nearest_nodes(isotrack_path_gdf, roadGraph.edges, roadGraph.nodes)
    route_graph = RoutesGraph().generate_stdRoadGraph_from_isotrack(isotrack_path_gdf, roadGraph, out_path)

    return route_graph.edges, route_graph.nodes


def calculate_hausdorff(graph_path: gpd.GeoDataFrame, isotrack_path: gpd.GeoDataFrame):
    """
    Calculates the Hausdorff distance based on the two inputs.

    :param graph_path: Geopandas dataframe of nodes representing the graph path.
    :param isotrack_path: Geopandas dataframe of pings representing the isotrack_path
    :return: The Hausdorff Distance.
    """
    shortest_path_coords = []

    for _, line in graph_path.iterrows():
        shortest_path_coords.extend(extract_list_of_coords_from_geom_object(line['geometry']))
    shortest_path_coords = np.array(shortest_path_coords)

    isotrack_coords = []

    for _, line in isotrack_path.iterrows():
        isotrack_coords.extend(extract_list_of_coords_from_geom_object(line['geometry']))
    isotrack_coords = np.array(isotrack_coords)

    dist, _, _ = directed_hausdorff(shortest_path_coords, isotrack_coords)
    return dist


def duration_of_isotrack_journey(isotrack_df: gpd.GeoDataFrame):
    """
    Calculate the average duration and its corresponding standard deviation in isotrack_gdf

    :param isotrack_df: Geopandas dataframe representing a distinct route between two depot pairs
    :return: Average duration of this route, and its corresponding standard deviation.
    """
    LEG_ID = "leg_id"
    CLUSTER = "cluster"
    FROM_DEPOT = 'from_depot'
    TO_DEPOT = 'to_depot'
    EVENT_DTTM = "Event_Dttm"
    START_TIME = 'start_time'
    END_TIME = 'end_time'
    DURATION = 'duration'

    df_grouped = isotrack_df.groupby([LEG_ID, CLUSTER, FROM_DEPOT, TO_DEPOT]).agg(
        {EVENT_DTTM: ["min", "max"]}).reset_index()

    df_grouped.columns = [LEG_ID, CLUSTER, FROM_DEPOT, TO_DEPOT, START_TIME, END_TIME]
    df_grouped[DURATION] = df_grouped[END_TIME] - df_grouped[START_TIME]
    mean_time = np.mean(df_grouped[DURATION].values)
    std_time = np.std(df_grouped[DURATION].values.astype(int))

    return datetime.timedelta(seconds=int(mean_time) * 10 ** (-9)), datetime.timedelta(
        seconds=int(std_time) * 10 ** (-9))


def calculate_time_component(s_edges: gpd.GeoDataFrame):
    """
    Calculates the time to traverse all of the edges within s_edges.

    :param s_edges: Geopandas Dataframe of line segments with the STD_LENGTH and STD_SPEED attributes
    :return: The total calculated time to traverse the edges in s_edges.
    """
    time_per_line_segment = s_edges[STD_LENGTH].values / (s_edges[STD_SPEED].values * (1000.0 / 3600.0))
    total_time = np.sum(time_per_line_segment)
    return total_time


def evaluate_shortest_path(roadGraph: RoadGraph.stdroadgraph, key_sites_gdf: gpd.GeoDataFrame, key_sites_col_name: str,
                           isotrack_path: str, k, criteria_type: int, out_path: str = None):
    """
    Conducts and compares the recommended route from the road_graph and the kth most used route within isotrack_path.

    :param roadGraph: road graph object as StdRoadGraph
    :param key_sites_gdf: Geopandas Dataframe of key sites
    :param key_sites_col_name: Column name containing the list of file names
    :param isotrack_path: Path in which the isotrack data is saved.
    :param k: value to be used to extract the kth most used route from the isotrack data
    :param criteria_type: weighting criteria type, could be 1,2, or 3.
    :param out_path: Optional path where the results can be saved.
    :return: List of distance differences, and a histogram plot of these distances.
    """
    isotrack_gdf = convert_isotrack_to_shpfile(isotrack_path)
    most_used_isotrack_path_gdf = get_kth_most_used_isotrack_path(isotrack_gdf, k)
    isotrack_s_time, isotrack_std_time = duration_of_isotrack_journey(most_used_isotrack_path_gdf)

    isotrack_edges, isotrack_nodes = assign_isotrack_path_to_graph_segments(roadGraph, most_used_isotrack_path_gdf)

    source, target = get_key_site_pair_names(most_used_isotrack_path_gdf)
    _, s_time, s_edges, s_nodes = roadGraph.shortest_path_between_key_sites(source, target, key_sites_gdf,
                                                                            key_sites_col_name, get_gdfs=True)
    if criteria_type == 1:
        s_time = calculate_time_component(s_edges)

    distances_differences = distance_distribution(s_edges, most_used_isotrack_path_gdf)
    hausdorff_dist = calculate_hausdorff(s_edges, isotrack_edges)
    mean_difference = np.mean(distances_differences)
    std_difference = np.std(distances_differences)
    plot = generate_distance_histogram(distances_differences)

    # Need to ensure the datetime objects are converted into a string object first
    isotrack_gdf['Event_Dttm'] = isotrack_gdf['Event_Dttm'].astype(str)
    most_used_isotrack_path_gdf['Event_Dttm'] = most_used_isotrack_path_gdf['Event_Dttm'].astype(str)

    if out_path:
        isotrack_gdf.to_file(f"{out_path}/isotrack_all_paths.shp")
        most_used_isotrack_path_gdf.to_file(f"{out_path}/isotrack_most_used.shp")
        s_edges.to_file(f"{out_path}/edges_shortest_path.shp")
        s_nodes.to_file(f"{out_path}/nodes_shortest_path.shp")
        isotrack_edges.to_file(f"{out_path}/edges_isotrack_most_used.shp")
        isotrack_nodes.to_file(f"{out_path}/nodes_isotrack_most_used.shp")

        stats_output = f"Mean Difference in Distance: {mean_difference}\n" \
                       f"Standard Deviation: {std_difference}\n" \
                       f"Hausdorff Distance: {hausdorff_dist}\n" \
                       f"Road Graph Journey time: {datetime.timedelta(seconds=int(s_time))}\n" \
                       f"Isotrack Journey time: {isotrack_s_time} +/- {isotrack_std_time}"
        with open(f"{out_path}/statistics.txt", 'w') as target:
            target.write(stats_output)

        plot.savefig(f"{out_path}/Distance_Histogram.png")

    return distances_differences, plot


def evaluate_shortest_path_grouped(directories: fd.ParentDirectories, criteria=3):
    """
    Evaluates the shortest paths between multiple depots and compares this with the corresponding most used routes

    :param directories: directories object containing the list of directories pertaining to a particular road graph
    :param criteria: Weighting criteria type: 1, 2, or 3.
    """
    if criteria == 1:
        netx_path = directories.netx_path_criteria1
        main_out_path = directories.out_path_criteria1
    elif criteria == 2:
        netx_path = directories.netx_path_criteria2
        main_out_path = directories.out_path_criteria2
    else:
        netx_path = directories.netx_path_criteria3
        main_out_path = directories.out_path_criteria3

    net = loadNetworkResults(netx_path)
    edges = gpd.read_file(directories.edges_path)
    nodes = gpd.read_file(directories.nodes_path)
    key_sites = gpd.read_file(directories.key_sites_path)
    roadGraph = RoadGraph.StdRoadGraph(net, nodes, edges)

    RoadGraph.util.create_file_path(main_out_path)

    isotrack_list = list(directories.isotrack_dict.keys())

    for isotrack_prefix in isotrack_list:
        out_path = RoadGraph.util.create_file_path(f"{main_out_path}/{isotrack_prefix}")
        evaluate_shortest_path(roadGraph, key_sites, 'location_n', directories.isotrack_dict[isotrack_prefix], 0,
                               criteria_type=1, out_path=out_path)


if __name__ == '__main__':
    directories = fd.plcrDirectories()
    evaluate_shortest_path_grouped(directories, criteria=1)
    evaluate_shortest_path_grouped(directories, criteria=2)
    evaluate_shortest_path_grouped(directories, criteria=3)
