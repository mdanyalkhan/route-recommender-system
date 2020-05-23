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
    mock_df.to_csv("mock_df.csv", index=False)
    data_set = IsotrackDataParser("mock_df.csv")

    def test_returns_dataframe_based_on_randomly_generated_start_end_depot(self):

        sample_data = self.data_set.extract_data_on_start_end_depot()

        #Check if number of unique to and from depot are 1
        self.assertEqual(sample_data[ColumnNames.FROM_DEPOT.value].nunique(), 1)
        self.assertEqual(sample_data[ColumnNames.TO_DEPOT.value].nunique(), 1)

        #Check that the from_depot value is not equal to the to_depot value
        self.assertTrue(sample_data[sample_data[ColumnNames.FROM_DEPOT.value] ==
                                     sample_data[ColumnNames.TO_DEPOT.value]].empty)

    def test_returns_dataframe_using_selected_from_start_depot_value(self):

        sample_data = self.data_set.extract_data_on_start_end_depot(start_depot="London")

        self.assertEqual(sample_data[ColumnNames.TO_DEPOT.value].sample().item(), "Southend")

    def test_returns_dataframe_using_selected_from_end_depot_value(self):

        sample_data = self.data_set.extract_data_on_start_end_depot(end_depot="Glasgow")

        self.assertEqual(sample_data[ColumnNames.FROM_DEPOT.value].sample().item(), "Edinburgh")

    def test_returns_dataframe_using_selected_depot_values(self):

        sample_data = self.data_set.extract_data_on_start_end_depot(start_depot="Birmingham",
                                                                    end_depot="Wolverhampton")

        self.assertEqual(sample_data[ColumnNames.FROM_DEPOT.value].sample().item(), "Birmingham")
        self.assertEqual(sample_data[ColumnNames.TO_DEPOT.value].sample().item(), "Wolverhampton")

    os.remove("mock_df.csv")



