from unittest import TestCase
from RoadNetwork import *


class Test(TestCase):
    test_object = HERoadsNetworkBuilder(connection_threshold=0.3, min_spacing_for_roundabout_resolution=1.99)

    def test_euclidean_distance(self):
        coord1 = (8, 7)
        coord2 = (3, 2)
        ans = sqrt(50)
        self.assertEqual(self.test_object._euclidean_distance(coord1, coord2), ans)

    def test_find_closest_road_returns_correct_index(self):
        target_coord = (1, 1)
        df = pd.DataFrame({
            "INDEX": [1, 2],
            "FUNCT_NAME": ["Main Carriageway", "Main Carriageway"],
            "FIRST_COORD": [(0.8, 0.9), (1.4, 1.5)],
            "LAST_COORD": [(0.2, 0.9), (1.1, 1.2)],
        })

        first_coord_min_dist = sqrt(pow(1 - 0.8, 2) + pow(1 - 0.9, 2))
        second_coord_min_dist = sqrt(pow(1 - 1.1, 2) + pow(1 - 1.2, 2))

        self.assertEqual(self.test_object._find_closest_main_carriageway(df, target_coord, 0), (1, first_coord_min_dist))
        self.assertEqual(self.test_object._find_closest_main_carriageway(df, target_coord, 0,
                                                                         use_first_coord_of_main_carriageway=False),
                         (2, second_coord_min_dist))

    def test_reconfiguration_of_carriageway_links_based_on_slip_roads_branching_out_of_roads(self):
        # Parameters
        df = pd.DataFrame({
            "INDEX": [1, 2, 3, 4],
            "FUNCT_NAME": ["Main Carriageway", "Main Carriageway", "Main Carriageway", "Slip Road"],
            "PREV_IND": [pd.NA, 1, 2, pd.NA],
            "NEXT_IND": [2, 3, pd.NA, 10],
            "FROM_NODE": ["None", "None", "None", "None"],
            "TO_NODE": ["None", "None", "None", "None"],
            "FIRST_COORD": [(0, 0), (0, 0.5), (0, 1.0), (0, 0.5)],
            "LAST_COORD": [(0, 0.5), (0, 1.0), (0, 1.5), (0.5, 0.5)]
        })
        node_dict = {}

        # Answers
        prev_ind_new = [pd.NA, pd.NA, 2, pd.NA]
        next_ind_new = [pd.NA, 3, pd.NA, 10]
        from_node_new = ["None", "_0", "None", "_0"]
        to_node_new = ["_0", "None", "None", "None"]
        node_ids = ["_0"]
        node_coords = [(0, 0.5)]

        # calculations
        df, node_dict = self.test_object._nodes_main_carriageways_to_slip_roads(df, node_dict)
        # Checks
        self.assertEqual(df.loc[:, "PREV_IND"].tolist(), prev_ind_new)
        self.assertEqual(df.loc[:, "NEXT_IND"].tolist(), next_ind_new)
        self.assertEqual(df.loc[:, "FROM_NODE"].tolist(), from_node_new)
        self.assertEqual(df.loc[:, "TO_NODE"].tolist(), to_node_new)
        self.assertEqual(node_dict["node_id"], node_ids)
        self.assertEqual(node_dict["geometry"], node_coords)

    def test_reconfiguration_of_carriageway_links_based_on_slip_roads_branching_into_roads(self):
        # Parameters
        df = pd.DataFrame({
            "INDEX": [1, 2, 3, 4],
            "FUNCT_NAME": ["Main Carriageway", "Main Carriageway", "Main Carriageway", "Slip Road"],
            "PREV_IND": [pd.NA, 1, 2, 10],
            "NEXT_IND": [2, 3, pd.NA, pd.NA],
            "FROM_NODE": ["None", "None", "None", "None"],
            "TO_NODE": ["None", "None", "None", "None"],
            "FIRST_COORD": [(0, 0), (0, 0.5), (0, 1.0), (0.5, 0.5)],
            "LAST_COORD": [(0, 0.5), (0, 1.0), (0, 1.5), (0, 0.5)]
        })
        node_dict = {}

        # Answers
        prev_ind_new = [pd.NA, pd.NA, 2, 10]
        next_ind_new = [pd.NA, 3, pd.NA, pd.NA]
        from_node_new = ["None", "_0", "None", "None"]
        to_node_new = ["_0", "None", "None", "_0"]
        node_ids = ["_0"]
        node_coords = [(0, 0.5)]

        # calculations
        df, node_dict = self.test_object._nodes_main_carriageways_to_slip_roads(df, node_dict)

        # Checks
        self.assertEqual(df.loc[:, "PREV_IND"].tolist(), prev_ind_new)
        self.assertEqual(df.loc[:, "NEXT_IND"].tolist(), next_ind_new)
        self.assertEqual(df.loc[:, "FROM_NODE"].tolist(), from_node_new)
        self.assertEqual(df.loc[:, "TO_NODE"].tolist(), to_node_new)
        self.assertEqual(node_dict["node_id"], node_ids)
        self.assertEqual(node_dict["geometry"], node_coords)

    def test_reconfiguration_of_carriageway_links_based_on_slip_roads_branching_between_roads(self):
        # Parameters
        df = pd.DataFrame({
            "INDEX": [1, 2, 3, 4, 5],
            "FUNCT_NAME": ["Main Carriageway", "Main Carriageway", "Main Carriageway",
                           "Slip Road", "Main Carriageway"],
            "PREV_IND": [pd.NA, 1, 2, pd.NA, pd.NA],
            "NEXT_IND": [2, 3, pd.NA, pd.NA, pd.NA],
            "FROM_NODE": ["None", "None", "None", "None", "None"],
            "TO_NODE": ["None", "None", "None", "None", "None"],
            "FIRST_COORD": [(0, 0), (0, 0.5), (0, 1.0), (0, 0.5), (0.5, 0.5)],
            "LAST_COORD": [(0, 0.5), (0, 1.0), (0, 1.5), (0.5, 0.5), (0.5, 1)]
        })
        node_dict = {}

        # Answers
        prev_ind_new = [pd.NA, pd.NA, 2, pd.NA, pd.NA]
        next_ind_new = [pd.NA, 3, pd.NA, pd.NA, pd.NA]
        from_node_new = ["None", "_0", "None", "_0", "_1"]
        to_node_new = ["_0", "None", "None", "_1", "None"]
        node_ids = ["_0", "_1"]
        node_coords = [(0, 0.5), (0.5, 0.5)]

        # calculations
        df, node_dict = self.test_object._nodes_main_carriageways_to_slip_roads(df, node_dict)

        # print(df.loc[:,"PREV_IND"].tolist())
        # #Checks
        self.assertEqual(df.loc[:, "PREV_IND"].tolist(), prev_ind_new)
        self.assertEqual(df.loc[:, "NEXT_IND"].tolist(), next_ind_new)
        self.assertEqual(df.loc[:, "FROM_NODE"].tolist(), from_node_new)
        self.assertEqual(df.loc[:, "TO_NODE"].tolist(), to_node_new)
        self.assertEqual(node_dict["node_id"], node_ids)
        self.assertEqual(node_dict["geometry"], node_coords)

    def test_resolution_of_line_segment_increases(self):
        coords = [(-2, 0), (0, 0), (1, 1), (3, 3)]
        self.assertEqual(self.test_object._increase_resolution_of_line(coords),
                         [(-2, 0), (-1.0, 0.0), (0, 0), (1, 1), (2.0, 2.0), (3, 3)])

        pass

    def test_reconfiguration_of_roads_based_on_roundabout_connections(self):
        df = pd.DataFrame({
            "INDEX": [1, 2, 3, 4, 5],
            "FUNCT_NAME": ["Main Carriageway", "Main Carriageway", "Slip Road", "Roundabout", "Main Carriageway"],
            "PREV_IND": [pd.NA, pd.NA, pd.NA, pd.NA, pd.NA],
            "NEXT_IND": [pd.NA, pd.NA, pd.NA, pd.NA, pd.NA],
            "FROM_NODE": ["None", "None", "None", "None", "None"],
            "TO_NODE": ["None", "None", "None", "None", "None"],
            "FIRST_COORD": [(0, -1), (5, 8), (0, 1), (0, 0), (1, 1)],
            "LAST_COORD": [(0, 0), (12, 9), (0, 2), (0.1, 0), (2, 2)],
            "geometry": [[(0, -1), (0, 0)], [(5, 8), (12, 9)], [(0, 1), (0, 2)],
                         [(0, 0), (0, 1), (1, 1), (1, 0), (0.1, 0)],
                         [(1, 1), (2, 2)]]
        })

        df["geometry"] = df["geometry"].apply(GeoLineDataFrameBuilder()._build_geometry_object)
        df["geometry"] = df["geometry"].apply(wkt.loads)
        node_dict = {}

        from_node_new = ["None", "None", "_0", "None", "_0"]
        to_node_new = ["_0", "None", "None", "None", "None"]

        df, node_dict = self.test_object._nodes_roads_to_roundabouts(df, node_dict)

        self.assertEqual(df["FROM_NODE"].tolist(), from_node_new)
        self.assertEqual(df["TO_NODE"].tolist(), to_node_new)

    def test_reconfiguration_of_roads_based_on_two_roundabout_connections(self):
        df = pd.DataFrame({
            "INDEX": [1, 2, 3, 4, 5, 6],
            "FUNCT_NAME": ["Main Carriageway", "Main Carriageway", "Slip Road", "Roundabout",
                           "Main Carriageway", "Roundabout"],
            "PREV_IND": [pd.NA, 5, pd.NA, pd.NA, pd.NA, pd.NA],
            "NEXT_IND": [pd.NA, pd.NA, pd.NA, pd.NA, 2, pd.NA],
            "FROM_NODE": ["None", "None", "None", "None", "None", "None"],
            "TO_NODE": ["None", "None", "None", "None", "None", "None"],
            "FIRST_COORD": [(0, -1), (5, 8), (0, 1), (0, 0), (1, 1), (0, 2)],
            "LAST_COORD": [(0, 0), (12, 9), (0, 2), (0.1, 0), (5, 8), (0.1, 2)],
            "geometry": [[(0, -1), (0, 0)], [(5, 8), (12, 9)], [(0, 1), (0, 2)],
                         [(0, 0), (0, 1), (1, 1), (1, 0), (0.1, 0)],
                         [(1, 1), (5, 8)],
                         [(0, 2), (0, 3), (1, 3), (1, 2), (0.1, 2)]]
        })

        df["geometry"] = df["geometry"].apply(GeoLineDataFrameBuilder()._build_geometry_object)
        df["geometry"] = df["geometry"].apply(wkt.loads)
        node_dict = {}

        # Answers
        from_node_new = ["None", "None", "_0", "None", "_0", "None"]
        to_node_new = ["_0", "None", "_1", "None", "None", "None"]
        prev_ind_new = [pd.NA, 5, pd.NA, pd.NA, pd.NA, pd.NA]
        next_ind_new = [pd.NA, pd.NA, pd.NA, pd.NA, 2, pd.NA]

        # Checks
        df, node_dict = self.test_object._nodes_roads_to_roundabouts(df, node_dict)
        self.assertEqual(df["FROM_NODE"].tolist(), from_node_new)
        self.assertEqual(df["TO_NODE"].tolist(), to_node_new)
        self.assertEqual(df["PREV_IND"].tolist(), prev_ind_new)
        self.assertEqual(df["NEXT_IND"].tolist(), next_ind_new)

    def test_nodes_are_assigned_to_dead_end_roads(self):
        df = pd.DataFrame({
            "INDEX": [1, 2, 3, 4, 5],
            "FUNCT_NAME": ["Main Carriageway", "Main Carriageway", "Main Carriageway", "Slip Road", "Roundabout"],
            "PREV_IND": [pd.NA, pd.NA, 2, pd.NA, pd.NA],
            "NEXT_IND": [pd.NA, 3, pd.NA, pd.NA, pd.NA],
            "FROM_NODE": ["None", "None", "None", "None", "None"],
            "TO_NODE": ["None", "None", "None", "None", "None"],
            "FIRST_COORD": [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)],
            "LAST_COORD": [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]
        })

        node_dict = {}

        # Answers
        from_node_new = ["_0", "_2", "None", "_4", "None"]
        to_node_new = ["_1", "None", "_3", "_5", "None"]
        df, node_dict = self.test_object._assign_nodes_to_dead_end_roads(df, node_dict)
        node_ids_new = ["_0", "_1", "_2", "_3", "_4", "_5"]

        # Checks
        self.assertEqual(df["FROM_NODE"].tolist(), from_node_new)
        self.assertEqual(df["TO_NODE"].tolist(), to_node_new)
        self.assertEqual(node_dict["node_id"], node_ids_new)
