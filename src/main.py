from src.DBSCANClusterer import *
from os.path import *
import os as os
from src.FileDirectories import *
from src.IsotrackDataParser import *
from src.RoadDataParser import *
from src.RoadAssignment import *


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

    parent_path = parent_directory_at_level(4)
    isotrak_filename = FileDirectories.RAW_DATA.value
    roads_filename = FileDirectories.HE_DATA.value

    if isfile(parent_path + isotrak_filename) and isfile(parent_path + roads_filename):
        isotrak_path = parent_path + isotrak_filename
        roads_path = parent_path + roads_filename
        print("File found")
    else:
        print("File not found")
        exit()


    isotrak_data_set = IsotrackDataParser(isotrak_path, depot_sampled= True, no_of_legs=250)
    print(isotrak_data_set.get_df()[ColumnNames.LEG_ID.value].nunique())
    print(isotrak_data_set.start_depot)
    print(isotrak_data_set.end_depot)

    # roads_data_set = RoadDataParser(roads_path)
    # new_data = road_assignment.classify_pings_to_road_data(isotrak_data_set, roads_data_set)
    # DBSCANObject = DBSCANClusterer(new_data)
    #
    # clusterData = DBSCANObject.createClusters()
    # export_path = os.getcwd() + "/clusterData.csv"
    # print("Writing out the clustered Isotrak data to {}".format(export_path))
    #
    # clusterData.to_csv(export_path, index=False)
    # print("Isotrak data with clusters exported")