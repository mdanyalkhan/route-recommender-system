import numpy as np

class DataParser:
    def __init__(self, filePath: str, noOfRows: int):
        self.filePath: str = filePath
        self.heading: np.ndarray = np.loadtxt(filePath, dtype=str, delimiter=',', max_rows=1)
        self.sampleData: np.ndarray = np.loadtxt(filePath, dtype=str, delimiter=',', skiprows=1, max_rows=noOfRows)
        self.__setDataShapeParam()

    def __setDataShapeParam(self):

        """
        Private function extracts row and column parameters of the data

        params: -
        returns: -

        """
        self.noOfRows: int
        self.noOfCol: int

        if len(self.sampleData.shape) == 2:
            self.noOfRows = self.sampleData.shape[0]
            self.noOfCol = self.sampleData.shape[1]
        else:
            self.noOfRows = 1
            self.noOfCol = self.sampleData.shape[0]

    def __str__(self):
        PADDING: int = 37
        colName: str
        colData: str
        colCount: int = 0
        outputString: str = ""

        for colName in self.heading:
            outputString += colName.center(PADDING) + " | "
        outputString += "\n"

        for index, colData in np.ndenumerate(self.sampleData):
            outputString += colData.center(PADDING) + " | "
            colCount += 1
            if colCount >= self.noOfCol:
                outputString += "\n"
                colCount = 0

        return outputString
