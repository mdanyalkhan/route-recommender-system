from unittest import TestCase
from RoadNetwork import *
from GeoDataFrameAux import *


class TestMergeNetworkDataFrames(TestCase):
    base_edges_df = pd.DataFrame({
        INDEX: [0, 1, 2, 3, 4],
        HE_ROAD_NO: ["M1", "M1", "M2", "M2", "X1"],
        PREV_IND: [pd.NA, 1, pd.NA, 2, pd.NA],
        NEXT_IND: [1, pd.NA, 2, pd.NA, pd.NA],
        FROM_NODE: ["B_1", "None", "B_2", "None", "B_4"],
        TO_NODE: ["None", "B_2", "None", "B_3", "B_5"]
    })

    base_nodes_df = pd.DataFrame({
        N_NODE_ID: ["B_1", "B_2", "B_3", "B_4", "B_5", "B_6"],
        N_TYPE: [N_DEAD_END, N_JUNCTION, N_DEAD_END, N_DEAD_END, N_DEAD_END, N_ROUNDABOUT],
        GEOMETRY: [[0, 0], [1, 1], [2, 2], [8, 8], [9, 9], [15, 15]],
        N_ROUNDABOUT_EXTENT: [pd.NA, pd.NA, pd.NA, pd.NA, pd.NA, 3.0]
    })

    base_nodes_df[GEOMETRY] = base_nodes_df[GEOMETRY].apply(GeoPointDataFrameBuilder()._build_geometry_object)
    base_nodes_df[GEOMETRY] = base_nodes_df[GEOMETRY].apply(wkt.loads)

    to_merge_edges_df = pd.DataFrame({
        INDEX: [0, 1, 2, 3, 4, 5, 6],
        HE_ROAD_NO: ["A1", "X1", "A1", "A2", "A2", "A3", "A4"],
        PREV_IND: [pd.NA, pd.NA, 0, pd.NA, 3, pd.NA, pd.NA],
        NEXT_IND: [2, pd.NA, pd.NA, 4, pd.NA, pd.NA, pd.NA],
        FROM_NODE: ["X_1", "X_2", "None", "X_4", "None", "X_6", "X_8"],
        TO_NODE: ["None", "X_3", "X_4", "None", "X_5", "X_7", "X_9"]
    })

    to_merge_nodes_df = pd.DataFrame({
        N_NODE_ID: ["X_1", "X_2", "X_3", "X_4", "X_5", "X_6", "X_7", "X_8", "X_9"],
        N_TYPE: [N_DEAD_END, N_DEAD_END, N_DEAD_END, N_JUNCTION, N_DEAD_END, N_DEAD_END, N_DEAD_END,
                 N_DEAD_END, N_DEAD_END],
        GEOMETRY: [[0, 0], [8, 8], [9, 9], [0, 1], [0, 2], [7.8, 8.4], [14, 15], [2, 3], [2, 2]],
        N_ROUNDABOUT_EXTENT: [pd.NA, pd.NA, pd.NA, pd.NA, pd.NA, pd.NA, pd.NA, pd.NA, pd.NA]
    })

    to_merge_nodes_df[GEOMETRY] = to_merge_nodes_df[GEOMETRY].apply(GeoPointDataFrameBuilder()._build_geometry_object)
    to_merge_nodes_df[GEOMETRY] = to_merge_nodes_df[GEOMETRY].apply(wkt.loads)

    def test_roads_are_excluded_between_dataframes(self):
        base_edges_df = self.base_edges_df.copy()
        to_merge_edges_df = self.to_merge_edges_df.copy()
        to_merge_nodes_df = self.to_merge_nodes_df.copy()

        new_edges_df, new_nodes_df = MergeNetworkDataFrames()._exclude_roads(base_edges_df,
                                                                             to_merge_edges_df,
                                                                             to_merge_nodes_df)

        self.assertEqual(new_edges_df[HE_ROAD_NO].tolist(), ["A1", "A1", "A2", "A2", "A3", "A4"])
        self.assertEqual(new_nodes_df[N_NODE_ID].tolist(), ["X_1", "X_4", "X_5", "X_6", "X_7", "X_8", "X_9"])

    def test_road_is_connected_to_roundabout(self):
        base_nodes_df = self.base_nodes_df.copy()
        to_merge_edges_df = self.to_merge_edges_df.copy()
        to_merge_nodes_df = self.to_merge_nodes_df.copy()

        new_edges_df, new_nodes_df, _ = MergeNetworkDataFrames()._connect_by_nodes(base_nodes_df,
                                                                                   to_merge_nodes_df,
                                                                                   to_merge_edges_df,
                                                                                   N_ROUNDABOUT)

        self.assertEqual(new_edges_df[TO_NODE].tolist(), ["None", "X_3", "X_4", "None", "X_5", "B_6", "X_9"])
        self.assertEqual(new_nodes_df[N_NODE_ID].tolist(), ["X_1", "X_2", "X_3", "X_4", "X_5", "X_6", "X_8", "X_9"])

    def test_dead_end_nodes_connect(self):
        base_nodes_df = self.base_nodes_df.copy()
        to_merge_edges_df = self.to_merge_edges_df.copy()
        to_merge_nodes_df = self.to_merge_nodes_df.copy()

        new_edges_df, new_nodes_df, _ = MergeNetworkDataFrames(threshold=0)._connect_by_nodes(base_nodes_df,
                                                                                              to_merge_nodes_df,
                                                                                              to_merge_edges_df,
                                                                                              N_DEAD_END,
                                                                                              check_only_dead_ends=False)

        self.assertEqual(new_edges_df[TO_NODE].tolist(), ["None", "B_5", "X_4", "None", "X_5", "X_7", "B_3"])

    def test_overall_function(self):
        base_edges_df = self.base_edges_df.copy()
        base_nodes_df = self.base_nodes_df.copy()
        to_merge_edges_df = self.to_merge_edges_df.copy()
        to_merge_nodes_df = self.to_merge_nodes_df.copy()

        new_road_no = ["M1", "M1", "M2", "M2", "X1", "A1", "A1", "A2", "A2", "A3", "A4"]
        new_node_ids = ['B_1', 'B_2', 'B_3', 'B_4', 'B_5', 'B_6', 'X_4', 'X_5', 'X_6', 'X_8']
        base_edges_df, base_nodes_df = MergeNetworkDataFrames(threshold=0).merge_two_network_dataframes(base_edges_df,
                                                                                                        base_nodes_df,
                                                                                                        to_merge_edges_df,
                                                                                                        to_merge_nodes_df)

        self.assertEqual(base_edges_df[HE_ROAD_NO].tolist(), new_road_no)
        self.assertEqual(base_nodes_df[N_NODE_ID].tolist(), new_node_ids)