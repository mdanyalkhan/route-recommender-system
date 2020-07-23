from src.utilities.file_directories import FileDirectories as fd
from src.utilities.aux_func import parent_directory_at_level
import pandas as pd
import numpy as np


def generate_potential_motorway_junction_name_candidates():
    pass

def parse_junctions():
    pass

if __name__ == "__main__":

    closure_path = parent_directory_at_level(__file__, 4) + fd.CLOSURE_DATA.value

    df = pd.read_csv(closure_path)
    print(df.columns)
    motorways = df.loc[:,'Road'].tolist()
    junctions_raw = df.loc[:, 'Junctions'].tolist()

    junction_list = junctions_raw[0].split(' ')

    list_of_junctions = []
    for i in range(1, len(junction_list) - 1):
        if junction_list[i] == '-':
            if junction_list[i-1][0] == 'J' and junction_list[i+1][0] == 'J':
                first_junc = int(junction_list[i-1][1:])
                second_junc = int(junction_list[i+1][1:])

                first, last = (first_junc, second_junc) if first_junc < second_junc else (second_junc, first_junc)
                while first <= last:
                    list_of_junctions.append(f"J{first}")
                    first += 1

    list_of_junctions += [junction for junction in junction_list if junction[0] == 'J' and
                          junction not in list_of_junctions]

    for i in range(len(junction_list) - 1):
        if junction_list[i][0] == 'M' or junction_list[i][0] == 'A':
            if junction_list[i+1][0] == 'J':
                list_of_junctions.append(f"{junction_list[i]} {junction_list[i+1]}")

    print(list_of_junctions)