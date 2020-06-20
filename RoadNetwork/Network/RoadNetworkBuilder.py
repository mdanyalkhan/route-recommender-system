import pickle
import networkx as nx
from RoadNetwork.Network.HENodesAndEdgesBuilder import *
from RoadNetwork.Network.OSNodesAndEdgesBuilder import *
from RoadNetwork.Network.NodesAndEdgesMerger import *
from RoadNetwork.Conversion.OSToStdConverter import *
from RoadNetwork.Utilities.ColumnNames import *


class RoadNetworkBuilder:

    def __init__(self, base_builder: NodesAndEdgesBuilder = HENodesAndEdgesBuilder(),
                 aux_builder: NodesAndEdgesBuilder = OSNodesAndEdgesBuilder(),
                 base_converter: ToStdConverter = None,
                 aux_converter: ToStdConverter = OSToToStdConverter(),
                 merger: NodesAndEdgesMerger =NodesAndEdgesMerger()):

        self.aux_converter = aux_converter
        self.base_converter = base_converter
        self.base_builder = base_builder
        self.aux_builder = aux_builder
        self.merger = merger

    def build_network(self, base_path: str, aux_path: str, is_base_conversion_required: bool,
                      is_aux_conversion_required: bool, is_base_directional=True,
                      is_aux_directional=False) -> nx.Graph:
        """
        Builds a networkx digraph object using a geodataframe saved in base_path as a basis, and auxiliary geodataframe
        that a user wants attached. Note that this method saves the geodataframe at different stages before being
        fully converted into a Networkx object. This includes:

        1. A nodes and edges geodataframe of the base geodataframe.
        2. All nodes and edges geodataframes of auxiliary dataframes in the aux_path.
        3. Nodes and edges geodataframe where both base and auxiliary geodataframes are merged.
        4. Optionally (if conversion is required):
            a. Standardised dataframe of base dataframe
            b. Standardised dataframes of all auxiliary dataframes.
        5. Networkx digraph pickle file

        :param base_path: Folder path of the base geodataframe
        :param aux_path: Folder path containing all auxiliary geodataframes
        :param is_base_conversion_required: Boolean, self-explanatory
        :param is_aux_conversion_required: Boolean, self-explanatory
        :param is_base_directional: Boolean, self-explanatory
        :param is_aux_directional: Boolean, self-explanatory
        :return: Networkx digraph of road network
        """
        out_path = self._create_file_path(os.path.dirname(base_path) + "/out")

        base_net_path = self._build_base_net_gdf(base_path, out_path, is_base_conversion_required, is_base_directional)
        aux_net_path = self._build_aux_net_gdf(aux_path, out_path, is_aux_conversion_required, is_aux_directional)
        final_path = self._merge_all_aux_gdfs_to_base(base_net_path, aux_net_path, out_path)

        return self.create_graph(final_path)

    def _build_base_net_gdf(self, base_path: str, out_path: str, is_base_conversion_required: bool,
                            is_base_directional: bool) -> str:
        """
        Builds nodes and edges geodataframe using the base geodataframe
        :param base_path: file path of base geodataframe
        :param out_path: File path where nodes and edges geodataframe are to be saved
        :param is_base_conversion_required: Boolean, self-explanatory
        :param is_base_directional: Boolean, self-explanatory
        :return: Folder path containing nodes and edge geodataframes
        """
        base_name = self._extract_shp_names(base_path)
        base_out_path = self._create_file_path(out_path + "/base")
        base_gdf = gpd.read_file(base_path)

        if is_base_conversion_required:
            base_gdf = self.base_converter.convert_to_std_gdf(base_gdf)
            base_out_converted_path = self._create_file_path(base_out_path + "/" + "converted")
            base_gdf.to_file(base_out_converted_path + "/" + base_name)

        base_edge_gdf, base_node_gdf = self.base_builder.build_nodes_and_edges(base_gdf, is_base_directional, "base")
        base_out_connnected_path = self._create_file_path(base_out_path + "/" "connected")
        base_edge_gdf.to_file(base_out_connnected_path + "/" + "edges.shp")
        base_node_gdf.to_file(base_out_connnected_path + "/" + "nodes.shp")

        return base_out_connnected_path

    def _build_aux_net_gdf(self, aux_path, out_path, is_aux_conversion_required, is_aux_directional):

        aux_in_path = aux_path
        aux_names = self._extract_shp_names(aux_path)
        aux_out_connected_path = self._create_file_path(out_path + "/aux")

        if is_aux_conversion_required:
            aux_in_path = self._create_file_path(aux_out_connected_path + "/converted")
            self.aux_converter.convert_multiple_to_std_gdfs(aux_path, aux_in_path)

        aux_out_connected_path = self._create_file_path(aux_out_connected_path + "/connected")
        self._build_multiple_networks_from_aux(aux_in_path, aux_out_connected_path, is_aux_directional)

        return aux_out_connected_path

    def _build_multiple_networks_from_aux(self, in_path, out_path, is_directional):

        list_of_files = os.listdir(in_path)
        shp_tags = [x.split("_")[0] for x in list_of_files if ".shp" in x]
        shp_full_paths_in = [in_path + "/" + x for x in list_of_files if ".shp" in x]
        shp_full_paths_out = [out_path + "/" + x.split("_")[0] for x in list_of_files if ".shp" in x]

        n = len(shp_full_paths_in)

        for i in range(n):
            print("iteration: " + str(i + 1) + " out of " + str(n + 1))
            os_gdf = gpd.read_file(shp_full_paths_in[i])
            edge_gdf, node_gdf = self.aux_builder.build_nodes_and_edges(os_gdf, is_directional=is_directional,
                                                                        node_tag=shp_tags[i])
            if not os.path.exists(shp_full_paths_out[i]):
                os.makedirs(shp_full_paths_out[i])
            edge_gdf.to_file(shp_full_paths_out[i] + "/" + shp_tags[i] + "_edges.shp")
            node_gdf.to_file(shp_full_paths_out[i] + "/" + shp_tags[i] + "_nodes.shp")

    def _merge_all_aux_gdfs_to_base(self, base_path, aux_path, out_path):

        base_e = gpd.read_file(base_path + "/edges.shp")
        base_n = gpd.read_file(base_path + "/nodes.shp")
        final_path = self._create_file_path(out_path + "/" + "final")
        final_path_gdf = self._create_file_path(final_path + "/" + "gdf")
        aux_folders = [directory for directory in os.listdir(aux_path) if not directory.startswith('.')]

        for folder in aux_folders:
            print("Running through: ", folder)
            aux_e = gpd.read_file(aux_path + "/" + folder + "/" + folder + "_edges.shp")
            aux_n = gpd.read_file(aux_path + "/" + folder + "/" + folder + "_nodes.shp")
            base_e, base_n = self.merger.merge_two_network_gdfs(base_e, base_n, aux_e, aux_n)

        base_e.to_file(final_path_gdf + "/edges.shp")
        base_n.to_file(final_path_gdf + "/nodes.shp")

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

        current_segment = roads_df.loc[roads_df["INDEX"] == road_index]
        current_segment = current_segment.iloc[0]

        coords = extract_list_of_coords_from_geom_object(current_segment.geometry)
        length = current_segment.SEC_LENGTH
        road_segment_index = [road_index]

        if pd.isna(current_segment.DIREC_CODE):
            road_id = current_segment.ROA_NUMBER + "_bi_" + current_segment.FUNCT_NAME
        else:
            road_id = current_segment.ROA_NUMBER + "_" + current_segment.DIREC_CODE + "_" + current_segment.FUNCT_NAME

        while not pd.isna(current_segment.NEXT_IND):
            current_segment = roads_df.loc[roads_df[INDEX] == int(current_segment.NEXT_IND)]
            current_segment = current_segment.iloc[0]
            coords += extract_list_of_coords_from_geom_object(current_segment.geometry)
            length += current_segment.SEC_LENGTH
            road_segment_index.extend([current_segment.INDEX])

        final_node = current_segment.TO_NODE
        d["ROAD_ID"] = road_id
        d["LENGTH"] = length
        d["road_segment_index"] = road_segment_index
        d["geometry"] = coords

        return d, final_node

    def create_graph(self, in_path):
        """
        Creates a graph NetworkX object using roads_gdf and nodes_gdf
        :param edges_gdf: geodataframe of roads
        :param nodes_gdf: geodataframe of nodes
        :return: net: A networkX object representing road network.
        """
        print("Creating Graph")
        edges_gdf = gpd.read_file(in_path + "/" + "gdf/edges.shp")
        nodes_gdf = gpd.read_file(in_path + "/" + "gdf/nodes.shp")

        net = nx.DiGraph()
        # for each slip road and roundabout node dataframe do:
        for _, node in nodes_gdf.iterrows():
            net.add_node(node.node_id, coordinates=node.geometry)

        start_segments = edges_gdf.loc[(edges_gdf["FUNCT_NAME"] == "Main Carriageway") |
                                       (edges_gdf["FUNCT_NAME"] == "Slip Road")]

        start_segments = start_segments.loc[pd.isna(edges_gdf["PREV_IND"])]

        for _, start_segment in start_segments.iterrows():
            segment_index = start_segment.INDEX
            from_node = start_segment.FROM_NODE
            attr, to_node = self.merge_road_segments(edges_gdf, segment_index)
            net.add_edge(from_node, to_node, attr=attr)
            if not start_segment.IS_DIREC:
                net.add_edge(to_node, from_node, attr=attr)

        print("Finished Graph")

        target_path = self._create_file_path(in_path + "/netx")
        target_file = target_path + "/roadGraph.pickle"

        with open(target_file, 'wb') as target:
            pickle.dump(net, target)

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
