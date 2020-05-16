from DataParser import *
from os.path import *

if __name__ == "__main__":

    parentPath: str
    childPath: str
    targetDirectory: str
    incomingData: DataParser

    parentPath = dirname(dirname(dirname(abspath(__file__))))
    print(parentPath)
    childPath = "/Incoming/imperial_data/data_with_labels/20191002-20200130_isotrak_legs_excl_5km_test.csv"

    if isfile(parentPath+childPath):
        targetDirectory = parentPath+childPath
    else:
        exit()

    incomingData = DataParser(targetDirectory,3)
    print(incomingData)