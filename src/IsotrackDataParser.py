from src.DataParser import *
from src.ColumnNames import *

class IsotrackDataParser(DataParser):

    def __init__(self, filePath: str, fromRow: int = 0, toRow: int = None):
        DataParser.__init__(self,filePath,fromRow,toRow)

    def __read_in_data(self, filePath: str, fromRow: int, toRow: int) -> None:
        """
        Extracts CSV data into a pandas dataframe.
        :param filePath: (Str)
        :param fromRow: (int) reads in data from 'fromRow'
        :param toRow: (int) reads in data from 'toRow'
        :return: null
        """
        if toRow == None:
            self.data = pd.read_csv(filePath, skiprows=fromRow,
                                    parse_dates=[ColumnNames.EVENT_DTTM.value])
        else:
            self.data = pd.read_csv(filePath, skiprows=fromRow, nrows=fromRow + toRow,
                                    parse_dates=[ColumnNames.EVENT_DTTM.value])

    def extract_data_on_start_end_depot(self, start_depot: str = None, end_depot: str = None) -> pd.DataFrame:
        """
        Extracts all legs, and their associated pings, for a specific start and end depot (can be
        specifically selected by the user or set at random).
        :param start_depot: (str) the start Royal Mail depot
        :param end_depot: (str) the end Royal Mail depot
        :return: A dataframe of all legs, and associated pings, with start_depot and end_depot
        """
        if start_depot is None or end_depot is None:
            if start_depot is not None:
                end_depot = self.__select_random_depot(start_depot, ColumnNames.FROM_DEPOT.value,
                                                       ColumnNames.TO_DEPOT.value)
            elif end_depot is not None:
                start_depot = self.__select_random_depot(end_depot, ColumnNames.TO_DEPOT.value,
                                                         ColumnNames.FROM_DEPOT.value)
            else:
                sample_ping = self.data.sample()
                start_depot = sample_ping[ColumnNames.FROM_DEPOT.value].item()
                end_depot = sample_ping[ColumnNames.TO_DEPOT.value].item()

        return self.data.loc[(self.data[ColumnNames.FROM_DEPOT.value] == start_depot) &
                             (self.data[ColumnNames.TO_DEPOT.value] == end_depot)].copy()

    def __select_random_depot(self, known_depot: str, known_depot_col: str, target_depot_col: str) -> str:
        """
        Extracts corresponding depot pair at random for a given known_depot.
        :param known_depot: (str) The Royal Mail depot chosen
        :param known_depot_col: (str) The dataframe column corresponding to the known_depot
        :param target_depot_col: (str) The dataframe column in which the corresponding depot pair will be chosen
        :return: (str) the depot pair
        """
        df_with_start_depot = self.data.loc[self.data[known_depot_col] == known_depot]
        df_with_diff_depot = df_with_start_depot.loc[self.data[target_depot_col] != known_depot]
        return df_with_diff_depot.sample()[target_depot_col].item()
