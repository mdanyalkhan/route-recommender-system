from collections import deque

import pandas as pd
import geopandas as gpd
from scipy.spatial import cKDTree
import numpy as np
from GeoDataFrameAux import extract_list_of_coords_from_geom_object
from RoadGraph.constants.StdColNames import *
from RoadGraph.constants.StdKeyWords import *

class RoadAssignment:

    def __init__(self):
        self.road_threshold = 100
        self.nearest_line_seg = 'line_seg'
        self.node_pairs = 'node_pairs'
        self.none_tuple = (None, None)

    def assign_node_pairs(self, isotrack_data: pd.DataFrame, edges: gpd.GeoDataFrame):
        print(len(isotrack_data))
        point_map = self._generate_point_line_dict(edges)
        self._assign_nearest_line_segments(point_map, isotrack_data)
        self._assign_node_pairs(isotrack_data, edges)
        print(len(isotrack_data))

    def _generate_point_line_dict(self, edges_gdf: gpd.GeoDataFrame):

        sel_edges = edges_gdf.loc[edges_gdf[STD_ROAD_TYPE] == STD_MAIN_CARRIAGEWAY]
        points = sel_edges[STD_GEOMETRY].apply(extract_list_of_coords_from_geom_object).tolist()
        std_index = sel_edges[STD_INDEX].tolist()

        d = {}

        for i in range(len(points)):
            cur_line = std_index[i]
            line_of_points = points[i]
            for point in line_of_points:
                d[point] = cur_line

        return d

    def _assign_nearest_line_segments(self, point_map: dict, isotrack_data: gpd.GeoDataFrame):
        points = list(point_map.keys())
        points_x = [point[0] for point in points]
        points_y = [point[1] for point in points]

        shortest_path_coords = np.dstack([points_x, points_y])[0]
        tree = cKDTree(shortest_path_coords)

        isotrack_coords = []
        for _, point in isotrack_data.iterrows():
            isotrack_coords.extend(extract_list_of_coords_from_geom_object(point['geometry']))
        isotrack_x = [coord[0] for coord in isotrack_coords]
        isotrack_y = [coord[1] for coord in isotrack_coords]
        isotrack_coords = np.dstack([isotrack_x, isotrack_y])[0]

        dist, indices = tree.query(isotrack_coords, k=1)

        std_index = []
        for index, distance in zip(indices, dist):

            if distance < self.road_threshold:
                sel_point = points[index]
                std_index.append(point_map[sel_point])
            else:
                std_index.append(None)

        isotrack_data[self.nearest_line_seg] = std_index

    def _assign_node_pairs(self, isotrack_data: gpd.GeoDataFrame, edges: gpd.GeoDataFrame):

        isotrack_data['visited'] = False
        isotrack_data.loc[pd.isna(isotrack_data[self.nearest_line_seg]), 'visited'] = True

        isotrack_data[self.node_pairs] = None
        for i in range(len(isotrack_data)):

            if not isotrack_data.iloc[i]['visited']:
                edges['visited'] = False
                index = isotrack_data.iloc[i][self.nearest_line_seg]

                if not edges.loc[edges[STD_INDEX] == index, 'visited'].values[0]:
                    que = deque()
                    que.append(index)
                    while que:
                        sel_ind = que.popleft()
                        edges.at[edges[STD_INDEX] == sel_ind, 'visited'] = True
                        if edges.loc[edges[STD_INDEX] == sel_ind, STD_FROM_NODE].values[0] != STD_NONE:
                            from_node = edges.loc[edges[STD_INDEX] == sel_ind, STD_FROM_NODE].values[0]
                        else:
                            prev_ind = int(edges.loc[edges[STD_INDEX] == sel_ind, STD_PREV_IND].values[0])
                            if not edges.loc[edges[STD_INDEX] == prev_ind, 'visited'].values[0]:
                                que.append(prev_ind)

                        if edges.loc[edges[STD_INDEX] == sel_ind, STD_TO_NODE].values[0] != STD_NONE:
                            to_node = edges.loc[edges[STD_INDEX] == sel_ind, STD_TO_NODE].values[0]
                        else:
                            next_ind = int(edges.loc[edges[STD_INDEX] == sel_ind, STD_NEXT_IND].values[0])
                            if not edges.loc[edges[STD_INDEX] == next_ind, 'visited'].values[0]:
                                que.append(next_ind)

                #Assign all node pairs to pings that are assigned with the line segment that forms the edge connecting
                #both node pairs
                visited_edges = edges.loc[edges['visited'] == True, STD_INDEX]
                isotrack_data.loc[isotrack_data[self.nearest_line_seg].isin(visited_edges), self.node_pairs] \
                    = pd.Series([(from_node, to_node) for _ in range(len(isotrack_data))])
                isotrack_data.loc[isotrack_data[self.nearest_line_seg].isin(visited_edges), 'visited'] = True
                edges.drop(['visited'], axis=1, inplace=True)

        isotrack_data.drop(isotrack_data[pd.isna(isotrack_data[self.nearest_line_seg]) == True].index, inplace=True)
        isotrack_data.drop(['visited', self.nearest_line_seg], axis=1, inplace=True)
