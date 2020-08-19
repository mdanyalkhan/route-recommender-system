from collections import deque
from heapq import heappush, heappop

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
        self.nearest_node = 'nearest_node'
        self.roundabout_threshold = 50.0
        self.none_tuple = (None, None)

    def assign_nearest_nodes(self, isotrack_data: pd.DataFrame, edges: gpd.GeoDataFrame, nodes: gpd.GeoDataFrame):

        isotrack_data[self.nearest_node] = None
        self._assign_nearest_roundabout_nodes(nodes, edges, isotrack_data)

        self._assign_nearest_carriageway_nodes(edges, isotrack_data)
        isotrack_data.drop(isotrack_data[pd.isna(isotrack_data[self.nearest_node]) == True].index, inplace=True)

    def _assign_nearest_roundabout_nodes(self, nodes, edges, isotrack_data):

        roundabout_point_map = self._generate_roundabout_point_dict(nodes, edges)
        points = list(roundabout_point_map.keys())
        # Set up ckdTree of nodes
        point_indices = nodes.loc[nodes[STD_N_TYPE] == STD_ROUNDABOUT].index.tolist()
        points_x = [point[0] for point in points]
        points_y = [point[1] for point in points]

        shortest_path_coords = np.dstack([points_x, points_y])[0]
        tree = cKDTree(shortest_path_coords)

        # Set up and find nearest nodes to each isotrack point
        isotrack_coords = []
        for _, point in isotrack_data.iterrows():
            isotrack_coords.extend(extract_list_of_coords_from_geom_object(point['geometry']))
        isotrack_x = [coord[0] for coord in isotrack_coords]
        isotrack_y = [coord[1] for coord in isotrack_coords]
        isotrack_coords = np.dstack([isotrack_x, isotrack_y])[0]

        dist, indices = tree.query(isotrack_coords, k=1)

        i = 0
        for index, distance in zip(indices, dist):
            nearest_point = points[index]
            if distance < self.roundabout_threshold:
                isotrack_data.loc[i, self.nearest_node] = roundabout_point_map[nearest_point]
            i += 1

    def _generate_roundabout_point_dict(self, nodes, edges):

        roundabout_edges = edges.loc[edges[STD_ROAD_TYPE] == STD_ROUNDABOUT]
        roundabout_nodes = nodes.loc[nodes[STD_N_TYPE] == STD_N_ROUNDABOUT]

        roundabout_point_map = {}

        for _, roundabout_node in roundabout_nodes.iterrows():
            node_id = roundabout_node[STD_NODE_ID]
            roundabout_segments = roundabout_edges.loc[roundabout_edges[STD_FROM_NODE] == node_id]
            points = roundabout_segments[STD_GEOMETRY].apply(extract_list_of_coords_from_geom_object).tolist()
            points = [point for point_group in points for point in point_group]
            for point in points:
                roundabout_point_map[point] = node_id

        return roundabout_point_map



    def _assign_nearest_carriageway_nodes(self, edges, isotrack_data):

        point_map = self._generate_point_line_dict(edges)
        self._find_nearest_line_segment(point_map, isotrack_data)
        self._find_nearest_node(isotrack_data, edges)

    def _generate_point_line_dict(self, edges_gdf: gpd.GeoDataFrame):

        sel_edges = edges_gdf.loc[edges_gdf[STD_ROAD_TYPE] != STD_ROUNDABOUT]
        points = sel_edges[STD_GEOMETRY].apply(extract_list_of_coords_from_geom_object).tolist()
        std_index = sel_edges[STD_INDEX].tolist()

        d = {}

        for i in range(len(points)):
            cur_line = std_index[i]
            line_of_points = points[i]
            for point in line_of_points:
                d[point] = cur_line

        return d

    def _find_nearest_line_segment(self, point_map: dict, isotrack_data: gpd.GeoDataFrame):
        points = list(point_map.keys())
        points_x = [point[0] for point in points]
        points_y = [point[1] for point in points]

        np_coords = np.dstack([points_x, points_y])[0]
        tree = cKDTree(np_coords)

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

    def _find_nearest_node(self, isotrack_data: gpd.GeoDataFrame, edges: gpd.GeoDataFrame):

        isotrack_data['visited'] = False
        # Do not examine those pings that are not allocated to a nearest line segment or have already been assigned
        # to a roundabout node
        isotrack_data.loc[pd.isna(isotrack_data[self.nearest_line_seg]), 'visited'] = True
        isotrack_data.loc[pd.isna(isotrack_data[self.nearest_node]) == False, 'visited'] = True

        for i in range(len(isotrack_data)):
            if not isotrack_data.iloc[i]['visited']:
                index = isotrack_data.iloc[i][self.nearest_line_seg]
                que = []
                heappush(que, (0, index))
                edges['visited'] = False
                edges['visited_prev'] = False
                edges['visited_next'] = False
                edges.loc[edges[STD_INDEX] == index, 'visited_prev'] = True
                edges.loc[edges[STD_INDEX] == index, 'visited_next'] = True

                while que:
                    weight, sel_ind = heappop(que)
                    edges.at[edges[STD_INDEX] == sel_ind, 'visited'] = True

                    if edges.loc[edges[STD_INDEX] == sel_ind, STD_FROM_NODE].values[0] != STD_NONE:
                        nearest_node = edges.loc[edges[STD_INDEX] == sel_ind, STD_FROM_NODE].values[0]
                        visited_edges = edges.loc[edges['visited_prev'] == True, STD_INDEX]
                        break
                    else:
                        prev_ind = int(edges.loc[edges[STD_INDEX] == sel_ind, STD_PREV_IND].values[0])
                        if not edges.loc[edges[STD_INDEX] == prev_ind, 'visited'].values[0]:
                            edges.loc[edges[STD_INDEX] == sel_ind, 'visited_prev'] = True
                            heappush(que, (weight + 1, prev_ind))

                    if edges.loc[edges[STD_INDEX] == sel_ind, STD_TO_NODE].values[0] != STD_NONE:
                        nearest_node = edges.loc[edges[STD_INDEX] == sel_ind, STD_TO_NODE].values[0]
                        visited_edges = edges.loc[edges['visited_next'] == True, STD_INDEX]
                        break
                    else:
                        next_ind = int(edges.loc[edges[STD_INDEX] == sel_ind, STD_NEXT_IND].values[0])
                        if not edges.loc[edges[STD_INDEX] == next_ind, 'visited'].values[0]:
                            edges.loc[edges[STD_INDEX] == sel_ind, 'visited_next'] = True
                            heappush(que, (weight + 1, next_ind))

                # Assign all node pairs to pings that are assigned with the line segment that forms the edge connecting
                # both node pairs
                isotrack_data.loc[(isotrack_data[self.nearest_line_seg].isin(visited_edges)) &
                                  (pd.isna(isotrack_data[self.nearest_node]) == True), self.nearest_node] = nearest_node
                isotrack_data.loc[isotrack_data[self.nearest_line_seg].isin(visited_edges), 'visited'] = True
                edges.drop('visited', axis=1, inplace=True)

        isotrack_data.drop(['visited', self.nearest_line_seg], axis=1, inplace=True)

    def find_nearest_edges(self, isotrack_data: pd.DataFrame, edges: gpd.GeoDataFrame):

        point_map = self._generate_point_line_dict(edges)
        self._find_nearest_line_segment(point_map, isotrack_data)
        isotrack_data['visited'] = False
        mapped_edges = gpd.GeoDataFrame()

        isotrack_data.loc[pd.isna(isotrack_data[self.nearest_line_seg]), 'visited'] = True

        for i in range(len(isotrack_data)):
            if not isotrack_data.iloc[i]['visited']:
                index = isotrack_data.iloc[i][self.nearest_line_seg]
                que = deque()
                que.append(index)
                edges['visited'] = False

                while que:
                    sel_ind = que.popleft()
                    edges.at[edges[STD_INDEX] == sel_ind, 'visited'] = True
                    if edges.loc[edges[STD_INDEX] == sel_ind, STD_PREV_IND].values[0] is not None:
                        prev_ind = int(edges.loc[edges[STD_INDEX] == sel_ind, STD_PREV_IND].values[0])
                        if not edges.loc[edges[STD_INDEX] == prev_ind, 'visited'].values[0]:
                            que.append(prev_ind)

                que.append(index)

                while que:
                    sel_ind = que.popleft()
                    edges.at[edges[STD_INDEX] == sel_ind, 'visited'] = True

                    if edges.loc[edges[STD_INDEX] == sel_ind, STD_NEXT_IND].values[0] is not None:
                        next_ind = int(edges.loc[edges[STD_INDEX] == sel_ind, STD_NEXT_IND].values[0])
                        if not edges.loc[edges[STD_INDEX] == next_ind, 'visited'].values[0]:
                            que.append(next_ind)

                # Assign all node pairs to pings that are assigned with the line segment that forms the edge connecting
                # both node pairs
                visited_edges = edges.loc[edges['visited'] == True, STD_INDEX].tolist()
                isotrack_data.loc[isotrack_data[self.nearest_line_seg].isin(visited_edges), 'visited'] = True
                mapped_edges = pd.concat([edges.loc[edges['visited'] == True], mapped_edges])
                edges.drop('visited', axis=1, inplace=True)

        isotrack_data.drop(['visited', self.nearest_line_seg], axis=1, inplace=True)
        return mapped_edges