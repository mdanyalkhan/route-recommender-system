from DBSCANClusterer import *
from os.path import *
from FileDirectories import *
import pandas as pd

def parentDirectoryAtLevel(level: int):
    parentPath: str = __file__
    for i in range(0,level):
        parentPath = dirname(parentPath)

    return parentPath


if __name__ == "__main__":

    parentPath: str
    childPath: str
    targetDirectory: str
    clusterData: DBSCANClusterer

    parentPath = parentDirectoryAtLevel(3)
    childPath = FileDirectories.RAW_DATA.value

    if isfile(parentPath+childPath):
        targetDirectory = parentPath+childPath
    else:
        print("File not found")
        exit()

    clusterData = DBSCANClusterer(targetDirectory,toRow=10)
    print(clusterData)
