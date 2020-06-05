from src.Clustering.DBSCANClusterer import *
from os.path import *
import os as os
from src.FileDirectories import *
from src.Clustering.RoadAssignment import *
from src.Clustering.PostProcess import *

def parent_directory_at_level(level: int):
    parentPath: str = __file__
    for i in range(0,level):
        parentPath = dirname(parentPath)

    return parentPath


if __name__ == "__main__":

    parent_path: str
    isotrak_filename: str
    roads_filename: str
    isotrak_path: str
    roads_path: str
    isotrak_data_set: IsotrackDataParser
    roads_data_set: RoadDataParser
    DBSCANObject: DBSCANClusterer
    road_assignment: RoadAssignment = RoadAssignment()
    post_process: PostProcess = PostProcess()

    parent_path = parent_directory_at_level(5)
    isotrak_filename = FileDirectories.RAW_DATA_TEST.value
    roads_filename = FileDirectories.HE_DATA.value

    if isfile(parent_path + isotrak_filename) and isfile(parent_path + roads_filename):
        isotrak_path = parent_path + isotrak_filename
        roads_path = parent_path + roads_filename
        print("File found")
    else:
        print("File not found")
        exit()

    isotrak_data_set = IsotrackDataParser(isotrak_path, depot_sampled=True, no_of_legs=250)
    roads_data_set = RoadDataParser(roads_path)
    new_data = road_assignment.classify_pings_to_road_data(isotrak_data_set, roads_data_set)
    DBSCANObject = DBSCANClusterer(new_data)

    clusterData = DBSCANObject.createClusters()

    final_data = post_process.conduct_post_process(clusterData)

    export_path = os.getcwd() + "/final_results.csv"
    print("Writing out final results to {}".format(export_path))

    final_data.to_csv(export_path, index=False)
    print("Final results exported")