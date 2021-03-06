from enum import Enum
from src.utilities.aux_func import parent_directory_at_level

"""
Local file directories used to facilitate the execution of this project. 
"""
class FileDirectories(Enum):
    RAW_DATA_TEST = "/Incoming/imperial_data/data_with_labels/20191002-20200130_isotrak_legs_excl_5km_test.csv"
    RAW_DATA_TRAIN = "/Incoming/imperial_data/data_with_labels/20191002-20200130_isotrak_legs_excl_5km_train/" \
                     "20191002-20200130_isotrak_legs_excl_5km_TRAIN_MEDWAY MC_PRINCESS ROYAL DC.csv"
    SCRUBBED_DATA = "/Incoming/imperial_data/data_to_run_code_on/20190701-20190823_isotrak_legs_few_cols.csv"
    RMG_LOCATIONS = "/Incoming/imperial_data/data_to_run_code_on/ALL_RMG_LOCATIONS.csv"
    HE_DATA = "/Incoming/imperial_data/data_to_run_code_on/he_data.csv"
    HE_JUNCTIONS = "/Incoming/imperial_data/highways_england_shapefiles/Motorway_Junctions/MotorwayJunctions.shp"
    ROAD_DATA = "/Incoming/imperial_data/data_to_run_code_on/roads_data.csv"
    HE_NETWORK = "/Incoming/imperial_data/highways_england_shapefiles/HAPMS/"
    OUT = "/out/"
    TEMP = "/temp/"
    OS_DATA = "/Other_incoming_data/oproad_essh_gb/data/"
    OS_SELECTED_DATA = "/Operational_data_OS_Open_Roads/"
    CLOSURE_DATA = "/Operational_Data/closures/closure_data_210720.csv"


class ParentDirectories:
    isotrack_path = parent_directory_at_level(__file__, 5) + "/Incoming/imperial_data/data_with_labels/20191002-" \
                                                             "20200130_isotrak_legs_excl_5km_train"
    key_sites_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/rm_sites/rm_locations.shp"

    # To be overwritten
    isotrack_dict = {}
    original_gdfs_path = None
    out_path_criteria1 = None
    out_path_criteria2 = None
    out_path_criteria3 = None
    out_prefix = None
    netx_path_criteria1 = None
    netx_path_criteria2 = None
    netx_path_criteria3 = None
    edges_path = None
    nodes_path = None


class LbbDirectories(ParentDirectories):
    isotrack_path = ParentDirectories.isotrack_path

    isotrack_dict = {
        'MD_PR': f"{isotrack_path}/20191002-20200130_isotrak_legs_excl_5km_TRAIN_MEDWAY MC_PRINCESS ROYAL DC.csv",
        'PR_SW': f"{isotrack_path}/20191002-20200130_isotrak_legs_excl_5km_TRAIN_PRINCESS ROYAL DC_SOUTH WEST DC.csv",
        'ND_BM': f"{isotrack_path}/20191002-20200130_isotrak_legs_excl_5km_TRAIN_NATIONAL DC_BRISTOL MC.csv",
        'HW_SW': f"{isotrack_path}/20191002-20200130_isotrak_legs_excl_5km_TRAIN_SOUTH WEST DC_HEATHROW WORLDWIDE DC.csv",
        }

    original_gdfs_path = f"{parent_directory_at_level(__file__, 4)}/Operational_Data/lbb/refined"
    out_path_criteria1 = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/compare_to_telemetry" \
                                                                  "/criteria1"
    out_path_criteria2 = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/compare_to_telemetry" \
                                                                  "/criteria2"
    out_path_criteria3 = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/compare_to_telemetry" \
                                                                  "/criteria3"
    netx_path_criteria1 = parent_directory_at_level(__file__,
                                                    4) + "/Operational_Data/lbb/out/netx/roadGraph_criteria1.pickle"
    netx_path_criteria2 = parent_directory_at_level(__file__,
                                                    4) + "/Operational_Data/lbb/out/netx/roadGraph_criteria2.pickle"
    netx_path_criteria3 = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/netx/roadGraph.pickle"
    edges_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/final/edges.shp"
    nodes_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/final/nodes.shp"
    key_sites_path = parent_directory_at_level(__file__,
                                               4) + "/Operational_Data/lbb/lbb_rm_locations/lbb_rm_locations.shp"


class plcrDirectories(ParentDirectories):
    isotrack_path = ParentDirectories.isotrack_path
    isotrack_dict = {
        'ND_SH': f"{isotrack_path}/20191002-20200130_isotrak_legs_excl_5km_TRAIN_NATIONAL DC_SHEFFIELD MC.csv",
        'NT_EM': f"{isotrack_path}/20191002-20200130_isotrak_legs_excl_5km_TRAIN_NOTTINGHAM MC_EAST MIDLANDS AIRPORT.csv"
        }

    original_gdfs_path = f"{parent_directory_at_level(__file__, 4)}/Operational_Data/plcr/refined"

    out_path_criteria1 = parent_directory_at_level(__file__, 4) + "/Operational_Data/plcr/out/compare_to_telemetry" \
                                                                  "/criteria1"
    out_path_criteria2 = parent_directory_at_level(__file__, 4) + "/Operational_Data/plcr/out/compare_to_telemetry" \
                                                                  "/criteria2"
    out_path_criteria3 = parent_directory_at_level(__file__, 4) + "/Operational_Data/plcr/out/compare_to_telemetry" \
                                                                  "/criteria3"
    netx_path_criteria1 = parent_directory_at_level(__file__,
                                                    4) + "/Operational_Data/plcr/out/netx/roadGraph_criteria1.pickle"
    netx_path_criteria2 = parent_directory_at_level(__file__,
                                                    4) + "/Operational_Data/plcr/out/netx/roadGraph_criteria2.pickle"
    netx_path_criteria3 = parent_directory_at_level(__file__, 4) + "/Operational_Data/plcr/out/netx/roadGraph.pickle"
    edges_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/plcr/out/final/edges.shp"
    nodes_path = parent_directory_at_level(__file__, 4) + "/Operational_Data/plcr/out/final/nodes.shp"
