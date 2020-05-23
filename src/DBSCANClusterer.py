from src.DataParser import *
from tqdm import tqdm
import pandas as pd
import numpy as np
from collections import defaultdict
from sklearn.cluster import DBSCAN
from scipy.spatial.distance import directed_hausdorff


class DBSCANClusterer(object):
    def __init__(self, df: pd.DataFrame):
        self.data = df

    def createClusters(self, eps = 0.06, minSamples = 1, symm = False):
        routes: pd.DataFrame = self.__find_unique_routes()

        resultsList = []
        for row in tqdm(routes.itertuples(), total=routes.shape[0]):
            df_sub: pd.DataFrame = self.data[(self.data.from_depot == row.from_depot) &
                               (self.data.to_depot == row.to_depot)].copy()
            df_clustered = self.__cluster(df_sub, eps, minSamples, symm)
            resultsList.append(df_clustered)

        result = pd.concat(resultsList)
        return result

    def __find_unique_routes(self):
        routes = self.data[[ColumnNames.FROM_DEPOT.value, ColumnNames.TO_DEPOT.value]].drop_duplicates()
        routes = routes[routes[ColumnNames.FROM_DEPOT.value] != routes[ColumnNames.TO_DEPOT.value]]
        routes.dropna(inplace=True)
        return routes

    def __cluster(self, df, eps, minSamples, symm):

        db_clusters = self.__apply_dbscan(df, eps=eps, min_samples=minSamples, symm=symm)

        leg_to_cluster = defaultdict(int)
        for k, v in db_clusters.items():
            for val in v:
                leg_to_cluster[val] = k

        df.loc[:, ColumnNames.CLUSTER.value] = df[ColumnNames.LEG_ID.value].map(leg_to_cluster)
        return df

    def __apply_dbscan(self, df, eps, min_samples, symm):
        distances = self.__make_hausdorff_matrix(df, symm)
        leg_ids = df[ColumnNames.LEG_ID.value].unique()
        print("Starting DBSCAN")
        clustering = DBSCAN(eps=eps, min_samples=min_samples, metric="precomputed").fit(distances)
        db_clusters = defaultdict(list)
        for i, cluster_number in enumerate(clustering.labels_):
            leg_id = leg_ids[i]
            db_clusters[cluster_number].append(leg_id)
        print("Completed DBSCAN")
        return db_clusters

    def __make_hausdorff_matrix(self, df, symm):
        leg_ids = df[ColumnNames.LEG_ID.value].unique()
        n = len(leg_ids)
        distances = np.zeros((n, n))
        print("Number of leg IDs: ", n)
        for i in range(n):
            print("i = ", i)
            for j in range(n):
                u_id = leg_ids[i]
                v_id = leg_ids[j]
                u = df[df[ColumnNames.LEG_ID.value] == u_id]
                v = df[df[ColumnNames.LEG_ID.value] == v_id]
                u = self.__make_points(u)
                v = self.__make_points(v)
                if symm:
                    distances[i, j] = max(directed_hausdorff(u, v)[0], directed_hausdorff(v, u)[0])
                else:
                    distances[i, j] = directed_hausdorff(u, v)[0]
        print("Calculated Hausdorff distances")
        return distances

    def __make_points(self, df):

        return [np.array(item) for item in zip(df[ColumnNames.EVENT_LAT.value], df[ColumnNames.EVENT_LONG.value])]


