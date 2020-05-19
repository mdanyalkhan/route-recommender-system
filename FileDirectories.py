from enum import Enum

class FileDirectories(Enum):
    RAW_DATA = "/Incoming/imperial_data/data_with_labels/20191002-20200130_isotrak_legs_excl_5km_test.csv"
    SCRUBBED_DATA = "/Incoming/imperial_data/data_to_run_code_on/20190701-20190823_isotrak_legs_few_cols.csv"
    RMG_LOCATIONS = "/Incoming/imperial_data/data_to_run_code_on/ALL_RMG_LOCATIONS.csv"
    HE_DATA = "/Incoming/imperial_data/data_to_run_code_on/he_data.csv"
    HE_JUNCTIONS = "/Incoming/imperial_data/data_to_run_code_on/he_junctions_mn.csv"
    ROAD_DATA = "/Incoming/imperial_data/data_to_run_code_on/roads_data.csv"
