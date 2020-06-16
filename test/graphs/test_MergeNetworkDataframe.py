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
        N_NODE_ID: ["B_1", "B_2", "B_3", "B_4", "B_5"],
        N_TYPE: [N_DEAD_END, N_JUNCTION, N_DEAD_END, N_DEAD_END, N_DEAD_END],
        GEOMETRY: [[0, 0], [1, 1], [2, 2], [8, 8], [9, 9]]
    })

    base_nodes_df[GEOMETRY] = base_nodes_df[GEOMETRY].apply(GeoPointDataFrameBuilder()._build_geometry_object)
    base_nodes_df[GEOMETRY] = base_nodes_df[GEOMETRY].apply(wkt.loads)

    to_merge_edges_df = pd.DataFrame({
        INDEX: [0, 1, 2, 3, 4],
        HE_ROAD_NO: ["A1", "A1", "A2", "A2", "X1"],
        PREV_IND: [pd.NA, 1, pd.NA, 2, pd.NA],
        NEXT_IND: [1, pd.NA, 2, pd.NA, pd.NA],
        FROM_NODE: ["X_1", "None", "X_2", "None", "X_4"],
        TO_NODE: ["None", "X_2", "None", "X_3", "X_5"]
    })

    to_merge_nodes_df = pd.DataFrame({
        N_NODE_ID: ["X_1", "X_2", "X_3", "X_4", "X_5"],
        N_TYPE: [N_DEAD_END, N_JUNCTION, N_DEAD_END, N_DEAD_END, N_DEAD_END],
        GEOMETRY: [[0, 0], [0, 1], [0, 2], [8, 8], [9, 9]]
    })

    def test_roads_are_excluded_between_dataframes(self):
        new_df = MergeNetworkDataFrames()._exclude_roads(self.base_edges_df, self.to_merge_edges_df)

        self.assertEqual(new_df[HE_ROAD_NO].tolist(), ["A1", "A1", "A2", "A2"])
