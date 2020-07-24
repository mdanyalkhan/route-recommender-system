from src.utilities.file_directories import FileDirectories as fd
from src.utilities.aux_func import parent_directory_at_level
import pandas as pd
import geopandas as gpd
import numpy as np


def generate_potential_motorway_junction_name_candidates(m_input: list, j_input: list) -> list:

    junction_suffix_candidates = []

    for i in range(len(j_input)):
        junction_suffix_candidates.append(parse_junctions(j_input[i]))

    junction_candidates = []
    for i  in range(len(m_input)):
        if m_input[i][-1] == 'M':
            m_input[i] = f"{m_input[i][:-1]}({m_input[i][-1]})"
        junction_candidates.extend([f"{m_input[i]} {junc}" for junc in junction_suffix_candidates[i] if junc[0] == 'J'])

    junction_candidates = list(set(junction_candidates))

    return junction_candidates

def parse_junctions(input: str) -> list:
    input_list = input.split()

    junction_candidates = []

    #Insert junction range
    for i in range(1, len(input_list) - 1):
        if input_list[i] == '-':
            if input_list[i-1][0] == 'J' and input_list[i+1][0] == 'J':
                first_junc = int(input_list[i-1][1:]) if input_list[i-1][1:].isdigit() else None
                second_junc = int(input_list[i+1][1:]) if input_list[i+1][1:].isdigit() else None

                if first_junc and second_junc:
                    first, last = (first_junc, second_junc) if first_junc < second_junc else (second_junc, first_junc)
                    while first <= last:
                        junction_candidates.append(f"J{first}")
                        first += 1

    #Add in any other outstanding junctions
    junction_candidates += [junction for junction in input_list if junction[0] == 'J' and
                          junction not in junction_candidates]

    #Add in possible junctions with Motorway Nos added as potential prefix
    for i in range(len(input_list) - 1):
        if input_list[i][0] == 'M' or input_list[i][0] == 'A':
            if input_list[i+1][0] == 'J':
                junction_candidates.append(f"{input_list[i]} {input_list[i+1]}")

    return junction_candidates

def increment(value: str) -> str:

    if value.isdigit():
        int_val = int(value)
        int_val += 1
        return str(int_val)
    else:
        str_val = value[-1]

        if str_val == 'b':
            return f"{int(value[:-1]) + 1}"

        str_val = chr(ord(str_val) + 1)
        return f"{value[:-1]}{str_val}"

def less_than(x: str, y: str):

    x_int = int(x) if x.isdigit() else int(x[:-1])
    y_int = int(y) if y.isdigit() else int(y[:-1])

    if not x.isdigit() and not y.isdigit() and x_int == y_int:
        return ord(x[-1]) < ord(y[-1])

    return x_int < y_int

if __name__ == "__main__":

    closure_path = parent_directory_at_level(__file__, 4) + fd.CLOSURE_DATA.value
    junctions_path = parent_directory_at_level(__file__, 5) + fd.HE_JUNCTIONS.value

    df = pd.read_csv(closure_path)
    junctions_df = gpd.read_file(junctions_path)

    real_junctions = junctions_df['number'].tolist()
    motorways = df.loc[:,'Road'].tolist()
    junctions_raw = df.loc[:, 'Junctions'].tolist()

    candidates = generate_potential_motorway_junction_name_candidates(motorways, junctions_raw)

    accepted = []
    rejected = []

    for candidate in candidates:
        if candidate in real_junctions:
            accepted += [candidate]
        else:
            rejected += [candidate]

    print(len(candidates))
    print(len(accepted))
    print(len(rejected))

    print(rejected)
