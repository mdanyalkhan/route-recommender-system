import pandas as pd
from src.ColumnNames import *

class DataParser:
    def __init__(self, filePath: str, fromRow: int = 0, toRow: int = None):
        self.__read_in_data(filePath, fromRow, toRow)

    def __read_in_data(self, filePath: str, fromRow: int, toRow: int) -> None:
        """
        Extracts CSV data into a pandas dataframe.
        :param filePath: (Str)
        :param fromRow: (int) reads in data from 'fromRow'
        :param toRow: (int) reads in data from 'toRow'
        :return: null
        """
        if toRow == None:
            self.data = pd.read_csv(filePath, skiprows=fromRow)
        else:
            self.data = pd.read_csv(filePath, skiprows=fromRow, nrows=fromRow + toRow)

    def get_df(self) -> pd.DataFrame:
        return self.data

    def __str__(self):
        return self.data.to_string()
