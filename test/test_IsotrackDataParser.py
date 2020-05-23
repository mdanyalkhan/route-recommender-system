from unittest import TestCase
from src.IsotrackDataParser import *
from src.ColumnNames import *
import pandas as pd
import os

class TestIsotrackDataParser(TestCase):

    mock_df: pd.DataFrame = pd.DataFrame([{ColumnNames.FROM_DEPOT.value: "London",
                                          ColumnNames.TO_DEPOT.value: "Southend",
                                           ColumnNames.EVENT_DTTM.value: "2019-10-02 20:30:28"},
                                         {ColumnNames.FROM_DEPOT.value: "Birmingham",
                                          ColumnNames.TO_DEPOT.value: "Wolverhampton",
                                          ColumnNames.EVENT_DTTM.value: "2019-10-02 20:30:28"},
                                         {ColumnNames.FROM_DEPOT.value: "Edinburgh",
                                          ColumnNames.TO_DEPOT.value: "Glasgow",
                                          ColumnNames.EVENT_DTTM.value: "2019-10-02 20:30:28"}])

    mock_from_depot: list  = ["London", "Birmingham", "Edinburgh"]
    mock_to_depot: list = ["Southend", "Wolverhampton", "Glasgow"]

    def test_returns_dataframe_based_on_randomly_generated_start_end_depot(self):
        self.mock_df.to_csv("mock_df.csv", index = False)
        data_set = IsotrackDataParser("mock_df.csv")
        sample_data = data_set.extract_data_on_start_end_depot()

        #Check if number of unique to and from depot are 1
        self.assertEqual(sample_data[ColumnNames.FROM_DEPOT.value].nunique(), 1)
        os.remove("mock_df.csv")