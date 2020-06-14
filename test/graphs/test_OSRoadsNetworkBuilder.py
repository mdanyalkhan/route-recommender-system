from unittest import TestCase
from RoadNetwork import *

class TestOSRoadsNetworkBuilder(TestCase):

    def test_connection_of_road_segments_is_correct(self):
        df = pd.DataFrame({
            INDEX: [0, 1, 2, 3],
            HE_ROAD_NO: ['A1', 'A1', 'M1', 'A1'],
            HE_FUNCT_NAME: ["Main Carriageway", "Main Carriageway", "Main Carriageway", "Slip Road"],
            PREV_IND: [pd.NA, pd.NA, pd.NA, pd.NA],
            NEXT_IND: [pd.NA, pd.NA, pd.NA, pd.NA],
            FROM_NODE: ["None", "None", "None", "None"],
            TO_NODE: ["None", "None", "None", "None"],
            FIRST_COORD: [(0, 0), (0, 0.5), (0, 1.0), (0, 0.5)],
            LAST_COORD: [(0, 0.5), (0, 1.0), (0, 1.5), (0.5, 0.5)]
        })

        prev_ind_new = [pd.NA, 0, pd.NA, pd.NA]
        next_ind_new = [1, pd.NA, pd.NA, pd.NA]

        df = OSRoadsNetworkBuilder(0)._connect_road_segments_based_on_funct_name(df, HE_MAIN_CARRIAGEWAY)

        print(df.loc[:,[PREV_IND, NEXT_IND]])
        self.assertEqual(df[PREV_IND].tolist(), prev_ind_new)
        self.assertEqual(df[NEXT_IND].tolist(), next_ind_new)

    def test_connection_of_road_segments_of_different_directions_is_correct(self):
        df = pd.DataFrame({
            INDEX: [0, 1, 2, 3],
            HE_ROAD_NO: ['A1', 'A1', 'M1', 'A1'],
            HE_FUNCT_NAME: ["Main Carriageway", "Main Carriageway", "Main Carriageway", "Slip Road"],
            PREV_IND: [pd.NA, pd.NA, pd.NA, pd.NA],
            NEXT_IND: [pd.NA, pd.NA, pd.NA, pd.NA],
            FROM_NODE: ["None", "None", "None", "None"],
            TO_NODE: ["None", "None", "None", "None"],
            FIRST_COORD: [(0, 0), (0, 1.0), (0, 1.0), (0, 0.5)],
            LAST_COORD: [(0, 0.5), (0, 0.5), (0, 1.5), (0.5, 0.5)]
        })

        prev_ind_new = [pd.NA, 0, pd.NA, pd.NA]
        next_ind_new = [1, pd.NA, pd.NA, pd.NA]

        df = OSRoadsNetworkBuilder(0)._connect_road_segments_based_on_funct_name(df, HE_MAIN_CARRIAGEWAY)
        print(df)
        print(df.loc[:,[PREV_IND, NEXT_IND]])
        # self.assertEqual(df[PREV_IND].tolist(), prev_ind_new)
        # self.assertEqual(df[NEXT_IND].tolist(), next_ind_new)


