from src.utilities.aux_func import *
from src.graphs.geo_frame_builder.geo_poly_data_frame_builder import *
from src.utilities.file_directories import FileDirectories as fd
import networkx as nx
from osgeo import ogr
import geopandas as gpd
import os
from shapely.geometry import LineString
import src.graphs.SRN_column_names as srn_cn
from src.graphs.pre_processing import *
import matplotlib.pyplot as plt

if __name__ == "__main__":

    out_path = parent_directory_at_level(__file__, 5) + fd.HE_NETWORK.value + "network.shp"
    print(out_path)
    roads_df = gpd.read_file(out_path)

    x,y = link_roads(roads_df)
    x.to_file(parent_directory_at_level(__file__, 3) + fd.TEMP.value + "SRN_edges.shp")
    y.to_file(parent_directory_at_level(__file__, 3) + fd.TEMP.value + "SRN_nodes.shp")
    create_graph(x,y)