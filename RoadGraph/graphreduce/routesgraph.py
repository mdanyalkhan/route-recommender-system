from collections import Counter
import pandas as pd
import geopandas as gpd
import RoadGraph.constants.StdColNames as cn
import RoadGraph.constants.StdKeyWords as kw
from RoadGraph import StdRoadGraph, StdRoadGraphBuilder
import pickle

LEG_ID = "leg_id"
CLUSTER = "cluster"
CLUSTER_ID = 'cluster_id'
FROM_DEPOT = 'from_depot'
TO_DEPOT = 'to_depot'
EVENT_DTTM = "Event_Dttm"
NEAREST_NODE = 'nearest_node'
NODE_ROUTE_LIST = 'node_route_list'
START_TIME = 'start_time'
END_TIME = 'end_time'


class RoutesGraph:
    def __init__(self):
        self.frac_to_appear_in = 0.2

    def generate_stdRoadGraph_from_isotrack(self, isotrack_data: pd.DataFrame, road_graph: StdRoadGraph, out_path=None):
        shp_map = self.generate_gdfs_for_each_cluster(isotrack_data, road_graph)

        nodes_merged = gpd.GeoDataFrame()
        edges_merged = gpd.GeoDataFrame()

        for cluster_id in shp_map:
            edges_merged = pd.concat([shp_map[cluster_id][0], edges_merged])
            nodes_merged = pd.concat([shp_map[cluster_id][1], nodes_merged])

        edges_merged = edges_merged[~edges_merged.index.duplicated(keep='first')]
        nodes_merged = nodes_merged[~nodes_merged.index.duplicated(keep='first')]
        net = StdRoadGraphBuilder().create_graph(nodes_merged, edges_merged)
        edges_merged, net = self._remove_redundant_roundabout_edges(edges_merged, nodes_merged, net)

        if out_path:
            edges_merged.to_file(f"{out_path}/edges.shp")
            nodes_merged.to_file(f"{out_path}/nodes.shp")
            with open(f"{out_path}/route_graph.pickle", 'wb') as target:
                pickle.dump(net, target)

        return StdRoadGraph(net, nodes_merged, edges_merged)

    def _remove_redundant_roundabout_edges(self, edges_merged, nodes_merged, net):
        roundabout_nodes = nodes_merged.loc[nodes_merged[cn.STD_N_TYPE] == kw.STD_N_ROUNDABOUT]
        edges_merged['marked'] = False
        node_pairs_to_del = []

        for _, roundabout_node in roundabout_nodes.iterrows():
            node_id = roundabout_node[cn.STD_NODE_ID]
            #Create empty list of second node candidate
            second_node_cand = []
            first_neighbours = list(net.successors(node_id))
            #For every neighbour of roundabout node
            for first_neighbour in first_neighbours:
                #If number of indices is 1
                indices = net[node_id][first_neighbour][cn.STD_Nx_ATTR][cn.STD_Nx_ROAD_IND]
                if len(indices) == 1:
                    #If number of neighbours of neighbour is two:
                    sec_neighbours = list(net.successors(first_neighbour))
                    if len(sec_neighbours) == 2:
                        #For every neighbour of neighbour that is not a roundabout node:
                        for sec_neighbour in sec_neighbours:
                            #If number of indices is 1
                            sec_indices = net[first_neighbour][sec_neighbour][cn.STD_Nx_ATTR][cn.STD_Nx_ROAD_IND]
                            if len(sec_indices) == 1:
                                #Add neighbour into your candidate second node list
                                second_node_cand += [sec_neighbour]

            #For every neighbour of roundaboute node
            for first_neighbour in first_neighbours:
                indices = net[node_id][first_neighbour][cn.STD_Nx_ATTR][cn.STD_Nx_ROAD_IND]
                #If neighbour of roundabout node in candidate list:
                if first_neighbour in second_node_cand and len(indices) == 1:
                    #mark edge for deletion
                    edges_merged.loc[edges_merged[cn.STD_INDEX] == indices[0], 'marked'] = True
                    #record node pairs, for deletion in net
                    node_pairs_to_del += [(node_id, first_neighbour)]

        #Delete marked edges
        edges_merged.drop(edges_merged[edges_merged.marked == True].index, inplace=True)
        edges_merged.drop('marked', axis=1, inplace=True)

        #Delete marked edges in net
        for node_pairs in node_pairs_to_del:
            net.remove_edge(node_pairs[0], node_pairs[1])
            net.remove_edge(node_pairs[1], node_pairs[0])

        return edges_merged, net

    def generate_gdfs_for_each_cluster(self, isotrack_data: pd.DataFrame, road_graph: StdRoadGraph):

        cluster_route_map = self.generate_node_routes(isotrack_data, road_graph)
        shp_map = {}

        for cluster_id in cluster_route_map:
            edges, nodes = road_graph.convert_path_to_gdfs(cluster_route_map[cluster_id])
            edges = edges[~edges.index.duplicated(keep='first')]
            nodes = nodes[~nodes.index.duplicated(keep='first')]
            shp_map[cluster_id] = (edges, nodes)
        return shp_map

    def generate_node_routes(self, isotrack_data: pd.DataFrame, road_graph: StdRoadGraph):
        isotrack_grouped = self._get_grouped_df(isotrack_data)
        cluster_map = self._assign_raw_node_route_for_each_cluster(isotrack_data, isotrack_grouped)
        cluster_route_map = self._assign_final_node_route_for_each_cluster(cluster_map, road_graph)

        return cluster_route_map

    def _assign_raw_node_route_for_each_cluster(self, isotrack_data, isotrack_grouped):
        cluster_map = {}
        cluster_ids = isotrack_data[CLUSTER].unique()
        for cluster_id in cluster_ids:

            df_temp = isotrack_data[isotrack_data[CLUSTER] == cluster_id]
            df_grouped_temp = isotrack_grouped[isotrack_grouped[CLUSTER] == cluster_id]

            # If we only have one or two members in cluster, then don't bother with the long process below
            # If one, just take this entity list
            if len(df_grouped_temp) == 1:
                cluster_map[cluster_id] = df_grouped_temp[NODE_ROUTE_LIST].values[0]

            # If two, take the longer one on the basis it has more information.
            elif len(df_grouped_temp) == 2:
                cluster_map[cluster_id] = self._get_best_of_two(df_grouped_temp)
            else:
                cluster_map[cluster_id] = self._get_cluster_entity_mapping(df_temp, df_grouped_temp)
        return cluster_map

    def _assign_final_node_route_for_each_cluster(self, cluster_map: dict, road_graph: StdRoadGraph):

        cluster_route_map = {}
        for cluster_id in cluster_map:

            old_node_route = cluster_map[cluster_id]
            new_node_route = [old_node_route[0]]

            for i in range(len(old_node_route) - 1):
                source_node = old_node_route[i]
                target_node = old_node_route[i + 1]
                path, _ = road_graph.shortest_path_between_nodes(source_node, target_node)
                new_node_route += path[1:]

            cluster_route_map[cluster_id] = new_node_route

        return cluster_route_map

    def _get_grouped_df(self, df):
        """
        Grouping so that each row is one leg_id whilst keeping the order of entities and min max dttm for that leg
        :param df:
        :return:
        """
        df_grouped = df.groupby([LEG_ID, CLUSTER, FROM_DEPOT, TO_DEPOT]).agg(
            {EVENT_DTTM: ["min", "max"], NEAREST_NODE: list}).reset_index()

        df_grouped.columns = [LEG_ID, CLUSTER, FROM_DEPOT, TO_DEPOT, START_TIME, END_TIME, NEAREST_NODE]
        df_grouped.loc[:, NODE_ROUTE_LIST] = df_grouped[NEAREST_NODE].apply(lambda x: self._unique(x))
        del df_grouped[NEAREST_NODE]

        return df_grouped

    def _unique(self, sequence):
        seen = set()
        return [x for x in sequence if not (x in seen or seen.add(x))]

    def _get_best_of_two(self, df):
        e_1 = df.iloc[0][NODE_ROUTE_LIST]
        e_2 = df.iloc[1][NODE_ROUTE_LIST]

        if len(e_1) > len(e_2):
            return list(e_1)
        else:
            return list(e_2)

    def _get_cluster_entity_mapping(self, df_temp, df_grouped_temp):
        """
        Takes in a df of one row per leg_id with a cluster and list of entities for each leg. Returns the same data but
        with just one list of entities representing each cluster
        :param df_temp: df that has been grouped so one row is one leg_id
        :param df_grouped_temp: df that has been grouped so one row is one leg_id
        :return: df with reduced entity_list applied
        """

        min_count_to_include = self._get_min_count(df_temp)
        node_counter = self._get_node_counter(df_temp)
        most_visited_nodes = self._get_most_visited_node_routes(min_count_to_include, node_counter)
        master_list = self._get_best_node_route_list(df_grouped_temp, most_visited_nodes)

        # Turn our entity lists into an actual list of list of entities
        list_of_list_of_node_routes = self._get_list_of_list_of_node_routes(df_grouped_temp, most_visited_nodes)

        master_list = self._get_master_list(list_of_list_of_node_routes, master_list, most_visited_nodes)

        return master_list

    def _get_min_count(self, df):
        """
        For each cluster in a pair of from/to sites and their corresponding leg_ids, we need to know how many of these
        leg_ids an entity must appear in for us to consider that this entity really is a part of the cluster.
        :param df: Dataframe which has already been subset to only one cluster in a to/from pair
        :return: integer which is the number of legs that an entity must appear in to be considered really travelled
        """
        n_leg_ids = df[LEG_ID].nunique()
        return int((n_leg_ids + 1) * self.frac_to_appear_in)

    def _get_node_counter(self, df):
        """
        Takes ALL the entities that are traversed by all legs in a cluster and counts the number of legs the appear in
        :param df: df that is of only one cluster between sites. ALL PINGS INCLUDED.
        :return: Counter object of all the entities. One count per leg_id appearance (not ping appearance)
        """
        node_routes = []
        for leg_id in df[LEG_ID].unique():
            df_leg = df[df[LEG_ID] == leg_id]
            node_routes += list(set(df_leg[NEAREST_NODE]))
        return Counter(node_routes)

    def _get_most_visited_node_routes(self, min_count_to_include, node_pair_counter):
        """
        Returns a list of the most visited entities
        :param min_count_to_include: minimum number of legs that an entity must appear in to be considered travelled
        :param entities_counter: Counter object of all the entities travelled by the legs in this cluster
        :return: list of entities that all appear at least min_count_to_include times
        """
        return [x for x in node_pair_counter if node_pair_counter[x] >= min_count_to_include]

    def _get_best_node_route_list(self, df, nodes_to_include):
        """
        Takes a dataframe of all the legs in a cluster, and returns the list of entities from the leg_id that has the most
        entities in our list of entities that appear enough to be considered to have really been traversed
        :param df: dataframe of one row per leg_id with list of entities, subset to one cluster
        :param entities_to_include: list of entities that appear in at least min_frac_to_include of leg_ids for this cluster
        :return: list of entities from this cluster that has the most entities that appear in our list of travelled entities
        """
        max_ratio_present = 0
        best_node_routes_list = []
        for row in df.itertuples():
            node_routes_present = [node for node in row.node_route_list if node in nodes_to_include]
            ratio_present = len(node_routes_present) / len(nodes_to_include)
            if ratio_present > max_ratio_present:
                max_ratio_present = ratio_present
                best_node_routes_list = list(row.node_route_list)
            if max_ratio_present == 1:
                # We've seen all of the entities in our cluster present in this one leg_id so stop
                break
        return best_node_routes_list

    def _get_list_of_list_of_node_routes(self, df, most_visited_nodes):
        """
          Takes in our df of only one cluster and returns a list of list of entities from it
          :param df: df subset to one cluster
          :param most_visited_entities: list of the most visited entities
          :return: list of lists, each list is the entity list from one leg_id
          """
        list_of_list_node_routes = []
        for row in df.itertuples():
            single_node_route_list = [x for x in row.node_route_list if x in most_visited_nodes]
            list_of_list_node_routes.append(single_node_route_list)
        return list_of_list_node_routes

    def _get_master_list(self, list_of_list_of_node_routes, master_list, most_visited_nodes):
        """
        Takes in the list of entities that has the most entities in the list of most visited entities. It then improves it
        by looking at all other entities in the cluster
        :param list_of_list_of_entities:
        :param master_list:
        :param most_visited_entities:
        :return: master_list - the best bet of our entities
        """
        for list_of_node_routes in list_of_list_of_node_routes:

            # find those present in each list that are not present in master list
            nodes_not_in_master_list = [node for node in list_of_node_routes if
                                             node not in master_list]

            # Loop through things to add and find index
            for node_routes_to_insert in nodes_not_in_master_list:

                i = list_of_node_routes.index(node_routes_to_insert)

                # Find the items before and after
                if (i > 0) & (i < len(list_of_node_routes) - 1):
                    before, after = list_of_node_routes[i - 1], list_of_node_routes[i + 1]

                    # If both items before and after present, insert into list between these two
                    if (before in master_list) & (after in master_list):
                        before_index = master_list.index(before)
                        after_index = master_list.index(after)
                        if after_index - before_index == 1:
                            master_list.insert(after_index, node_routes_to_insert)
            if len(master_list) == len(most_visited_nodes):
                return master_list
        return master_list
