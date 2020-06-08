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


if __name__ == "__main__":

    # out_path = parent_directory_at_level(__file__, 3) + fd.TEMP.value + "clipped_roads.shp"
    #
    # clipped_roads = gpd.read_file(out_path)
    main_carriageways = gpd.read_file(parent_directory_at_level(__file__,3) + fd.TEMP.value + "main_carriageways.shp")
    linked_main_carriageways = link_main_carriageway_segments(main_carriageways)
    merged_roads_df = merge_road_segments(linked_main_carriageways)
    merged_roads_df.to_file(parent_directory_at_level(__file__,3) + fd.TEMP.value + "merged_roads.shp")
    # print(clipped_roads.iloc[0].geometry_list)
    #merge_main_carriageway(clipped_roads)

    # Load HE Shapefile
    # he_path = parent_directory_at_level(__file__, 5) + fd.HE_NETWORK.value
    # he_gdf = gpd.read_file(he_path)
    # print(he_gdf)
    #
    # # # Create clipper polygon
    # coords = [(327838.0, 406237.0), (329310, 386013), (364126, 387741),
    #           (361886, 407645)]
    # poly_converter = GeoPolyDataFrameBuilder()
    # poly_gdf = poly_converter.build_geo_frame(coords, "epsg:27700")
    # clipped_gdf = clip(he_gdf, poly_gdf)

    # clipped_gdf.to_file(out_path)

    # out_path = parent_directory_at_level(__file__, 3) + fd.TEMP.value + "sample_lines.shp"
    #
    # gdf = gpd.read_file(out_path)
    #
    # print(gdf)
    # clip and save HE shapefile
    # he_clipped = gpd.clip(he_gdf, poly_gdf)
    # Clip HE shapefile with polygon as bounds
    # temp_path = parent_directory_at_level(__file__, 5) + fd.HE_NETWORK.value
    # poly = gpd.read_file(temp_path)
    # print(poly.crs)
    # print(poly)
    # print(poly['geometry'].iloc[0])

    # out_path = parent_directory_at_level(__file__, 5) + fd.HE_NETWORK.value
    # print(out_path)
    #
    # he_df = gpd.read_file(out_path)
    # print(he_df.crs)
    # print(len(he_df.loc[he_df[srn_cn.FUNCT_NAME] =='Ox Bow Lay-by']))
    # print(len(he_df.loc[(he_df[srn_cn.ROAD_NUMBER] == "M5") & (he_df[srn_cn.DIRECTION] == "SB") ]))
    # print(he_df.FUNCT_NAME.unique())
    # print(len(he_df.loc[he_df[srn_cn.DIRECTION] == "ND"]))
    # print(he_df.loc[(he_df[srn_cn.DIRECTION] == "AC") & (he_df[srn_cn.FUNCT_NAME] == "Main Carriageway")][srn_cn.LOCATION])
    # he_df.to_csv(os.getcwd()+"/xyz.csv", index = False)
    # x = {'Color':'blue'}
    # y={'length': 123}
    # g = nx.Graph()
    # g.add_edge(1,3)
    # g[1][3].update(x)
    # g[1][3].update(y)
    # print(g[1])

    # out_path = parent_directory_at_level(__file__, 3) + fd.OUT.value
    # graph = nx.read_shp(out_path)
    # print(graph[(-1.3732059093312137, 0.9284424353776157)])
    # shp = ogr.Open(out_path)
    # for lyr in shp:
    #     print("Name: " + lyr.GetName())
    #     feature = lyr.GetNextFeature()
    #     geom = feature.geometry()
    #     print(geom)
    #     print(geom.GetPoint_2D(0)[0])
    # print(temp.GetFieldAsString("Weight"))
    # temp2 = temp.GetDefnRef().GetFieldDefn(0)
    # print(temp2.GetDefault())
    # print(ogr.GeometryTypeToName(lyr.GetGeomType()))
    # print(graph.number_of_nodes())
    # print(graph.number_of_edges())
    # print(graph.nodes)
    # print(graph.edges)
