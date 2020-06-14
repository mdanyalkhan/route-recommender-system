from src.utilities.aux_func import *
from src.utilities.file_directories import FileDirectories as fd
import geopandas as gpd
from RoadNetwork import *
import os
if __name__ == "__main__":

    print("hello world")
    # he_path = parent_directory_at_level(__file__, 5) + fd.HE_NETWORK.value + "/network.shp"
    # folder_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/OS_Open_roads"

    # he_gdf = gpd.read_file(he_path)
    # he_road_numbers = he_gdf["ROA_NUMBER"].unique().tolist()
    #
    # merged_os_gdf = OSOpenRoadsToHERoadsConverter().convert_and_merge_to_HE_geoDataframe(folder_path, he_road_numbers)
    #
    # merged_os_gdf.to_file(folder_path + "/os_merged_converted.shp")
    # clipped_roads_path = parent_directory_at_level(__file__,3) + "/temp/clipped_roads.shp"
    # os_road_path = parent_directory_at_level(__file__, 3) + "/temp/OS_roads.shp"
    #
    # os_road_gdf = gpd.read_file(os_road_path)
    # clipped_roads_gdf = gpd.read_file(clipped_roads_path)
    # clipped_roads_numbers = clipped_roads_gdf["ROA_NUMBER"].unique().tolist()
    # os_processed_gdf = OSOpenRoadsToHERoadsConverter().convert_to_HE_dataframe(os_road_gdf, clipped_roads_numbers)
    # os_processed_gdf.to_file(parent_directory_at_level(__file__, 3) + "/temp/OS_roads_converted.shp")

    # SJ_road_link_path = parent_directory_at_level(__file__,4) + fd.OS_DATA.value + "SJ_RoadLink.shp"
    # poly_clip_gdf = gpd.read_file(poly_clip_path)
    # SJ_road_link_gdf = gpd.read_file(SJ_road_link_path)
    # SJ_road_link_gdf_clip = clip(SJ_road_link_gdf, poly_clip_gdf)
    # out_path = parent_directory_at_level(__file__,3) + "/temp/OS_roads.shp"
    # SJ_road_link_gdf_clip.to_file(out_path)
    # out_path = parent_directory_at_level(__file__, 4) + fd.OS_DATA.value + "SJ_RoadLink.shp"
    # print(out_path)
    # roads_df = gpd.read_file(out_path)
    # print(roads_df["class"].unique())
    # print(roads_df["formOfWay"].unique())
    # print(roads_df["function"].unique())
    # print(roads_df["roadNumber"].unique())
    # print(roads_df.loc[(roads_df['roadNumber'].isnull()) & ((roads_df['class'] == "Motorway") |
    #                                                         (roads_df['class'] == "Slip Road"))] )

    # x,y = link_roads(roads_df)
    # x.to_file(parent_directory_at_level(__file__, 3) + fd.TEMP.value + "SRN_edges.shp")
    # y.to_file(parent_directory_at_level(__file__, 3) + fd.TEMP.value + "SRN_nodes.shp")
    # create_graph(x,y)