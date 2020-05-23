from src.DBSCANClusterer import *
from os.path import *
import os as os
from src.FileDirectories import *
from src.IsotrackDataParser import *

def parentDirectoryAtLevel(level: int):
    parentPath: str = __file__
    for i in range(0,level):
        parentPath = dirname(parentPath)

    return parentPath


if __name__ == "__main__":

    parent_path: str
    child_path: str
    target_path: str
    data_set: IsotrackDataParser
    DBSCANObject: DBSCANClusterer

    parent_path = parentDirectoryAtLevel(4)
    child_path = FileDirectories.RAW_DATA.value

    if isfile(parent_path + child_path):
        target_path = parent_path + child_path
        print("File found")
    else:
        print("File not found")
        exit()

    data_set = IsotrackDataParser(target_path, depot_sampled= True)

    # DBSCANObject = DBSCANClusterer(targetDirectory)
    # clusterData = DBSCANObject.createClusters()
    # export_path = os.getcwd() + "/clusterData.csv"
    # print("Writing out the clustered Isotrak data to {}".format(export_path))
    #
    # clusterData.to_csv(export_path, index=False)
    # print("Isotrak data with clusters exported")