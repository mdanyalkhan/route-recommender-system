from ColumnNames import *
from DataParser import *
import pandas as pd

class DBSCANClusterer(DataParser):
    def __init__(self, filePath: str, fromRow: int = 0, toRow: int = None):
        DataParser.__init__(self,filePath,fromRow,toRow)

    def createCluster(self):
        routes: pd.DataFrame = self.__findUniqueRoutes()
        print(routes)

    def __findUniqueRoutes(self):
        routes = self.data[[ColumnNames.FROM_DEPOT.value, ColumnNames.TO_DEPOT.value]].drop_duplicates()
        routes = routes[routes[ColumnNames.FROM_DEPOT.value] != routes[ColumnNames.TO_DEPOT.value]]
        routes.dropna(inplace=True)
        return routes

