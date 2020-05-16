from DataParser import *
from os.path import *

def parentDirectoryAtLevel(level: int):
    parentPath: str = __file__
    for i in range(0,level):
        parentPath = dirname(parentPath)

    return parentPath

if __name__ == "__main__":

    parentPath: str
    childPath: str
    targetDirectory: str
    incomingData: DataParser

    parentPath = parentDirectoryAtLevel(3)
    print(parentPath)
    childPath = "/Incoming/imperial_data/data_with_labels/20191002-20200130_isotrak_legs_excl_5km_test.csv"

    if isfile(parentPath+childPath):
        targetDirectory = parentPath+childPath
    else:
        exit()

    incomingData = DataParser(targetDirectory,3)
    print(incomingData)