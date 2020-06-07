from unittest import TestCase
from src.clustering.IsotrackDataParser import *
from src.clustering.ColumnNames import *
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

    def test_initialised_with_full_data_frame(self):
        self.mock_df.to_csv("mock_df.csv", index=False)
        full_set = IsotrackDataParser("mock_df.csv")
        os.remove("mock_df.csv")
        self.assertEqual(len(full_set), len(self.mock_df))

    def test_returns_dataframe_based_on_randomly_generated_start_end_depot(self):

        self.mock_df.to_csv("mock_df.csv", index=False)
        sample_set = IsotrackDataParser("mock_df.csv", depot_sampled= True)
        os.remove("mock_df.csv")
        sample_df = sample_set.get_df()

        #Check if number of unique to and from depot are 1
        self.assertEqual(sample_df[ColumnNames.FROM_DEPOT.value].nunique(), 1)
        self.assertEqual(sample_df[ColumnNames.TO_DEPOT.value].nunique(), 1)

        #Check that the from_depot value is not equal to the to_depot value
        self.assertTrue(sample_df[sample_df[ColumnNames.FROM_DEPOT.value] ==
                                     sample_df[ColumnNames.TO_DEPOT.value]].empty)

    def test_returns_dataframe_using_selected_from_start_depot_value(self):

        self.mock_df.to_csv("mock_df.csv", index=False)
        sample_set = IsotrackDataParser("mock_df.csv", depot_sampled= True, start_depot="London")
        os.remove("mock_df.csv")
        sample_df = sample_set.get_df()

        self.assertEqual(sample_df[ColumnNames.TO_DEPOT.value].sample().item(), "Southend")

    def test_returns_dataframe_using_selected_from_end_depot_value(self):

        self.mock_df.to_csv("mock_df.csv", index=False)
        sample_set = IsotrackDataParser("mock_df.csv", depot_sampled= True, end_depot="Glasgow")
        os.remove("mock_df.csv")
        sample_df = sample_set.get_df()

        self.assertEqual(sample_df[ColumnNames.FROM_DEPOT.value].sample().item(), "Edinburgh")

    def test_returns_dataframe_using_selected_depot_values(self):

        self.mock_df.to_csv("mock_df.csv", index=False)
        sample_set = IsotrackDataParser("mock_df.csv", depot_sampled= True, start_depot="Birmingham",
                                        end_depot="Wolverhampton")
        os.remove("mock_df.csv")
        sample_df = sample_set.get_df()

        self.assertEqual(sample_df[ColumnNames.FROM_DEPOT.value].sample().item(), "Birmingham")
        self.assertEqual(sample_df[ColumnNames.TO_DEPOT.value].sample().item(), "Wolverhampton")

    def test_returns_dataframe_only_under_no_of_legs_threshold(self):

        #Set up mock dataframe
        mock_df_duplicates = pd.DataFrame([{ColumnNames.LEG_ID.value: 1,
                                            ColumnNames.FROM_DEPOT.value: "London",
                                            ColumnNames.TO_DEPOT.value: "Southend",
                                            ColumnNames.EVENT_DTTM.value: "2019-10-02 20:30:28"},
                                           {ColumnNames.LEG_ID.value: 1,
                                            ColumnNames.FROM_DEPOT.value: "London",
                                            ColumnNames.TO_DEPOT.value: "Southend",
                                            ColumnNames.EVENT_DTTM.value: "2019-10-02 20:30:28"},
                                           {ColumnNames.LEG_ID.value: 1,
                                            ColumnNames.FROM_DEPOT.value: "Birmingham",
                                            ColumnNames.TO_DEPOT.value: "Wolverhampton",
                                            ColumnNames.EVENT_DTTM.value: "2019-10-02 20:30:28"},
                                           {ColumnNames.LEG_ID.value: 2,
                                            ColumnNames.FROM_DEPOT.value: "Birmingham",
                                            ColumnNames.TO_DEPOT.value: "Wolverhampton",
                                            ColumnNames.EVENT_DTTM.value: "2019-10-02 20:30:28"},
                                           ])

        mock_df_duplicates.to_csv("mock_df_duplicates.csv", index=False)
        sample_set = IsotrackDataParser("mock_df_duplicates.csv", depot_sampled= True, no_of_legs=1)
        os.remove("mock_df_duplicates.csv")
        sample_df = sample_set.get_df()

        self.assertTrue(sample_df[ColumnNames.FROM_DEPOT.value].sample().item() != "Birmingham")
        self.assertTrue(sample_df[ColumnNames.FROM_DEPOT.value].sample().item() == "London")


