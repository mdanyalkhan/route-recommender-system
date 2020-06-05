from src.Clustering.DataParser import *
from src.Clustering.ColumnNames import *


class RoadDataParser(DataParser):

    def __init__(self, file_path: str, from_row: int = 0, to_row: int = None):

        super(RoadDataParser,self).__init__(file_path,from_row, to_row)


    def _read_in_data(self, file_path: str, from_row: int, to_row: int) -> None:
        """
        Extracts CSV data into a pandas dataframe.
        :param file_path: (Str)
        :param from_row: (int) reads in data from 'fromRow'
        :param to_row: (int) reads in data from 'toRow'
        :return: null
        """
        if to_row == None:
            self.data = pd.read_csv(file_path, skiprows=from_row,
                                    dtype={ColumnNames.LINK_NAME.value: str,
                                           ColumnNames.C_WAY.value: str,
                                           ColumnNames.SECTION.value: str})
        else:
            self.data = pd.read_csv(file_path, skiprows=from_row, nrows=from_row + to_row,
                                    dtype={ColumnNames.LINK_NAME.value: str,
                                           ColumnNames.C_WAY.value: str,
                                           ColumnNames.SECTION.value: str})
