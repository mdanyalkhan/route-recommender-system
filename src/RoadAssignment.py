import src.util as util
import numpy as np
import pandas as pd
import math
import logging
from scipy import spatial
from collections import defaultdict


class RoadAssignment:

    def __init__(self):
        self.road_threshold = 0.25

    def assign_entity(self, clusters_df, all_locations):
        """ Add a column road that contains the closest entity to the ping
        :param clusters_df:
        :param all_locations:
        :return: clusters_df with a additional column "road"
        """

        ind = defaultdict(list)

        for i, loc, lat, lon, section in zip(all_locations.index.values, all_locations.road, all_locations.latitude,
                                             all_locations.longitude, all_locations.section):
            ind[i].append(loc)
            ind[i].append(lat)
            ind[i].append(lon)
            ind[i].append(section)

        combined_x_y_arrays = np.dstack([all_locations.latitude.ravel(), all_locations.longitude.ravel()])[0]

        #  making a tree
        mytree = spatial.cKDTree(combined_x_y_arrays)

        # grab the starting points that are the from_depots
        df_start = clusters_df.copy()

        # getting our points we want to label in the correct shape
        start_points = np.array(list(zip(df_start.Event_Lat, df_start.Event_Long)))

        start_dist, start_indices = mytree.query(start_points, n_jobs=-1)

        clusters_df.loc[df_start.index.values, "dist_to_nearest_road"] = start_dist
        clusters_df.loc[df_start.index.values, "loc_index_start"] = start_indices

        clusters_df.loc[:, "road"] = clusters_df.loc_index_start.map(ind)

        clusters = clusters_df.copy()

        clusters['road_number'] = clusters.apply(self.add_road, axis=1)
        clusters['latitude'] = clusters.apply(self.add_lat, axis=1)
        clusters['longitude'] = clusters.apply(self.add_lon, axis=1)
        section_col = clusters.apply(self.add_section, axis=1)

        clusters["distance_from"] = util.haversine_np(clusters.loc[:, 'Event_Long'], clusters.loc[:, 'Event_Lat'],
                                                      clusters.loc[:, 'longitude'], clusters.loc[:, 'latitude'])

        clusters.drop('road', axis=1, inplace=True)

        clusters.rename({'road_number': 'road'}, axis=1, inplace=True)

        clusters['road'] = np.where(clusters['distance_from'] <= self.road_threshold, clusters['road'],
                                    'unknown')

        clusters[cn.ROAD_TYPE] = clusters.apply(util.add_entity_type, axis=1)

        clusters['section'] = section_col

        # Remove unnecessary columns
        clusters = clusters.drop(['dist_to_nearest_road', 'loc_index_start', 'latitude', 'longitude', 'distance_from'],
                                 axis=1)

        return clusters

    def sort_junctions(self, row):
        """
        :param row: a row that contains JXX-JXX
        :return: sorted JXX-JXX
        """

        i = row["section"]
        junct = []

        if type(i) == float and math.isnan(i):
            return i
        else:
            first = i.split('-', 1)[0]
            second = i.split('-', 1)[1]
            junct.append(first)
            junct.append(second)
            junct = util.sort_list(junct)

        return "-".join(junct)

    def sort_section_column(self, df):
        """
        The function is used to sort the junctions in the section column (J15-J14 would become J14-J15)
        :param df:
        :return:
        """

        df["section"] = df.apply(self.sort_junctions, axis=1)

        return df

    def clean_intersection(self, row):
        if row['road_before'] == row['road_after']:
            res = row['road_before']
        # Filter one single ping is detected from an A-road (unlikely to happen-Truck on A roads are slow)
        elif row['road_before'] != row['road'] and row['road'] != row['road_after'] and row['road_type'] == "A-road":
            res = "to_filter"
        else:
            res = row['road']
        return res

    def cleaning_classification_impurities(self, clusters_df):
        """
        Function that uses logic in order to clean unexpected classification
        :param clusters_df:
        :return:
        """
        # Add the shifted columns to remove the points on intersections
        clusters_df["road_before"] = clusters_df.road.shift(1)
        clusters_df["road_after"] = clusters_df.road.shift(-1)

        clusters_df.road = clusters_df.apply(self.clean_intersection, axis=1)
        clusters_df = clusters_df[clusters_df.road != 'to_filter']
        # TODO - check what effect this has on our data
        # TODO - if we have a canonical example of a cluster, ca
        clusters_df = clusters_df[clusters_df.road != 'unknown']

        clusters_df = clusters_df.drop(["road_before", "road_after"], axis=1)

        clusters_df = self.sort_section_column(clusters_df)

        return clusters_df

    def add_road(self, r):
        res = r['road'][0]
        return res

    def add_lat(self, r):
        res = r['road'][1]
        return res

    def add_lon(self, r):
        res = r['road'][2]
        return res

    def add_section(self, r):
        res = r['road'][3]
        return res
