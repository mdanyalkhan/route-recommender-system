
#HE roads geodataframe column names
HE_CLASS_NAME = "CLASS_NAME" #Use Class to determine whether A or M
HE_ROAD_NO = "ROA_NUMBER" #Use roadNumber
HE_SECT_LABEL = "SECT_LABEL" #Set to NULL
HE_LOCATION = "LOCATION" #Set to NULL
HE_START_DATE = "START_DATE" #Set to NULL
HE_END_DATE = "S_END_DATE" #Set to NULL
HE_LENGTH = "SEC_LENGTH" #Set to length
HE_FUNCT_NAME = "FUNCT_NAME" #Use formOfWay
HE_AREA_NAME = "AREA_NAME" #Set to NULL
HE_DIRECTION = "DIREC_CODE" #Set to NULL
HE_PERM_LANES = "PERM_LANES" #Set to NULL
HE_CARRIAGEWAY_TYPE = "DUAL_NAME" #Set to formOfWay
HE_ENVIRONMENT = "ENVIR_NAME" #set to NULL
HE_AUTHORITY = "AUTH_NAME" #Set to NULL
HE_REFERENCE = "REFERENCE" #Use identifier

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

#Key string variables in HE dataframe
HE_MAIN_CARRIAGEWAY = "Main Carriageway"
HE_SLIP_ROAD = "Slip Road"
HE_ROUNDABOUT = "Roundabout"
HE_NONE = "None"

#Key string variables in OS dataframe
OS_MOTORWAY = "Motorway"
OS_A_ROAD = "A Road"
OS_MAIN_CARRIAGEWAY_LIST = ["Single Carriageway", "Dual Carriageway",
                            "Collapsed Dual Carriageway", "Shared User Carriageway"]
OS_SLIP_ROAD = "Slip Road"
OS_ROUNDABOUT = "Roundabout"

#Nodes Geodataframe column names
NODE_ID = "node_id"


