import pandas as pd
from src.ColumnNames import *


class DataParser(object):
    def __init__(self, file_path: str, from_row: int = 0, to_row: int = None):
        print("running parent init")

        self._read_in_data(file_path, from_row, to_row)

    def _read_in_data(self, file_path: str, from_row: int, to_row: int) -> None:
        """
        Extracts CSV data into a pandas dataframe.
        :param file_path: (Str)
        :param from_row: (int) reads in data from 'fromRow'
        :param to_row: (int) reads in data from 'toRow'
        :return: null
        """
        if to_row == None:
            self.data = pd.read_csv(file_path, skiprows=from_row)
        else:
            self.data = pd.read_csv(file_path, skiprows=from_row, nrows=from_row + to_row)

    def get_df(self) -> pd.DataFrame:
        return self.data

    def __str__(self):
        return self.data.to_string()

    def __len__(self):
        return len(self.data)
