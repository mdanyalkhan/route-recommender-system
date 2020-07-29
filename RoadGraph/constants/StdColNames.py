"""
Equivalent to an enum file, containing the column names of the standard geodataframe used to build the road graph
"""
#Edges column names
STD_INDEX = 'INDEX'
STD_ROAD_NO = "ROAD_NO"
STD_ROAD_TYPE = "ROAD_TYPE"
STD_FORMOFWAY = "FORM_OF_WA"
STD_SPEED = "Speed"
STD_LENGTH = "Length"
STD_IS_SRN = "IS_SRN"
STD_IS_DIREC = "IS_DIREC"
STD_GEOMETRY = "geometry"
STD_FROM_NODE = "FROM_NODE"
STD_TO_NODE = "TO_NODE"
STD_PREV_IND = "PREV_IND"
STD_NEXT_IND = "NEXT_IND"

#Nodes Geodataframe column names
STD_NODE_ID = "node_id"
STD_N_TYPE = "Type"
STD_N_ROUNDABOUT_EXTENT = "Extent"

#Netx attr dataframe column names
STD_Nx_ATTR = 'attr'
STD_Nx_ROAD_ID = "road_id"
STD_Nx_LENGTH = "length"
STD_Nx_TIME = "time"
STD_Nx_ROAD_IND = "road_segment_indices"
STD_Nx_WEIGHT = "weight"
STD_Nx_IS_SRN = "is_srn"