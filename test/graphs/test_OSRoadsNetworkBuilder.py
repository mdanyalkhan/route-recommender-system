from unittest import TestCase
from RoadNetwork import *
from shapely.ops import linemerge

class TestOSRoadsNetworkBuilder(TestCase):

    def test_connection_of_road_segments_is_correct(self):
        df = pd.DataFrame({
            INDEX: [0, 1, 2],
            HE_ROAD_NO: ['A1', 'A1', 'M1'],
            HE_FUNCT_NAME: ["Main Carriageway", "Main Carriageway", "Main Carriageway"],
            PREV_IND: [pd.NA, pd.NA, pd.NA],
            NEXT_IND: [pd.NA, pd.NA, pd.NA],
            FROM_NODE: ["None", "None", "None"],
            TO_NODE: ["None", "None", "None"],
            FIRST_COORD: [(0, 0), (0, 0.5), (0, 1.0)],
            LAST_COORD: [(0, 0.5), (0, 1.0), (0, 1.5)]
        })

        prev_ind_new = [pd.NA, 0, pd.NA]
        next_ind_new = [1, pd.NA, pd.NA]

        df, _ = OSRoadsNetworkBuilder()._connect_and_assign_nodes_main_carriageways_slip_roads(df, {})

        self.assertEqual(df[PREV_IND].tolist(), prev_ind_new)
        self.assertEqual(df[NEXT_IND].tolist(), next_ind_new)

    def test_connection_of_road_segments_where_two_road_segments_last_coords_are_the_same(self):
        df = pd.DataFrame({
            INDEX: [0, 1, 2],
            HE_ROAD_NO: ['A1', 'A1', 'M1'],
            HE_FUNCT_NAME: ["Main Carriageway", "Main Carriageway", "Main Carriageway"],
            PREV_IND: [pd.NA, pd.NA, pd.NA],
            NEXT_IND: [pd.NA, pd.NA, pd.NA],
            FROM_NODE: ["None", "None", "None"],
            TO_NODE: ["None", "None", "None"],
            FIRST_COORD: [(0, 0), (0, 1.0), (0, 1.0)],
            LAST_COORD: [(0, 0.5), (0, 0.5), (0, 1.5)]
        })

        prev_ind_new = [pd.NA, 0, pd.NA]
        next_ind_new = [1, pd.NA, pd.NA]

        df, _ = OSRoadsNetworkBuilder()._connect_and_assign_nodes_main_carriageways_slip_roads(df, {})

        self.assertEqual(df[PREV_IND].tolist(), prev_ind_new)
        self.assertEqual(df[NEXT_IND].tolist(), next_ind_new)

    def test_connection_of_road_segments_where_two_road_segments_first_coords_are_the_same(self):
        df = pd.DataFrame({
            INDEX: [0, 1, 2],
            HE_ROAD_NO: ['M1', 'A1', 'A1'],
            HE_FUNCT_NAME: ["Main Carriageway", "Main Carriageway", "Main Carriageway"],
            PREV_IND: [pd.NA, pd.NA, pd.NA],
            NEXT_IND: [pd.NA, pd.NA, pd.NA],
            FROM_NODE: ["None", "None", "None"],
            TO_NODE: ["None", "None", "None"],
            FIRST_COORD: [(0, 0), (0, 1.0), (0, 1.0)],
            LAST_COORD: [(0, 0.5), (0, 0.5), (0, 1.5)]
        })

        prev_ind_new = [pd.NA, 2, pd.NA]
        next_ind_new = [pd.NA, pd.NA, 1]
        df, _ = OSRoadsNetworkBuilder()._connect_and_assign_nodes_main_carriageways_slip_roads(df, {})
        self.assertEqual(df[PREV_IND].tolist(), prev_ind_new)
        self.assertEqual(df[NEXT_IND].tolist(), next_ind_new)

    def test_connection_where_there_are_more_than_two_road_segment_connections(self):
        df = pd.DataFrame({
            INDEX: [0, 1, 2, 3, 4, 5],
            HE_ROAD_NO: ['A1', 'A1', 'A1', 'M1', 'M1', 'M1'],
            HE_FUNCT_NAME: ["Main Carriageway", "Main Carriageway", "Main Carriageway", "Main Carriageway",
                            "Main Carriageway", "Main Carriageway"],
            PREV_IND: [pd.NA, pd.NA, pd.NA, pd.NA, pd.NA, pd.NA],
            NEXT_IND: [pd.NA, pd.NA, pd.NA, pd.NA, pd.NA, pd.NA],
            FROM_NODE: ["None", "None", "None", "None", "None", "None"],
            TO_NODE: ["None", "None", "None", "None", "None", "None"],
            FIRST_COORD: [(0, 0), (0, 0), (0, 0), (0.5, 0.5), (-1, -2.2), (10.1, 9)],
            LAST_COORD: [(0, 0.5), (0, 2.5), (0, 1.5), (-1, 2.2), (0.5, 0.5), (0.5, 0.5)]
        })

        prev_ind_new = [pd.NA, pd.NA, pd.NA, pd.NA, pd.NA, pd.NA]
        next_ind_new = [pd.NA, pd.NA, pd.NA, pd.NA, pd.NA, pd.NA]
        from_node_new = ["_0", "_0", "_0", "_1", "None", "None"]
        to_node_new = ["None", "None", "None", "None", "_1", "_1"]

        df, nodes = OSRoadsNetworkBuilder()._connect_and_assign_nodes_main_carriageways_slip_roads(df, {})

        self.assertEqual(df[PREV_IND].tolist(), prev_ind_new)
        self.assertEqual(df[NEXT_IND].tolist(), next_ind_new)
        self.assertEqual(df[FROM_NODE].tolist(), from_node_new)
        self.assertEqual(df[TO_NODE].tolist(), to_node_new)
        self.assertEqual(nodes[N_NODE_ID], ['_0', '_1'])

    def test_connections_to_os_type_roundabout(self):
        df = pd.DataFrame({
            INDEX: [0, 1, 2, 3, 4, 5],
            HE_ROAD_NO: ['A1', 'A1', 'A1', 'A1', 'M1', 'M1'],
            HE_FUNCT_NAME: ["Roundabout", "Roundabout", "Roundabout", "Roundabout",
                            "Main Carriageway", "Main Carriageway"],
            PREV_IND: [pd.NA, pd.NA, pd.NA, pd.NA, pd.NA, pd.NA],
            NEXT_IND: [pd.NA, pd.NA, pd.NA, pd.NA, pd.NA, pd.NA],
            FROM_NODE: ["None", "None", "None", "None", "None", "None"],
            TO_NODE: ["None", "None", "None", "None", "None", "None"],
            FIRST_COORD: [(0, 0), (0, 0.5), (1, 0.5), (1, 0.0), (0, 0), (10.1, 9)],
            LAST_COORD: [(0, 0.5), (1, 0.5), (1, 0.0), (0, 0), (-1, -1.2), (1, 0.5)],
            GEOMETRY: [[(0, 0), (0, 0.5)], [(0, 0.5), (1, 0.5)], [(1, 0.5), (1, 0.0)],
                       [(1, 0.0), (0, 0)], [(0, 0), (-1, -1.2)], [(10.1, 9), (1, 0.5)]]
        })

        df[GEOMETRY] = df[GEOMETRY].apply(GeoLineDataFrameBuilder()._build_geometry_object)
        df[GEOMETRY] = df[GEOMETRY].apply(wkt.loads)

        gdf = gpd.GeoDataFrame(df, geometry= GEOMETRY)
        nodes = {}

        from_node_new = ["None", "None", "None", "None", "_0", "None"]
        to_node_new = ["None", "None", "None", "None", "None", "_0"]
        gdf, nodes = OSRoadsNetworkBuilder()._nodes_roads_to_roundabouts(gdf, nodes)

        self.assertEqual(gdf[FROM_NODE].tolist(), from_node_new)
        self.assertEqual(gdf[TO_NODE].tolist(), to_node_new)
        self.assertEqual(nodes[N_NODE_ID], ['_0'])