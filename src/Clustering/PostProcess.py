from src.Clustering.ColumnNames import ColumnNames as cn
import numpy as np
import pandas as pd
import math as maths
from tqdm import tqdm
from collections import Counter

class PostProcess(object):

    def __init__(self):
        self.frac_to_appear_in = 0.2

    def conduct_post_process(self, df: pd.DataFrame):
        df.loc[:, cn.ENTITY.value] = df.road.astype(str) + "/" + df.section.astype(str)
        df_grouped = self.get_grouped_df(df)
        df.loc[:, cn.CLUSTER_ID.value] = df.from_depot + df.to_depot + df.cluster.astype(str)
        df_grouped.loc[:, cn.CLUSTER_ID.value] = df_grouped.from_depot + df_grouped.to_depot + df_grouped.cluster.astype(str)

        df_result_list = []

        for cluster_id in tqdm(df[cn.CLUSTER_ID.value].unique(), total=df[cn.CLUSTER_ID.value].nunique()):

            df_temp = df[df[cn.CLUSTER_ID.value] == cluster_id]
            df_grouped_temp = df_grouped[df_grouped[cn.CLUSTER_ID.value] == cluster_id]

            # If we only have one or two members in cluster, then don't bother with the long process below
            # If one, just take this entity list
            if len(df_grouped_temp) == 1:
                result = df_temp
                # Adding this here as by definition each ping is representative and the df doesn't go through the
                # sorting function
                result.loc[:, cn.REPRESENTATIVE.value] = 1

            # If two, take the longer one on the basis it has more information.
            elif len(df_grouped_temp) == 2:
                master_list = self.get_best_of_two(df_grouped_temp)
                result = self.sort_filter_df_on_entities(df_temp, master_list)

            else:
                master_list = self.get_cluster_entity_mapping(df_temp, df_grouped_temp)
                result = self.sort_filter_df_on_entities(df_temp, master_list)

            df_result_list.append(result)
        final_df = pd.concat(df_result_list)
        final_df = self.get_runtime(final_df)
        final_df = self.get_runtime_stats(final_df)
        final_df = self.add_leg_id_count(final_df)

        final_df_len_before_filter = len(final_df)
        final_df = self.filter_df(final_df)
        filterdf = final_df[final_df[cn.OVERNIGHT.value] == 1]
        filterdf = self.add_leg_id_count_filter(self.get_runtime_stats_filter(filterdf))
        final_df = self.merge_df(final_df, filterdf)
        final_df_len_after_filter = len(final_df)
        assert final_df_len_before_filter == final_df_len_after_filter, "We have duplicated or removed records"

        return final_df

    def get_grouped_df(self, df):
        """
        Grouping so that each row is one leg_id whilst keeping the order of entities and min max dttm for that leg
        :param df:
        :return:
        """
        df_grouped = df.groupby([cn.LEG_ID.value, cn.CLUSTER.value, cn.FROM_DEPOT.value, cn.TO_DEPOT.value]).agg(
            {cn.EVENT_DTTM.value: ["min", "max"], cn.ENTITY.value: lambda x: " ".join(x).split(" ")}).reset_index()
        df_grouped.columns = [cn.LEG_ID.value, cn.CLUSTER.value, cn.FROM_DEPOT.value, cn.TO_DEPOT.value,
                              cn.START_TIME.value, cn.END_TIME.value,
                              cn.ENTITIES.value]
        df_grouped.loc[:, cn.ENTITY_LIST.value] = df_grouped[cn.ENTITIES.value].apply(lambda x: self.unique(x))
        del df_grouped[cn.ENTITIES.value]
        return df_grouped

    def unique(self, sequence):
        """
        Takes in a list, returns a list of unique items WHILST PRESERVING ORDER
        :param sequence: list of entities
        :return: list of entities without repeats
        """
        seen = set()
        return [x for x in sequence if not (x in seen or seen.add(x))]

    def get_best_of_two(self, df):
        """
        Takes a df with only two leg_ids in a cluster and returns the longer of the two lists of entities
        :param df: dataframe with two leg_ids in a cluster
        :return: list which is the longer of their two lists of entities
        """
        e_1 = df.iloc[0].entity_list
        e_2 = df.iloc[1].entity_list

        if len(e_1) > len(e_2):
            return list(e_1)
        else:
            return list(e_2)

    def get_min_count(self, df):
        """
        For each cluster in a pair of from/to sites and their corresponding leg_ids, we need to know how many of these
        leg_ids an entity must appear in for us to consider that this entity really is a part of the cluster.
        :param df: Dataframe which has already been subset to only one cluster in a to/from pair
        :return: integer which is the number of legs that an entity must appear in to be considered really travelled
        """
        n_leg_ids = df[cn.LEG_ID.value].nunique()
        return maths.ceil(n_leg_ids * self.frac_to_appear_in)

    def get_most_visited_entities(self, min_count_to_include, entities_counter):
        """
        Returns a list of the most visited entities
        :param min_count_to_include: minimum number of legs that an entity must appear in to be considered travelled
        :param entities_counter: Counter object of all the entities travelled by the legs in this cluster
        :return: list of entities that all appear at least min_count_to_include times
        """
        return [x for x in entities_counter if entities_counter[x] >= min_count_to_include]

    def get_entity_counter(self, df):
        """
        Takes ALL the entities that are traversed by all legs in a cluster and counts the number of legs the appear in
        :param df: df that is of only one cluster between sites. ALL PINGS INCLUDED.
        :return: Counter object of all the entities. One count per leg_id appearance (not ping appearance)
        """
        entities = []
        for leg_id in df[cn.LEG_ID.value].unique():
            df_leg = df[df[cn.LEG_ID.value] == leg_id]
            entities += list(set(df_leg[cn.ENTITY.value]))
        return Counter(entities)

    def get_best_entity_list(self, df, entities_to_include):
        """
        Takes a dataframe of all the legs in a cluster, and returns the list of entities from the leg_id that has the most
        entities in our list of entities that appear enough to be considered to have really been traversed
        :param df: dataframe of one row per leg_id with list of entities, subset to one cluster
        :param entities_to_include: list of entities that appear in at least min_frac_to_include of leg_ids for this cluster
        :return: list of entities from this cluster that has the most entities that appear in our list of travelled entities
        """
        max_ratio_present = 0
        best_entity_list = []
        for row in df.itertuples():
            entities_present = [road for road in row.entity_list if road in entities_to_include]
            ratio_present = len(entities_present) / len(entities_to_include)
            if ratio_present > max_ratio_present:
                max_ratio_present = ratio_present
                best_entity_list = list(row.entity_list)
            if max_ratio_present == 1:
                # We've seen all of the entities in our cluster present in this one leg_id so stop
                break
        return best_entity_list

    def get_list_of_list_of_entities(self, df, most_visited_entities):
        """
        Takes in our df of only one cluster and returns a list of list of entities from it
        :param df: df subset to one cluster
        :param most_visited_entities: list of the most visited entities
        :return: list of lists, each list is the entity list from one leg_id
        """
        list_of_list_of_entities = []
        for row in df.itertuples():
            single_entity_list = [x for x in row.entity_list if x in most_visited_entities]
            list_of_list_of_entities.append(single_entity_list)
        return list_of_list_of_entities

    def get_master_list(self, list_of_list_of_entities, master_list, most_visited_entities):
        """
        Takes in the list of entities that has the most entities in the list of most visited entities. It then improves it
        by looking at all other entities in the cluster
        :param list_of_list_of_entities:
        :param master_list:
        :param most_visited_entities:
        :return: master_list - the best bet of our entities
        """
        for list_of_entities in list_of_list_of_entities:

            # find those present in each list that are not present in master list
            entities_not_in_master_list = np.setdiff1d(list_of_entities, master_list)

            # Loop through things to add and find index
            for entity_to_insert in entities_not_in_master_list:

                i = list_of_entities.index(entity_to_insert)

                # Find the items before and after
                if (i > 0) & (i < len(list_of_entities) - 1):
                    before, after = list_of_entities[i - 1], list_of_entities[i + 1]

                    # If both items before and after present, insert into list between these two
                    if (before in master_list) & (after in master_list):
                        before_index = master_list.index(before)
                        after_index = master_list.index(after)
                        if after_index - before_index == 1:
                            master_list.insert(after_index, entity_to_insert)
            if len(master_list) == len(most_visited_entities):
                return master_list
        return master_list

    def sort_filter_df_on_entities(self, df, sorter):
        """
        Takes in a dataframe with a column "entity_list" and a list of ordered entities. Filters to only include the
        entity_list, and orders dataframe on this list. Uses some fancy pandas feature I don't know.
        :param df: all the pings, with the column entity_list
        :param sorter: ordered list of entities for sorting the dataframe on
        :return: df ordered by the order of entities in the list
        """
        df_present = df[df[cn.ENTITY.value].isin(sorter)]
        df_absent = df[~df[cn.ENTITY.value].isin(sorter)]

        if len(df_present) > 0:
            df_present.loc[:, cn.REPRESENTATIVE.value] = 1
        if len(df_absent) > 0:
            df_absent.loc[:, cn.REPRESENTATIVE.value] = 0

        df_present[cn.ENTITY.value] = df_present[cn.ENTITY.value].astype('category')

        df_present.entity.cat.set_categories(sorter, inplace=True)
        df_present.sort_values(cn.ENTITY.value, inplace=True)

        df = pd.concat([df_present, df_absent], sort=False)

        return df

    def get_cluster_entity_mapping(self, df_temp, df_grouped_temp):
        """
        Takes in a df of one row per leg_id with a cluster and list of entities for each leg. Returns the same data but
        with just one list of entities representing each cluster
        :param df_temp: df that has been grouped so one row is one leg_id
        :param df_grouped_temp: df that has been grouped so one row is one leg_id
        :return: df with reduced entity_list applied
        """

        min_count_to_include = self.get_min_count(df_temp)
        entities_counter = self.get_entity_counter(df_temp)
        most_visited_entities = self.get_most_visited_entities(min_count_to_include, entities_counter)
        master_list = self.get_best_entity_list(df_grouped_temp, most_visited_entities)

        # Turn our entity lists into an actual list of list of entities
        list_of_list_of_entities = self.get_list_of_list_of_entities(df_grouped_temp, most_visited_entities)

        master_list = self.get_master_list(list_of_list_of_entities, master_list, most_visited_entities)

        return master_list

    def get_runtime(self, df):
        """
        Creates a runtime column from Event_Dttm per leg_id time in decimal hours.
        :param df: Isotrak clustered Dataframe
        :return: dataframe with added runtime column
        """
        df_short = df[[cn.LEG_ID.value, cn.EVENT_DTTM.value]]
        df_grouped = df_short.groupby(cn.LEG_ID.value).agg({cn.EVENT_DTTM.value: ["min", "max"]}).reset_index()
        df_grouped.columns = [cn.LEG_ID.value, cn.START_TIME.value, cn.END_TIME.value]
        df_grouped.loc[:, cn.RUNTIME.value] = pd.to_datetime(df_grouped[cn.END_TIME.value]) - pd.to_datetime(
            df_grouped[cn.START_TIME.value])
        df_grouped.loc[:, cn.RUNTIME.value] = df_grouped[cn.RUNTIME.value].apply(lambda x: round(x.seconds / 3600, 2))
        df_merged = pd.merge(df, df_grouped, on=cn.LEG_ID.value, how='left')
        assert len(df_short) == len(df_merged), "we've lost some columns :o"

        return df_merged

    def decimal_to_time(self, x):
        """
        converts decimals to time
        :param x: float; decimal
        :return: string; time in HH:MM
        """
        hours = int(x)
        minutes = (x * 60) % 60
        # seconds = (x * 3600) % 60
        return "%02d:%02d" % (hours, minutes)

    def get_runtime_stats(self, df):
        """
        Compute runtime stats for the dataframe for all data
        :param df: Dataframe with cluster_id and runtime
        :return df: Dataframe with runtime stats per cluster using all data
        """
        df_short = df[[cn.CLUSTER_ID.value, cn.RUNTIME.value]]
        df_grouped = df_short.groupby(cn.CLUSTER_ID.value).agg(
            {cn.RUNTIME.value: ["min", "max", "mean", "median", "count"]}).reset_index()
        df_grouped.columns = [cn.CLUSTER_ID.value, cn.MIN_RUNTIME.value, cn.MAX_RUNTIME.value,
                              cn.MEAN_RUNTIME.value, cn.MEDIAN_RUNTIME.value,
                              cn.COUNT_RUNTIME.value]

        df_merged = pd.merge(df, df_grouped, on=cn.CLUSTER_ID.value, how='left')
        assert len(df_short) == len(df_merged), "we've lost some columns :o"
        for col in [cn.MAX_RUNTIME.value, cn.MIN_RUNTIME.value, cn.MEDIAN_RUNTIME.value, cn.MEAN_RUNTIME.value]:
            df_merged[col] = df_merged[col].apply(self.decimal_to_time)
        return df_merged

    def get_runtime_stats_filter(self, df):
        """
        Compute runtime stats for the dataframe with only the data in it from nighttime
        :param df: Dataframe with cluster_id and runtime
        :return df: Dataframe with runtime stats per cluster using nighttime data
        """
        df_short = df[[cn.CLUSTER_ID.value, cn.RUNTIME.value]]
        df_grouped = df_short.groupby(cn.CLUSTER_ID.value).agg(
            {cn.RUNTIME.value: ["min", "max", "mean", "median", "count"]}).reset_index()

        df_grouped.columns = [cn.CLUSTER_ID.value, cn.MIN_RUNTIME_FT.value, cn.MAX_RUNTIME_FT.value,
                              cn.MEAN_RUNTIME_FT.value, cn.MEDIAN_RUNTIME_FT.value,
                              cn.COUNT_RUNTIME_FT.value]

        df_merged = pd.merge(df, df_grouped, on=cn.CLUSTER_ID.value, how='left')
        assert len(df_short) == len(df_merged), "we've lost some columns :o"
        for col in [cn.MAX_RUNTIME_FT.value, cn.MIN_RUNTIME_FT.value,
                    cn.MEDIAN_RUNTIME_FT.value, cn.MEAN_RUNTIME_FT.value]:

            df_merged[col] = df_merged[col].apply(self.decimal_to_time)
        return df_merged

    def filter_df(self, df):
        """
        Takes in a dataframe with start_time column, finds the hour, and returns the dataframe with only those trips that
        left between 19:00 and 03:59
        :param df: dataframe with all the rows
        :return df: dataframe with only those rows between 19:00 and 03:59
        """
        df[cn.START_TIME.value] = pd.to_datetime(df[cn.START_TIME.value], infer_datetime_format=True)
        df[cn.HOUR_DEPARTED.value] = df[cn.START_TIME.value].dt.hour
        df[cn.OVERNIGHT.value] = np.where(((df[cn.HOUR_DEPARTED.value] >= 19) | (df[cn.HOUR_DEPARTED.value] < 4)), 1, 0)
        df[cn.UNIQUE.value] = range(0, len(df))
        return df

    def merge_df(self, df, dt):
        """
        Merges the filtered dataframe (overnight only) and the unfiltered dataframe (daytime)
        :param df: dataframe of all data with runtime columns per cluster
        :param dt: dataframe of only overnight data with runtime columns per cluster for just this filtered data
        :return df_merged: dataframe that had all of the data in it, with seperate runtime columns for overnight and daytime
        """
        df_merged = df.merge(dt[[cn.UNIQUE.value, cn.MIN_RUNTIME_FT.value,
                                 cn.MAX_RUNTIME_FT.value, cn.MEAN_RUNTIME_FT.value, cn.MEDIAN_RUNTIME_FT.value,
                                 cn.COUNT_RUNTIME_FT.value, cn.COUNT_LEG_ID_FT.value]], on=cn.UNIQUE.value, how='left')
        df_merged.drop([cn.UNIQUE.value], axis=1, inplace=True)
        df_merged[cn.RUNTIME.value] = df_merged[cn.RUNTIME.value].apply(self.decimal_to_time)
        return df_merged

    def add_leg_id_count(self, df):
        """
        Add a column of the count of leg_id in a cluster_id.
        :param df: Isotrak clustered dataframe
        :return: Dataframe with added count_leg_id column
        """
        df_short = df[[cn.CLUSTER_ID.value, cn.LEG_ID.value]]
        df_grouped = df_short.groupby(cn.CLUSTER_ID.value).agg({cn.LEG_ID.value: lambda x: x.nunique()}).reset_index()
        df_grouped.rename(columns={cn.LEG_ID.value: cn.COUNT_LEG_ID.value}, inplace=True)
        df_merged = pd.merge(df, df_grouped, on=cn.CLUSTER_ID.value, how='left')
        assert len(df_short) == len(df_merged), "we've lost some columns :o"
        return df_merged

    def add_leg_id_count_filter(self, df):
        """
        Add a column of the count of leg_id in a cluster_id for the filtered overnight dataframe
        :param df: Isotrak clustered dataframe
        :return: Dataframe with added count_leg_id column
        """
        df_short = df[[cn.CLUSTER_ID.value, cn.LEG_ID.value]]
        df_grouped = df_short.groupby(cn.CLUSTER_ID.value).agg({cn.LEG_ID.value: lambda x: x.nunique()}).reset_index()
        df_grouped.rename(columns={cn.LEG_ID.value: cn.COUNT_LEG_ID_FT.value}, inplace=True)
        df_merged = pd.merge(df, df_grouped, on=cn.CLUSTER_ID.value, how='left')
        assert len(df_short) == len(df_merged), "we've lost some columns :o"
        return df_merged