import pandas as pd
import geopandas as gpd
import pickle
import os
import networkx as nx

from RoadGraph import OSToStdGdfConverter, StdNodesEdgesGdfBuilder, StdNodesEdgesGdfConnector
from RoadGraph.StdColNames import *
from RoadGraph.StdKeyWords import *


class StdRoadGraphBuilder:

    def __init__(self, converter=OSToStdGdfConverter(), builder=StdNodesEdgesGdfBuilder(),
                 connector=StdNodesEdgesGdfConnector()):
        self.converter = converter
        self.builder = builder
        self.connector = connector

    def build_road_graph(self, in_path, target_path, is_conversion_required=True):

        curr_path = in_path
        out_path = self._create_file_path(target_path + "/out")

        if is_conversion_required:
            curr_path = self._convert_gdfs(curr_path, out_path)

        curr_path = self._build_edges_nodes_gdfs(curr_path, out_path)
        curr_path = self._connect_edges_and_nodes_gdfs(curr_path, out_path)

        edges_gdf = gpd.read_file(curr_path + "/edges.shp")
        nodes_gdf = gpd.read_file(curr_path + "/nodes.shp")

        net = self.create_graph(nodes_gdf, edges_gdf)
        target_path = self._create_file_path(out_path + "/netx")
        target_file = target_path + "/roadGraph.pickle"

        with open(target_file, 'wb') as target:
            pickle.dump(net, target)

        return net

    def _convert_gdfs(self, in_path, out_path):

        """
        Converts multiple shp geospatial roads dataframes into the standard GeoDataFrame used for this project.
        The results are saved in the out_path directory
        :param in_path: File path containing all shp files that are to be converted
        :param out_path: File path in which the converted standard dataframes are to be saved
        :param roads_to_exclude: Any roads to be excluded (should be in list form)
        """
        converted_path = self._create_file_path(out_path + "/converted")
        list_of_files = os.listdir(in_path)
        shp_full_paths_in = [in_path + "/" + x for x in list_of_files if ".shp" in x]
        shp_full_paths_out = [converted_path + "/" + x for x in list_of_files if ".shp" in x]

        n = len(shp_full_paths_in)
        for i in range(n):
            print("iteration: " + str(i + 1) + " out of " + str(n + 1))
            os_gdf = gpd.read_file(shp_full_paths_in[i])
            self.converter.convert_to_std_gdf(os_gdf, shp_full_paths_out[i])

        return converted_path

    def _build_edges_nodes_gdfs(self, in_path, out_path):

        connected_path = self._create_file_path((out_path + "/connected"))
        prefix = 'A'

        list_of_files = os.listdir(in_path)
        shp_full_paths_in = [in_path + "/" + x for x in list_of_files if ".shp" in x]
        shp_full_paths_out = []
        for file in list_of_files:
            if ".shp" in file:
                shp_full_paths_out.append(connected_path + "/" + prefix)
                prefix = chr(ord(prefix) + 1)

        n = len(shp_full_paths_in)

        prefix = 'A'
        for i in range(n):
            print("iteration: " + str(i + 1) + " out of " + str(n + 1))
            std_gdf = gpd.read_file(shp_full_paths_in[i])
            self._create_file_path(shp_full_paths_out[i])
            self.builder.build_nodes_and_edges_gdf(std_gdf, shp_full_paths_out[i], node_tag=prefix)
            prefix = chr(ord(prefix) + 1)

        return connected_path

    def _connect_edges_and_nodes_gdfs(self, in_path, out_path):

        list_of_files = os.listdir(in_path)
        shp_full_paths_in = [in_path + "/" + x for x in list_of_files if not x.startswith(".")]
        final_path = self._create_file_path(out_path + "/final")

        n = len(shp_full_paths_in)
        gdf_edges = gpd.read_file(shp_full_paths_in[0] + "/edges.shp")
        gdf_nodes = gpd.read_file(shp_full_paths_in[0] + "/nodes.shp")

        for i in range(1, n):
            print("iteration: " + str(i + 1) + " out of " + str(n + 1))
            aux_edges = gpd.read_file(shp_full_paths_in[i] + "/edges.shp")
            aux_nodes = gpd.read_file(shp_full_paths_in[i] + "/nodes.shp")
            gdf_edges, gdf_nodes = self.connector.connect_two_nodeEdges_std_gdfs(gdf_edges, gdf_nodes,
                                                                                 aux_edges, aux_nodes)

        gdf_edges.to_file(final_path + "/edges.shp")
        gdf_nodes.to_file(final_path + "/nodes.shp")

        return final_path


    def merge_road_segments(self, roads_df, road_index):
        """
        Merges all linked road segments and condense information into a dict
        :param road_index: index of starting road segment
        :param roads_df: Linked Road segments geodataframe
        :return: d: a dictionary containing coordinates, length, indices and unique road ID of road
                final_node: final node that this road connects to
        """
        d = {}

        current_segment = roads_df.loc[roads_df[STD_INDEX] == road_index]
        current_segment = current_segment.iloc[0]

        length = current_segment[STD_LENGTH]
        road_segment_index = [road_index]
        road_id = current_segment[STD_ROAD_NO] + "_" + current_segment[STD_ROAD_TYPE]

        while not pd.isna(current_segment[STD_NEXT_IND]):
            current_segment = roads_df.loc[roads_df[STD_INDEX] == int(current_segment[STD_NEXT_IND])]
            current_segment = current_segment.iloc[0]
            length += current_segment[STD_LENGTH]
            road_segment_index.extend([STD_INDEX])

        final_node = current_segment[STD_TO_NODE]
        d["Road_id"] = road_id
        d["Length"] = length
        d["Road_segment_indices"] = road_segment_index

        return d, final_node

    def create_graph(self, nodes_gdf, edges_gdf):
        """
        Creates a graph NetworkX object using roads_gdf and nodes_gdf
        :param edges_gdf: geodataframe of roads
        :param nodes_gdf: geodataframe of nodes
        :return: net: A networkX object representing road network.
        """
        print("Creating Graph")

        net = nx.DiGraph()
        # for each slip road and roundabout node dataframe do:
        for _, node in nodes_gdf.iterrows():
            net.add_node(node.node_id, coordinates=node.geometry)

        start_segments = edges_gdf.loc[(edges_gdf[STD_ROAD_TYPE] == STD_MAIN_CARRIAGEWAY) |
                                       (edges_gdf[STD_ROAD_TYPE] == STD_SLIP_ROAD)]

        start_segments = start_segments.loc[pd.isna(edges_gdf["PREV_IND"])]
        n = 1

        for index, start_segment in start_segments.iterrows():
            print(index)
            segment_index = start_segment[STD_INDEX]
            from_node = start_segment[STD_FROM_NODE]
            attr, to_node = self.merge_road_segments(edges_gdf, segment_index)
            net.add_edge(from_node, to_node, attr=attr)
            if not start_segment[STD_IS_DIREC]:
                print('bi-directional')
                net.add_edge(to_node, from_node, attr=attr)

        print("Finished Graph")

        return net

    def _extract_shp_names(self, file_path):
        list_of_files = os.listdir(file_path)
        shp_tags = [x for x in list_of_files if ".shp" in x]

        if len(shp_tags) == 1:
            return shp_tags[0]
        else:
            return shp_tags

    def _create_file_path(self, file_path):
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        return file_path


