from unittest import TestCase
from RoadGraph import *
from src.utilities.aux_func import parent_directory_at_level


class TestRoadGraph(TestCase):
    in_nodes_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/final/nodes.shp"
    in_edges_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/final/edges.shp"
    nodes_gdf = gpd.read_file(in_nodes_path)
    edges_gdf = gpd.read_file(in_edges_path)

    def test_no_duplicate_nodes(self):
        d = {}

        self.nodes_gdf['coords'] = self.nodes_gdf['geometry'].apply(lambda x: extract_coord_at_index(x, 0))
        self.assertEqual(len(self.nodes_gdf.loc[self.nodes_gdf.duplicated(['coords'], keep=False), :]), 0)
        self.nodes_gdf.drop('coords', axis=1, inplace=True)

    def test_prev_and_next_indices_are_not_the_same(self):
        same_indices = self.edges_gdf.loc[self.edges_gdf[STD_PREV_IND] == self.edges_gdf[STD_NEXT_IND]]
        edges_filtered = same_indices.loc[(pd.isna(self.edges_gdf[STD_PREV_IND]) == False) &
                                          (pd.isna(self.edges_gdf[STD_NEXT_IND]) == False)]

        # For London, Birmingham and Bristol region there are four areas in which both indices are the same, this
        # is strictly due to the nature of the OS data, rather than the methodology applied. These edges are index:
        # 31675, 31676, 62895 and 62896
        self.assertEqual(len(edges_filtered), 4)

    def test_that_prev_ind_and_from_node_are_both_not_filled_in(self):
        check_edges = self.edges_gdf.loc[(pd.isna(self.edges_gdf[STD_PREV_IND]) == False) &
                                         (self.edges_gdf[STD_FROM_NODE] != 'None')]

        print(check_edges[STD_INDEX].tolist())

    def test_that_next_ind_and_to_node_are_both_not_filled_in(self):

        check_edges = self.edges_gdf.loc[(pd.isna(self.edges_gdf[STD_NEXT_IND]) == False) &
                                         (self.edges_gdf[STD_TO_NODE] != 'None')]
        print(check_edges[STD_INDEX].tolist())

    def test_check_from_node_and_to_node_are_not_the_same(self):
        check_edges = self.edges_gdf.loc[(self.edges_gdf[STD_FROM_NODE] == self.edges_gdf[STD_TO_NODE]) &
                                         (self.edges_gdf[STD_FROM_NODE] != 'None') &
                                         (self.edges_gdf[STD_TO_NODE] != 'None') &
                                         (self.edges_gdf[STD_ROAD_TYPE] != STD_ROUNDABOUT)]
        print(check_edges[STD_INDEX].tolist())
