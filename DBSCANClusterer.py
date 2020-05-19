from ColumnNames import *
import pandas as pd

class DBSCANClusterer:
    def __init__(self, filePath: str, fromRow: int = 0, toRow: int = None):

        if toRow == None:
            self.data = pd.read_csv(filePath, skiprows= fromRow, parse_dates=ColumnNames.EVENT_DTTM.value)
        else:
            self.data = pd.read_csv(filePath, skiprows= fromRow, nrows= fromRow + toRow,
                                    parse_dates=[ColumnNames.EVENT_DTTM.value])

    def __str__(self):
        return self.data.to_string()

