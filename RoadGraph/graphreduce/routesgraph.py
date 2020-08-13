from collections import Counter
import pandas as pd
from RoadGraph import StdRoadGraph
from RoadGraph.constants.StdKeyWords import *
from RoadGraph.constants.StdColNames import *
import networkx as nx
import numpy as np

LEG_ID = "leg_id"
CLUSTER = "cluster"
CLUSTER_ID = 'cluster_id'
FROM_DEPOT = 'from_depot'
TO_DEPOT = 'to_depot'
EVENT_DTTM = "Event_Dttm"
NODE_PAIRS = 'node_pairs'
NODE_PAIRS_LIST = 'node_pairs_list'
START_TIME = 'start_time'
END_TIME = 'end_time'


class RoutesGraph:
    def __init__(self):
        self.frac_to_appear_in = 0.2

    def __int__(self):
        pass

    def generate_routes_graph(self, isotrack_data: pd.DataFrame, road_graph: StdRoadGraph):

        isotrack_grouped = self._get_grouped_df(isotrack_data)
        cluster_map = self._assign_node_pair_routes(isotrack_data, isotrack_grouped)
        cluster_route_map = self._assign_node_routes(cluster_map, road_graph)

        shp_map = {}

        for cluster_id in cluster_route_map:
            shp_map[cluster_id] = road_graph.convert_path_to_gdfs(cluster_route_map[cluster_id])

        return shp_map

    def _assign_node_pair_routes(self, isotrack_data, isotrack_grouped):
        cluster_map = {}
        cluster_ids = isotrack_data[CLUSTER].unique()
        for cluster_id in cluster_ids:

            df_temp = isotrack_data[isotrack_data[CLUSTER] == cluster_id]
            df_grouped_temp = isotrack_grouped[isotrack_grouped[CLUSTER] == cluster_id]

            # If we only have one or two members in cluster, then don't bother with the long process below
            # If one, just take this entity list
            if len(df_grouped_temp) == 1:

                cluster_map[cluster_id] = df_grouped_temp[NODE_PAIRS_LIST].values[0]

            # If two, take the longer one on the basis it has more information.
            elif len(df_grouped_temp) == 2:
                cluster_map[cluster_id] = self._get_best_of_two(df_grouped_temp)
            else:
                cluster_map[cluster_id] = self._get_cluster_entity_mapping(df_temp, df_grouped_temp)
        return cluster_map

    def _assign_node_routes(self, cluster_map: dict, road_graph: StdRoadGraph):

        cluster_route_map = {}
        for cluster_id in cluster_map:
            node_pairs = cluster_map[cluster_id]

            i = 0
            while i < len(node_pairs) - 1:
                if node_pairs[i] != node_pairs[i + 1]:
                    break
                i += 1

            if i == len(node_pairs) - 1:
                cluster_route_map[cluster_id] = [node for node in node_pairs[i]]
                continue

            first_path, first_dist = self._shortest_dist_to_next_node_pair(road_graph, node_pairs[i][0],
                                                                           node_pairs[i + 1])
            second_path, second_dist = self._shortest_dist_to_next_node_pair(road_graph, node_pairs[i][1],
                                                                             node_pairs[i + 1])

            node_route = [node_pairs[i][1]] + first_path if first_dist < second_dist else [node_pairs[i][0]] + second_path
            next_node = node_pairs[i + 1][0] if node_pairs[i + 1][1] == node_route[-1] else node_pairs[i + 1][1]

            for j in range(i+2, len(node_pairs)):
                path, _ = self._shortest_dist_to_next_node_pair(road_graph, next_node, node_pairs[j])
                node_route += path
                next_node = node_pairs[j][0] if node_pairs[j][1] == node_route[-1] else node_pairs[j][1]

            cluster_route_map[cluster_id] = node_route

        return cluster_route_map


    def _shortest_dist_to_next_node_pair(self, road_graph, source_node, target_nodes):

        first_path, first_dist = road_graph.shortest_path_between_nodes(source_node, target_nodes[0])
        second_path, second_dist = road_graph.shortest_path_between_nodes(source_node, target_nodes[1])

        return (first_path, first_dist) if first_dist < second_dist else (second_path, second_dist)

    def _get_grouped_df(self, df):
        """
        Grouping so that each row is one leg_id whilst keeping the order of entities and min max dttm for that leg
        :param df:
        :return:
        """
        df_grouped = df.groupby([LEG_ID, CLUSTER, FROM_DEPOT, TO_DEPOT]).agg(
            {EVENT_DTTM: ["min", "max"], NODE_PAIRS: list}).reset_index()
        df_grouped.columns = [LEG_ID, CLUSTER, FROM_DEPOT, TO_DEPOT, START_TIME, END_TIME, NODE_PAIRS]
        df_grouped.loc[:, NODE_PAIRS_LIST] = df_grouped[NODE_PAIRS].apply(lambda x: self._unique(x))
        del df_grouped[NODE_PAIRS]

        return df_grouped

    def _unique(self, sequence):
        seen = set()
        return [x for x in sequence if not (x in seen or seen.add(x))]

    def _get_best_of_two(self, df):
        e_1 = df.iloc[0][NODE_PAIRS_LIST]
        e_2 = df.iloc[1][NODE_PAIRS_LIST]

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
        node_pair_counter = self._get_node_pair_counter(df_temp)
        most_visited_node_pairs = self._get_most_visited_node_pairs(min_count_to_include, node_pair_counter)
        master_list = self._get_best_node_pair_list(df_grouped_temp, most_visited_node_pairs)

        # Turn our entity lists into an actual list of list of entities
        list_of_list_of_node_pairs = self._get_list_of_list_of_node_pairs(df_grouped_temp, most_visited_node_pairs)

        master_list = self._get_master_list(list_of_list_of_node_pairs, master_list, most_visited_node_pairs)

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

    def _get_node_pair_counter(self, df):
        """
        Takes ALL the entities that are traversed by all legs in a cluster and counts the number of legs the appear in
        :param df: df that is of only one cluster between sites. ALL PINGS INCLUDED.
        :return: Counter object of all the entities. One count per leg_id appearance (not ping appearance)
        """
        node_pairs = []
        for leg_id in df[LEG_ID].unique():
            df_leg = df[df[LEG_ID] == leg_id]
            node_pairs += list(set(df_leg[NODE_PAIRS]))
        return Counter(node_pairs)

    def _get_most_visited_node_pairs(self, min_count_to_include, node_pair_counter):
        """
        Returns a list of the most visited entities
        :param min_count_to_include: minimum number of legs that an entity must appear in to be considered travelled
        :param entities_counter: Counter object of all the entities travelled by the legs in this cluster
        :return: list of entities that all appear at least min_count_to_include times
        """
        return [x for x in node_pair_counter if node_pair_counter[x] >= min_count_to_include]

    def _get_best_node_pair_list(self, df, node_pairs_to_include):
        """
        Takes a dataframe of all the legs in a cluster, and returns the list of entities from the leg_id that has the most
        entities in our list of entities that appear enough to be considered to have really been traversed
        :param df: dataframe of one row per leg_id with list of entities, subset to one cluster
        :param entities_to_include: list of entities that appear in at least min_frac_to_include of leg_ids for this cluster
        :return: list of entities from this cluster that has the most entities that appear in our list of travelled entities
        """
        max_ratio_present = 0
        best_node_pair_list = []
        for row in df.itertuples():
            node_pairs_present = [node_pair for node_pair in row.node_pairs_list if node_pair in node_pairs_to_include]
            ratio_present = len(node_pairs_present) / len(node_pairs_to_include)
            if ratio_present > max_ratio_present:
                max_ratio_present = ratio_present
                best_node_pair_list = list(row.node_pairs_list)
            if max_ratio_present == 1:
                # We've seen all of the entities in our cluster present in this one leg_id so stop
                break
        return best_node_pair_list

    def _get_list_of_list_of_node_pairs(self, df, most_visited_node_pairs):
        """
          Takes in our df of only one cluster and returns a list of list of entities from it
          :param df: df subset to one cluster
          :param most_visited_entities: list of the most visited entities
          :return: list of lists, each list is the entity list from one leg_id
          """
        list_of_list_node_pairs = []
        for row in df.itertuples():
            single_node_pair_list = [x for x in row.node_pairs_list if x in most_visited_node_pairs]
            list_of_list_node_pairs.append(single_node_pair_list)
        return list_of_list_node_pairs

    def _get_master_list(self, list_of_list_of_node_pairs, master_list, most_visited_node_pairs):
        """
        Takes in the list of entities that has the most entities in the list of most visited entities. It then improves it
        by looking at all other entities in the cluster
        :param list_of_list_of_entities:
        :param master_list:
        :param most_visited_entities:
        :return: master_list - the best bet of our entities
        """
        for list_of_node_pairs in list_of_list_of_node_pairs:

            # find those present in each list that are not present in master list
            node_pairs_not_in_master_list = [node_pair for node_pair in list_of_node_pairs if
                                             node_pair not in master_list]

            # Loop through things to add and find index
            for node_pairs_to_insert in node_pairs_not_in_master_list:

                i = list_of_node_pairs.index(node_pairs_to_insert)

                # Find the items before and after
                if (i > 0) & (i < len(list_of_node_pairs) - 1):
                    before, after = list_of_node_pairs[i - 1], list_of_node_pairs[i + 1]

                    # If both items before and after present, insert into list between these two
                    if (before in master_list) & (after in master_list):
                        before_index = master_list.index(before)
                        after_index = master_list.index(after)
                        if after_index - before_index == 1:
                            master_list.insert(after_index, node_pairs_to_insert)
            if len(master_list) == len(most_visited_node_pairs):
                return master_list
        return master_list
