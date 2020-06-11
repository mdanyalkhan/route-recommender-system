from src.utilities.aux_func import *
from src.utilities.file_directories import FileDirectories as fd
import geopandas as gpd

if __name__ == "__main__":

    out_path = parent_directory_at_level(__file__, 4) + fd.OS_DATA.value + "SJ_RoadLink.shp"
    print(out_path)
    roads_df = gpd.read_file(out_path)
    print(roads_df["class"].unique())
    print(roads_df["formOfWay"].unique())
    print(roads_df["function"].unique())
    print(roads_df["roadNumber"].unique())
    print(roads_df.loc[(roads_df['roadNumber'].isnull()) & ((roads_df['class'] == "Motorway") |
                                                            (roads_df['class'] == "Slip Road"))] )

    # x,y = link_roads(roads_df)
    # x.to_file(parent_directory_at_level(__file__, 3) + fd.TEMP.value + "SRN_edges.shp")
    # y.to_file(parent_directory_at_level(__file__, 3) + fd.TEMP.value + "SRN_nodes.shp")
    # create_graph(x,y)