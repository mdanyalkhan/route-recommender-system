from unittest import TestCase
from RoadNetwork import *

class TestOSOpenRoadsToHERoadsConverter(TestCase):

    mock_os_df = pd.DataFrame({
        OS_CLASS: ["A Road", "Motorway", "A Road", "unknown"],
        OS_ROAD_NO: ["A1", "M1", "A2", "None"],
        OS_FUNCT_NAME: ["Single Carriageway", "Roundabout", "Slip Road", "Slip Road"]
    })

    def test_convert_OS_data_to_HE_compatible_dataframe(self):

        OSOpenRoadsToHERoadsConverter().convert_to_HE_dataframe(self.mock_os_df)
        pass