
#Standardised Roads geodataframe column names
STD_CLASS_NAME = "CLASS_NAME"
STD_ROAD_NO = "ROA_NUMBER"
STD_SECT_LABEL = "SECT_LABEL"
STD_LOCATION = "LOCATION"
STD_START_DATE = "START_DATE"
STD_END_DATE = "S_END_DATE"
STD_LENGTH = "SEC_LENGTH"
STD_FUNCT_NAME = "FUNCT_NAME"
STD_AREA_NAME = "AREA_NAME"
STD_DIRECTION = "DIREC_CODE"
STD_PERM_LANES = "PERM_LANES"
STD_CARRIAGEWAY_TYPE = "DUAL_NAME"
STD_ENVIRONMENT = "ENVIR_NAME"
STD_AUTHORITY = "AUTHO_NAME"
STD_REFERENCE = "REFERENCE"

#OS_open_roads geodataframe column names
OS_ID = "identifier"
OS_CLASS = "class"
OS_ROAD_NO = "roadNumber"
OS_LENGTH = "length"
OS_FUNCT_NAME = "formOfWay"


#Additional column names to be added to the geodataframe
INDEX = "INDEX"
PREV_IND = "PREV_IND"
NEXT_IND = "NEXT_IND"
FIRST_COORD = "FIRST_COORD"
LAST_COORD = "LAST_COORD"
FROM_NODE = "FROM_NODE"
TO_NODE = "TO_NODE"
GEOMETRY = "geometry"
IS_DIRECTIONAL = "IS_DIREC"
#Key string variables in HE dataframe
STD_MAIN_CARRIAGEWAY = "Main Carriageway"
STD_SLIP_ROAD = "Slip Road"
STD_ROUNDABOUT = "Roundabout"
STD_LAYBY = "Ox Bow Lay-by"
STD_NONE = "None"

#Key string variables in OS dataframe
OS_MOTORWAY = "Motorway"
OS_A_ROAD = "A Road"
OS_MAIN_CARRIAGEWAY_LIST = ["Single Carriageway", "Dual Carriageway",
                            "Collapsed Dual Carriageway", "Shared User Carriageway"]
OS_SLIP_ROAD = "Slip Road"
OS_ROUNDABOUT = "Roundabout"

#Nodes Geodataframe column names
N_NODE_ID = "node_id"
N_TYPE = "Type"
N_ROUNDABOUT_EXTENT = "Extent"
N_COORD = "Coord"

#Node type names
N_ROUNDABOUT = "Roundabout"
N_JUNCTION = "Junction"
N_DEAD_END = "Dead End"


