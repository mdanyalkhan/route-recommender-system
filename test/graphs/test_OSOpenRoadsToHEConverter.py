from unittest import TestCase
from RoadNetwork import *
from GeoDataFrameAux import *

#TODO: amend geometry to only be lineString Z
class TestOSOpenRoadsToHERoadsConverter(TestCase):
    mock_os_df = pd.DataFrame({
        OS_CLASS: ["A Road", "Motorway", "A Road", "unknown"],
        OS_ROAD_NO: ["A1", "M1", "A2", "None"],
        OS_FUNCT_NAME: ["Single Carriageway", "Roundabout", "Slip Road", "Slip Road"],
        OS_LENGTH: ["10", "20", "30", "40"],
        OS_ID: ["1", "2", "3", "4"],
        GEOMETRY: [(0, 0), (1, 1), (2, 2), (3, 3)]
    })

    mock_os_df[GEOMETRY] = mock_os_df[GEOMETRY].apply(GeoPointDataFrameBuilder()._build_geometry_object)
    mock_os_df[GEOMETRY] = mock_os_df[GEOMETRY].apply(wkt.loads)
    mock_os_gdf = gpd.GeoDataFrame(mock_os_df, geometry= GEOMETRY)

    # def test_convert_OS_data_to_HE_compatible_dataframe(self):
    #
    #     OSOpenRoadsToHERoadsConverter().convert_to_HE_dataframe(self.mock_os_gdf, ["A1","A1"])

    def test_roundabout_renaming_is_correct(self):

        df = pd.DataFrame({
            HE_ROAD_NO: ['A1', 'A1', 'A1', 'A1', 'M1', 'M1'],
            HE_FUNCT_NAME: ["Roundabout", "Roundabout", "Roundabout", "Roundabout",
                            "Main Carriageway", "Main Carriageway"],
            GEOMETRY: [[(0, 0), (0, 0.5)], [(0, 0.5), (1, 0.5)], [(1, 0.5), (1, 0.0)],
                       [(1, 0.0), (0, 0)], [(0, 0), (-1, -1.2)], [(10.1, 9), (1, 0.5)]]
        })

        df[GEOMETRY] = df[GEOMETRY].apply(GeoLineDataFrameBuilder()._build_geometry_object)
        df[GEOMETRY] = df[GEOMETRY].apply(wkt.loads)
        gdf = gpd.GeoDataFrame(df, geometry= GEOMETRY)

        he_road_no_new = ['A1_0','A1_0','A1_0','A1_0','M1', 'M1']
        gdf = OSOpenRoadsToHERoadsConverter()._rename_roundabouts(gdf)
        self.assertEqual(gdf[HE_ROAD_NO].tolist(), he_road_no_new)
