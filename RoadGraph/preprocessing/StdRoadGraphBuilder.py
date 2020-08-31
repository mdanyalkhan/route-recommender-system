import pandas as pd
import geopandas as gpd
import pickle
import os
import networkx as nx
from RoadGraph import OSToStdGdfConverter, StdNodesEdgesGdfBuilder, StdNodesEdgesGdfConnector
from RoadGraph.constants.StdColNames import *
from RoadGraph.constants.StdKeyWords import *
from RoadGraph.util import create_file_path


class StdRoadGraphBuilder:

    def __init__(self, converter=OSToStdGdfConverter(), builder=StdNodesEdgesGdfBuilder(),
                 connector=StdNodesEdgesGdfConnector()):
        self.converter = converter
        self.builder = builder
        self.connector = connector

    def build_road_graph(self, in_path: str, target_path: str, is_conversion_required: bool = True,
                         weight_type: str = "Time") -> nx.Graph:
        """
        Constructs a Networkx Object from the original geo spatial roads dataframe, saving the intermediate
        dataframe within specified paths via target_path
        :param in_path: Path containing all roads dataframe shpfiles
        :param target_path: Path to save the Networkx object (in .pickle) and other intermediate dataframes
        :param is_conversion_required: Conversion of the original geo spatial dataframe into a standardised dataframe
        :param weight_type: type of weight to be used for the edges, either 'Time' or 'Length'
        :return: A Networkx Graph object representing the roads geoDataFrame.
        """
        curr_path = in_path
        out_path = create_file_path(target_path + "/out")

        if is_conversion_required:
            curr_path = self._convert_gdfs(curr_path, out_path)

        curr_path = self._build_edges_nodes_gdfs(curr_path, out_path)
        curr_path = self._connect_edges_and_nodes_gdfs(curr_path, out_path)

        edges_gdf = gpd.read_file(curr_path + "/edges.shp")
        nodes_gdf = gpd.read_file(curr_path + "/nodes.shp")

        net = self.create_graph(nodes_gdf, edges_gdf, weight_type)
        target_path = create_file_path(out_path + "/netx")
        target_file = target_path + "/roadGraph.pickle"

        with open(target_file, 'wb') as target:
            pickle.dump(net, target)

        return net

    def _convert_gdfs(self, in_path: str, out_path: str) -> str:

        """
        Converts multiple shp geospatial roads dataframes into the standard GeoDataFrame used for this project.
        The results are saved in the out_path directory
        :param in_path: File path containing all shp files that are to be converted
        :param out_path: File path in which the converted standard dataframes are to be saved
        :return converted_path: the path in which the converted geodataframes are saved
        """
        converted_path = create_file_path(out_path + "/converted")
        list_of_files = os.listdir(in_path)
        shp_full_paths_in = [in_path + "/" + x for x in list_of_files if ".shp" in x]
        shp_full_paths_out = [converted_path + "/" + x for x in list_of_files if ".shp" in x]

        n = len(shp_full_paths_in)
        for i in range(n):
            print("iteration: " + str(i + 1) + " out of " + str(n + 1))
            os_gdf = gpd.read_file(shp_full_paths_in[i])
            self.converter.convert_to_std_gdf(os_gdf, shp_full_paths_out[i])

        return converted_path

    def _build_edges_nodes_gdfs(self, in_path: str, out_path: str) -> str:
        """
        Builds the nodes and edges geoDataFrames for each roads geoDataFrame saved in in_path
        :param in_path: Path in which the roads geoDataFrame is saved
        :param out_path: Path in which the nodes and edges GeoDataFrames will be saved
        :return: Path in which all the nodes and edges geoDataFrames are saved
        """
        connected_path = create_file_path((out_path + "/connected"))
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
            create_file_path(shp_full_paths_out[i])
            self.builder.build_nodes_and_edges_gdf(std_gdf, shp_full_paths_out[i], node_tag=prefix)
            prefix = chr(ord(prefix) + 1)

        return connected_path

    def _connect_edges_and_nodes_gdfs(self, in_path: str, out_path: str) -> str:
        """
        Merges/connects the nodes and edges geoDataFrame into a single GeoDataFrame.
        :param in_path: Path in which the all nodes and edges GeoDataFrames are saved
        :param out_path: Path to save the single combined GeoDataFrame
        :return: Path in which the single combined GeoDataFrame is saved
        """
        list_of_files = os.listdir(in_path)
        shp_full_paths_in = [in_path + "/" + x for x in list_of_files if not x.startswith(".")]
        final_path = create_file_path(out_path + "/final")

        n = len(shp_full_paths_in)
        gdf_edges = gpd.read_file(shp_full_paths_in[0] + "/edges.shp")
        gdf_nodes = gpd.read_file(shp_full_paths_in[0] + "/nodes.shp")
        print(f"{shp_full_paths_in[0]}")
        for i in range(1, n):
            print("iteration: " + str(i + 1) + " out of " + str(n + 1))
            print(f"{shp_full_paths_in[i]}")
            aux_edges = gpd.read_file(shp_full_paths_in[i] + "/edges.shp")
            aux_nodes = gpd.read_file(shp_full_paths_in[i] + "/nodes.shp")
            gdf_edges, gdf_nodes = self.connector.connect_two_nodeEdges_std_gdfs(gdf_edges, gdf_nodes,
                                                                                 aux_edges, aux_nodes)

        gdf_edges.to_file(final_path + "/edges.shp")
        gdf_nodes.to_file(final_path + "/nodes.shp")

        return final_path


    def merge_road_segments(self, edges_gdf: gpd.GeoDataFrame, edge_index: int) -> (dict, int):
        """
        Merges all linked road segments and condense information into a dict
        :param edge_index: index of starting road segment
        :param edges_gdf: Linked Road segments geodataframe
        :return: d: a dictionary the total length, indices and unique road IDs of the edge
                final_node: final node that this road connects to
        """
        d = {}
        kph_to_mps_factor = 1000.0/3600.0
        current_segment = edges_gdf.loc[edges_gdf[STD_INDEX] == edge_index]
        current_segment = current_segment.iloc[0]
        length = current_segment[STD_LENGTH]
        time = length/(current_segment[STD_SPEED]*kph_to_mps_factor)
        road_segment_index = [edge_index]
        road_id = current_segment[STD_ROAD_NO] + "_" + current_segment[STD_ROAD_TYPE]

        if current_segment[STD_IS_SRN] == 1:
            is_srn = True
        else:
            is_srn = False

        while not pd.isna(current_segment[STD_NEXT_IND]):
            current_segment = edges_gdf.loc[edges_gdf[STD_INDEX] == int(current_segment[STD_NEXT_IND])]
            current_segment = current_segment.iloc[0]
            length += current_segment[STD_LENGTH]
            time += current_segment[STD_LENGTH]/(current_segment[STD_SPEED]*kph_to_mps_factor)
            road_segment_index.extend([current_segment[STD_INDEX]])

            if current_segment[STD_IS_SRN] == 1:
                is_srn = True

        final_node = current_segment[STD_TO_NODE]
        d[STD_Nx_ROAD_ID] = road_id
        d[STD_Nx_LENGTH] = length
        d[STD_Nx_TIME] = time
        d[STD_Nx_ROAD_IND] = road_segment_index
        d[STD_Nx_IS_SRN] = is_srn

        return d, final_node

    def create_graph(self, nodes_gdf, edges_gdf, weight_type: str = 'Time'):
        """
        Creates a graph NetworkX object using roads_gdf and edges_gdf
        :param edges_gdf: geodataframe of roads
        :param nodes_gdf: geodataframe of nodes
        :param weight_type: type of weight to be used for the edges, either 'Time' or 'Length'
        :return: net: A networkX object representing road network.
        """
        print("Creating Graph")

        net = nx.DiGraph()
        # for each slip road and roundabout node dataframe do:
        for _, node in nodes_gdf.iterrows():
            coords = node[STD_GEOMETRY]
            net.add_node(node.node_id, coordinates=coords)

        start_segments = edges_gdf.loc[(edges_gdf[STD_ROAD_TYPE] == STD_MAIN_CARRIAGEWAY) |
                                       (edges_gdf[STD_ROAD_TYPE] == STD_SLIP_ROAD)]

        start_segments = start_segments.loc[pd.isna(edges_gdf[STD_PREV_IND])]
        n = 1

        for index, start_segment in start_segments.iterrows():
            print(index)
            segment_index = start_segment[STD_INDEX]
            from_node = start_segment[STD_FROM_NODE]
            attr, to_node = self.merge_road_segments(edges_gdf, segment_index)
            weight = attr[STD_Nx_TIME] if weight_type == "Time" else attr[STD_Nx_LENGTH]

            net.add_edge(from_node, to_node, attr=attr, weight=weight)
            if not start_segment[STD_IS_DIREC]:
                net.add_edge(to_node, from_node, attr=attr, weight=weight)

        print("Finished Graph")

        return net

    def _extract_shp_names(self, file_path: str):
        """
        Extracts all shp files from file_path
        :param file_path: target path to extract shp files
        :return: Either a list of all shp file names, or a single shp file name
        """
        list_of_files = os.listdir(file_path)
        shp_tags = [x for x in list_of_files if ".shp" in x]

        if len(shp_tags) == 1:
            return shp_tags[0]
        else:
            return shp_tags

