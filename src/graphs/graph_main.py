from RoadGraph.preprocessing import *
from src.utilities import file_directories as fd
from src.utilities.aux_func import parent_directory_at_level

if __name__ == "__main__":

    #Generating the road graph for the London, Bristol & Birmingham region
    lbb_in_path = fd.LbbDirectories().original_gdfs_path
    lbb_target_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/temp"
    lbb_road_graph = StdRoadGraphBuilder().build_road_graph(lbb_in_path, lbb_target_path)

    #Generating the road graph for the Preston, Leeds, Chester & Rugby region
    # plcr_in_path = fd.plcrDirectories().original_gdfs_path
    # plcr_target_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/plcr"
    # plcr_road_graph = StdRoadGraphBuilder().build_road_graph(plcr_in_path, plcr_target_path)
