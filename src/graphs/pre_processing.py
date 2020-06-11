import numpy as np
import geopandas as gpd
import pandas as pd
import src.graphs.SRN_column_names as srn_cn
from shapely.geometry import MultiLineString
from shapely import wkt
from math import sqrt
import networkx as nx
from GeoDataFrameAux import *


def extract_coord(line_object, index: int):

    list_of_coords = extract_list_of_coords_from_geom_line(line_object)
    return list_of_coords[index]


def extract_list_of_coords_from_geom_line(line_object):
    list_of_coords = []
    if type(line_object) is MultiLineString:
        list_of_lines = list(line_object)
        for line in list_of_lines:
            list_of_coords.extend(list(line.coords))
    else:
        list_of_coords = list(line_object.coords)
    return list_of_coords


def is_coord_equal(coord1: tuple, coord2: tuple):
    return (abs(coord1[0] - coord2[0]) < 1.0) and (abs(coord1[1] - coord2[1]) < 1.0)


def filter_to_slip_roads_and_roundabouts(he_data):
    return he_data.loc[
        (he_data[srn_cn.FUNCT_NAME] == "Slip Road") | (he_data[srn_cn.FUNCT_NAME] == "Roundabout")].copy()


def filter_to_main_carriageway(he_data):
    return he_data.loc[he_data[srn_cn.FUNCT_NAME] == "Main Carriageway"].copy()


def link_roads(he_df):
    """
    Links all roads, and creates nodes between main carriageways and slip roads, roads and roundabouts, and dead-ends
    :param he_df:
    :return: updated he_df containing new columns prev_ind, next_ind, from_node, to_node, and index. And nodes_df
    containing the node IDs.
    """
    print("Running Link_roads")
    # Insert index as column
    he_df.insert(loc=0, column="INDEX", value=he_df.index)
    # Set up link columns for each road segment (much like block linking)
    he_df["PREV_IND"] = pd.NA
    he_df["NEXT_IND"] = pd.NA
    # Extract first and last coordinates of each road segment
    he_df["FIRST_COORD"] = he_df["geometry"].apply(lambda x: extract_coord(x, 0))
    he_df["LAST_COORD"] = he_df["geometry"].apply(lambda x: extract_coord(x, -1))

    # Set from_node and to_node columns
    he_df["FROM_NODE"] = "None"
    he_df["TO_NODE"] = "None"

    # Set up a dict of nodes
    nodes = {}
    # Link all main carriageways and slip roads
    he_df = link_based_on_funct_name(he_df, "Main Carriageway")
    he_df = link_based_on_funct_name(he_df, "Slip Road")

    # link_main_cariageways_to_slip_roads
    he_df, slip_road_nodes = link_main_carriageways_to_slip_roads(he_df, nodes)

    # link_roundabouts_to_segments
    he_df, roundabout_nodes = link_roundabouts_to_segments(he_df, nodes)

    # set new nodes for all remaining ends of roads that are not connected
    he_df, dead_end_nodes = assign_nodes_to_dead_end_roads(he_df, nodes)

    he_df.drop(['FIRST_COORD', 'LAST_COORD'], axis=1, inplace=True)

    nodes_df = pd.DataFrame(nodes)
    nodes_df["coordinates"] = nodes_df["coordinates"].apply(GeoPointDataFrameBuilder()._build_geometry_object)
    nodes_df["coordinates"] = nodes_df["coordinates"].apply(wkt.loads)

    nodes_gdf = gpd.GeoDataFrame(nodes_df, geometry="coordinates")
    nodes_gdf.crs = {'init': 'epsg:27700'}
    print("Finished Link_roads")

    return he_df, nodes_gdf


def assign_nodes_to_dead_end_roads(he_df: gpd.GeoDataFrame, node_dict: dict):
    """
    Assigns nodes to all other roads that have ends that are not connected
    :param he_df: roads dataframe
    :param node_dict: nodes data structure to record new nodes
    :return: updated he_df and node_dict
    """
    print("Starting assign_nodes_to_dead_end_roads")
    dead_ends = he_df.loc[(he_df["FROM_NODE"] == "None") | (he_df["TO_NODE"] == "None")]
    dead_ends = dead_ends.loc[(pd.isna(he_df["PREV_IND"])) | (pd.isna(he_df["NEXT_IND"]))]
    dead_ends = dead_ends.loc[(he_df["FUNCT_NAME"] == "Main Carriageway") |
                              (he_df["FUNCT_NAME"] == "Slip Road")]
    for index, dead_end in dead_ends.iterrows():
        if pd.isna(dead_end.PREV_IND) and dead_end.FROM_NODE == "None":
            coord = dead_end.FIRST_COORD
            node_dict = assign_new_node_id(node_dict, coord, "D")

            he_df.at[index, "FROM_NODE"] = node_dict["node_id"][-1]
        if pd.isna(dead_end.NEXT_IND) and dead_end.TO_NODE == "None":
            coord = dead_end.LAST_COORD
            node_dict = assign_new_node_id(node_dict, coord, "D")
            he_df.at[index, "TO_NODE"] = node_dict["node_id"][-1]

    print("Finishing assign_nodes_to_dead_end_roads")

    return he_df, node_dict


def euclidean_distance(coord1: tuple, coord2: tuple):
    """
    Calculates the Euclidean distance between two coordinates
    :param coord1: Tuple of numerical digits
    :param coord2: Second tupe of numerical digits
    :return: Returns the Euclidean distance between two coordinates
    """
    x1, y1 = coord1
    x2, y2 = coord2
    return sqrt(pow(x1 - x2, 2) + pow(y1 - y2, 2))


def find_closest_road(he_df: gpd.geodataframe, target_coord: tuple, use_first_coord=True):
    """
    Identifies the main carriageway closest to target_coord
    :param he_df: geodataframe containing the roads geospatial data
    :param target_coord: coordinates to use to compare all roads with
    :param use_first_coord: Use the first-coordinates of the main carriageway for comparison, otherwise use the last
    :return: The index and distance of the main carriageway closest to target_coord
    """
    # Set up a temporary column of distances in he_df
    he_df["distances"] = np.inf

    if use_first_coord:
        COORD = "FIRST_COORD"
    else:
        COORD = "LAST_COORD"

    # Apply euclidean distance to coordinates column of he_df
    carriageway_df = he_df.loc[he_df["FUNCT_NAME"] == "Main Carriageway"]
    # carriageway_df.loc["distances"] = carriageway_df[COORD].apply(lambda x: euclidean_distance(x, target_coord))
    distances = carriageway_df[COORD].apply(lambda x: euclidean_distance(x, target_coord))
    # Find index corresponding to minimum distance and return
    closest_road = carriageway_df.loc[carriageway_df["distances"] == carriageway_df["distances"].min()]
    min_dist = distances.min()
    index = distances.index[distances == distances.min()][0]
    min_index = carriageway_df.loc[index, "INDEX"]
    he_df.drop("distances", axis=1, inplace=True)

    return min_index, min_dist


def configure_links_and_assign_nodes(he_df: gpd.geodataframe, node_dict: dict, target_coord: tuple,
                                     slip_road_index: int, min_index: int, min_distance: float,
                                     threshold: float = 5, is_prev: bool = True):
    """
    Re-assigns the main carriageway's link with a slip road and sets the corresponding nodes
    :param he_df: The roads geodataframe containing the main carriageway and slip roads
    :param node_dict: Dictionary of node IDs and their corresponding coordinates
    :param min_index: Index of the carriageway closest to the slip road
    :param min_distance: Distance of the carriageway with respect to the slip road
    :param threshold: Distance threshold in which a connection between the carriageway and slip road is recognised
    :param is_prev: Establishes whether connection is with respect to the beginning or end of slip road
    :return: he_df with updates to reflect connectivity and nodal connection between slip road and carriageways
    """
    if is_prev:
        ind_a = "NEXT_IND"
        ind_b = "PREV_IND"
        node_a = "FROM_NODE"
        node_b = "TO_NODE"
    else:
        ind_a = "PREV_IND"
        ind_b = "NEXT_IND"
        node_a = "TO_NODE"
        node_b = "FROM_NODE"

    if min_distance < threshold:
        node_dict = assign_new_node_id(node_dict, target_coord, "S")
        # Update connections to adjacent carriageway segment (if there is one)
        if not pd.isna(he_df.loc[he_df["INDEX"] == min_index, ind_a].values[0]):
            index = he_df.loc[he_df["INDEX"] == min_index, ind_a].values[0]
            he_df.loc[he_df["INDEX"] == index, ind_b] = pd.NA
            he_df.loc[he_df["INDEX"] == index, node_a] = node_dict["node_id"][-1]
        # update connection to current carriageway
        he_df.loc[he_df["INDEX"] == min_index, ind_a] = pd.NA
        he_df.loc[he_df["INDEX"] == min_index, node_b] = node_dict["node_id"][-1]
        he_df.loc[he_df["INDEX"] == slip_road_index, node_a] = node_dict["node_id"][-1]

    return he_df


def assign_new_node_id(node_dict: dict, coords: tuple, prefix: str):
    """
    Assigns a new node ID into node_dict
    :param node_dict: existing data structure containing list of nodes
    :param coords: coordinate of new node ID
    :return: updated node_dict
    """
    # Set node_dict with coordinates of FIRST_COORD

    if not bool(node_dict):
        first_term = prefix + str(1)
        node_dict["node_id"] = [first_term]
    elif node_dict["node_id"][-1][0] != prefix:
        first_term = prefix + str(1)
        node_dict["node_id"].extend([first_term])

    else:
        node_dict["node_id"].extend([node_dict["node_id"][-1][0] + str(int(node_dict["node_id"][-1][1:]) + 1)])

    node_dict.setdefault("coordinates", []).extend([coords])
    return node_dict


def link_main_carriageways_to_slip_roads(he_df: gpd.geodataframe, node_dict: dict):
    """
    Identfies and establishes connections between slip roads and main carriageways. Where
    connections are identified, a new node is generated and incorporated into the roads
    geospatial data structure.

    :param he_df: roads geospatial datastructure containing the main carriageways and slip roads
    :param node_dict: existing data structure containing the list of nodes
    :return: updated he_df and node_dict
    """
    slip_roads_df = he_df.loc[he_df["FUNCT_NAME"] == "Slip Road"]
    slip_roads_df = slip_roads_df.loc[(pd.isna(he_df["PREV_IND"])) | (pd.isna(he_df["NEXT_IND"]))]

    print("Starting link_main_carriageways_to_slip_roads")
    for _, slip_road in slip_roads_df.iterrows():
        index = slip_road.INDEX

        if pd.isna(slip_road.PREV_IND):  # If PREV_IND is <NA> then:
            first_coord = slip_road.FIRST_COORD
            min_index, min_dist = find_closest_road(he_df, first_coord, use_first_coord=False)
            he_df = configure_links_and_assign_nodes(he_df, node_dict, first_coord, index, min_index, min_dist)

        if pd.isna(slip_road.NEXT_IND):
            last_coord = slip_road.LAST_COORD
            min_index, min_dist = find_closest_road(he_df, last_coord, use_first_coord=True)
            he_df = configure_links_and_assign_nodes(he_df, node_dict, last_coord, index, min_index, min_dist,
                                                     is_prev=False)

    print("Finishing link_main_carriageways_to_slip_roads")
    return he_df, node_dict


def link_roundabouts_to_segments(he_df: gpd.geodataframe, node_dict: dict, threshold: float = 10):
    """
    Identifies and establishes connections between all road segments and connections. Where
    connections are identified, a new node is generated and incorporated into the roads
    geospatial data structure.

    :param threshold: Threshold to use to consider roads to be linked to roundabout
    :param he_df: geospatial data structure containing the main carriageways, slip roads, and roundabouts
    :param node_dict: Existing data structure containing list of roundabout nodes
    :return: updated he_df and node_dict
    """
    print("Starting link_roundabouts_to_segments")
    # Select all roundabouts
    roundabout_df = he_df.loc[he_df["FUNCT_NAME"] == "Roundabout"]
    # For every roundabout do the following:
    for _, roundabout in roundabout_df.iterrows():
        # Set representative coordinate of roundabout and set up node into node_dict
        node_coord = calculate_mean_roundabout_pos(roundabout)
        roundabout_coords = list(roundabout["geometry"].coords)
        #:TODO: sort out magic number below
        roundabout_refined_coords = increase_resolution_of_line(roundabout_coords, 2)
        node_dict = assign_new_node_id(node_dict, node_coord, "R")
        # Identify the closest of distances between the roundabout and the FIRST_COORD and LAST_COORD of each road segment.
        he_df["distance_first"] = he_df.loc[(he_df["FUNCT_NAME"] == "Main Carriageway") |
                                            (he_df["FUNCT_NAME"] == "Slip Road"), "FIRST_COORD"] \
            .apply(lambda x: calculate_proximity_of_road_to_roundabout(roundabout_refined_coords, x))
        he_df["distance_last"] = he_df.loc[(he_df["FUNCT_NAME"] == "Main Carriageway") |
                                           (he_df["FUNCT_NAME"] == "Slip Road"), "LAST_COORD"] \
            .apply(lambda x: calculate_proximity_of_road_to_roundabout(roundabout_refined_coords, x))

        he_df.loc[he_df["distance_first"] <= threshold, "FROM_NODE"] = node_dict["node_id"][-1]
        he_df.loc[he_df["distance_first"] <= threshold, "PREV_IND"] = pd.NA

        he_df.loc[he_df["distance_last"] <= threshold, "TO_NODE"] = node_dict["node_id"][-1]
        he_df.loc[he_df["distance_last"] <= threshold, "NEXT_IND"] = pd.NA
        he_df.drop(['distance_last', 'distance_first'], axis=1, inplace=True)

    print("Finishing link_roundabouts_to_segments")

    return he_df, node_dict

def increase_resolution_of_line(line_coords: list, min_spacing):

    n = len(line_coords)
    index = 1

    while index < n:
        coord_a = line_coords[index - 1]
        coord_b = line_coords[index]

        if euclidean_distance(coord_a, coord_b) > min_spacing:

            midpoint = calculate_midpoint(coord_a, coord_b)
            line_coords.insert(index, midpoint)
            n += 1
        else:
            index+=1

    return line_coords

def calculate_midpoint(coord_a, coord_b):

    x1,y1 = coord_a
    x2,y2 = coord_b

    return ((x1+x2)/2, (y1+y2)/2)

def calculate_proximity_of_road_to_roundabout(roundabout_coords: list, target_coord: tuple):
    """
    Calculates the distance of the road segment relative to roundabout
    :param roundabout: geodataframe of roundabout
    :param target_coord: coordinates tuple
    :return nearest_distance: closest distance from roundabout to road segment
    """
    distance = []
    for coord in roundabout_coords:
        distance.append(euclidean_distance(coord, target_coord))
    return min(distance)

def calculate_mean_roundabout_pos(roundabout: gpd.GeoDataFrame):
    """
    Calculates the mean coordinates of the roundabout
    :param roundabout: geodataframe of roundabout
    :return: mean coordinates of roundabout
    """
    coords = list(roundabout["geometry"].coords)
    n = len(coords)
    x_sum = 0
    y_sum = 0

    for coord in coords:
        x_sum += coord[0]
        y_sum += coord[1]
    x_ave = x_sum / n
    y_ave = y_sum / n

    return (x_ave, y_ave)


def link_based_on_funct_name(he_df, funct_name: str):
    """
    Explicitly links all road segments by function name and geometry
    :param he_df: Geodataframe of roads data
    :funct_name: name of road type to perform linking on
    :return: A GeoDataframe with extra columns that links each road segment
    """
    carriageway_df = he_df.loc[he_df["FUNCT_NAME"] == funct_name]
    road_numbers = carriageway_df.ROA_NUMBER.unique()
    directions = carriageway_df.DIREC_CODE.unique()
    print("Starting link_based_on_funct_name")

    for road_number in road_numbers:
        for direction in directions:
            carriageway = carriageway_df.loc[(carriageway_df["ROA_NUMBER"] == road_number) &
                                             (carriageway_df["DIREC_CODE"] == direction)]

            for index, segment in carriageway.iterrows():

                last_coord = segment.LAST_COORD
                connecting_road = carriageway.index[carriageway["FIRST_COORD"].
                    apply(lambda x: is_coord_equal(x, last_coord))].tolist()

                if (len(connecting_road) == 1):
                    he_df.loc[index, "NEXT_IND"] = connecting_road[0]
                    he_df.loc[connecting_road[0], "PREV_IND"] = index

    print("Finishing link_based_on_funct_name")

    return he_df


def merge_road_segments(roads_df, road_index):
    """
    Merges all linked road segments and condense information into a dict
    :param road_index: index of starting road segment
    :param roads_df: Linked Road segments geodataframe
    :return: d: a dictionary containing coordinates, length, indices and unique road ID of road
            final_node: final node that this road connects to
    """
    d = {}

    current_segment = roads_df.loc[roads_df["INDEX"] == road_index]
    current_segment = current_segment.iloc[0]

    coords = extract_list_of_coords_from_geom_line(current_segment.geometry)
    length = current_segment.SEC_LENGTH
    road_segment_index = [road_index]
    road_id = current_segment.ROA_NUMBER + "_" + current_segment.DIREC_CODE + "_" + current_segment.FUNCT_NAME

    while not pd.isna(current_segment.NEXT_IND):
        current_segment = roads_df.loc[roads_df.INDEX == current_segment.NEXT_IND]
        current_segment = current_segment.iloc[0]
        coords += extract_list_of_coords_from_geom_line(current_segment.geometry.coords)
        length += current_segment.SEC_LENGTH
        road_segment_index.extend([current_segment.INDEX])

    final_node = current_segment.TO_NODE
    d["ROAD_ID"] = road_id
    d["LENGTH"] = length
    d["road_segment_index"] = road_segment_index
    d["geometry"] = coords


    return d, final_node


def create_graph(roads_gdf: gpd.GeoDataFrame, nodes_gdf: gpd.GeoDataFrame):
    """
    Creates a graph NetworkX object using roads_gdf and nodes_gdf
    :param roads_gdf: geodataframe of roads
    :param nodes_gdf: geodataframe of nodes
    :return: net: A networkX object representing road network.
    """
    print("Creating Graph")

    net = nx.DiGraph()
    # for each slip road and roundabout node dataframe do:
    for _, node in nodes_gdf.iterrows():
        net.add_node(node.node_id, coordinates=node.coordinates)

    start_segments = roads_gdf.loc[(roads_gdf["FUNCT_NAME"] == "Main Carriageway") |
                                   (roads_gdf["FUNCT_NAME"] == "Slip Road")]

    start_segments = start_segments.loc[pd.isna(roads_gdf["PREV_IND"])]

    for _, start_segment in start_segments.iterrows():
        segment_index = start_segment.INDEX
        from_node = start_segment.FROM_NODE
        attr, to_node = merge_road_segments(roads_gdf, segment_index)
        net.add_edge(from_node, to_node, attr = attr)

    print("Finished Graph")

    return net
