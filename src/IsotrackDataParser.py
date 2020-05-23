from src.DataParser import *
from src.ColumnNames import *

class IsotrackDataParser(DataParser):

    def __init__(self, file_path: str, from_row: int = 0, to_row: int = None, depot_sampled: bool = False,
                 start_depot: str = None, end_depot: str = None, no_of_legs: int = None):

        #TODO: construct an IsotrackDataParserBuilder for greater clarity

        self.no_of_legs = no_of_legs
        self.start_depot: str = start_depot
        self.end_depot: str = end_depot
        self.is_depot_sampled: bool = depot_sampled

        super(IsotrackDataParser,self).__init__(file_path,from_row, to_row)


    def _read_in_data(self, file_path: str, from_row: int, to_row: int) -> None:
        """
        Extracts CSV data into a pandas dataframe.
        :param file_path: (Str)
        :param from_row: (int) reads in data from 'fromRow'
        :param to_row: (int) reads in data from 'toRow'
        :return: null
        """
        df: pd.DataFrame
        if to_row == None:
            df = pd.read_csv(file_path, skiprows=from_row,
                             parse_dates=[ColumnNames.EVENT_DTTM.value])
        else:
            df = pd.read_csv(file_path, skiprows=from_row, nrows=from_row + to_row,
                             parse_dates=[ColumnNames.EVENT_DTTM.value])

        if self.is_depot_sampled:
            self.data = self.__extract_data_on_start_end_depot(df, self.start_depot, self.end_depot)
        else:
            self.data = df

    def __extract_data_on_start_end_depot(self, df: pd.DataFrame, start_depot: str = None,
                                          end_depot: str = None) -> pd.DataFrame:
        """
        Extracts all legs, and their associated pings, for a specific start and end depot (can be
        specifically selected by the user or set at random).
        :param df: (pd.Dataframe) dataframe to extract data from
        :param start_depot: (str) the start Royal Mail depot
        :param end_depot: (str) the end Royal Mail depot
        :return: A dataframe of all legs, and associated pings, with start_depot and end_depot
        """
        if start_depot is None or end_depot is None:
            if start_depot is not None:
                end_depot = self.__select_corresponding_sample_depot(df, start_depot, ColumnNames.FROM_DEPOT.value,
                                                                     ColumnNames.TO_DEPOT.value)
            elif end_depot is not None:
                start_depot = self.__select_corresponding_sample_depot(df, end_depot, ColumnNames.TO_DEPOT.value,
                                                                       ColumnNames.FROM_DEPOT.value)
            else:
                start_depot, end_depot = self.__select_sample_depot_pair(df)

        self.start_depot = start_depot
        self.end_depot = end_depot

        return df.loc[(df[ColumnNames.FROM_DEPOT.value] == start_depot) &
                             (df[ColumnNames.TO_DEPOT.value] == end_depot)].copy()

    def __select_corresponding_sample_depot(self, df: pd.DataFrame, known_depot: str, known_depot_col: str,
                                            target_depot_col: str) -> str:
        """
        Extracts corresponding depot pair at random for a given known_depot.
        :param df: (pd.Dataframe) dataframe to extract data from
        :param known_depot: (str) The Royal Mail depot chosen
        :param known_depot_col: (str) The dataframe column corresponding to the known_depot
        :param target_depot_col: (str) The dataframe column in which the corresponding depot pair will be chosen
        :return: (str) the depot pair
        """
        df_with_start_depot = df.loc[df[known_depot_col] == known_depot]
        df_with_diff_depot = df_with_start_depot.loc[df[target_depot_col] != known_depot]
        return df_with_diff_depot.sample()[target_depot_col].item()

    def __select_sample_depot_pair(self, df) -> (str, str):
        """
        Selects start and end depot pair at random based on the maximum allowable number of leg IDs
        :param df: (pd.Dataframe)
        :return: tupele(str,str) of start depot value and end depot value
        """
        start_depot: str
        end_depot: str

        if self.no_of_legs is None:
            sample_ping = df.loc[df[ColumnNames.FROM_DEPOT.value] != df[ColumnNames.TO_DEPOT.value]].sample()
            start_depot = sample_ping[ColumnNames.FROM_DEPOT.value].item()
            end_depot = sample_ping[ColumnNames.TO_DEPOT.value].item()
        else:
            df_unique_depot_pair = df.loc[df[ColumnNames.FROM_DEPOT.value] != df[ColumnNames.TO_DEPOT.value]]

            df_group_filter = df_unique_depot_pair.groupby(
                [ColumnNames.FROM_DEPOT.value,ColumnNames.TO_DEPOT.value]).filter(
                lambda x: x[ColumnNames.LEG_ID.value].nunique() <= self.no_of_legs)

            sample_ping = df_group_filter.sample()
            start_depot = sample_ping[ColumnNames.FROM_DEPOT.value].item()
            end_depot = sample_ping[ColumnNames.TO_DEPOT.value].item()

        return start_depot, end_depot