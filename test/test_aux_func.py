from unittest import TestCase
from src.graphs.geo_frame_builder.geo_poly_data_frame_builder import *
from src.graphs.geo_frame_builder.geo_line_data_frame_builder import *
import geopandas as gpd

class Test_aux_functions(TestCase):

    #Parameters
    crs = "epsg:27700"

    #Build boundary
    mock_bounds_coords = [(0,0), (0,1), (1,1), (1,0)]
    mock_boundary_gdf = GeoPolyDataFrameBuilder().build_geo_frame(mock_bounds_coords,crs)

    def test_is_in_bounds(self):
        print("hello")