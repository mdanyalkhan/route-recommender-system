from enum import Enum

class ColumnNames(Enum):
    EVENT_DTTM = "Event_Dttm"
    FROM_DEPOT = "from_depot"
    TO_DEPOT = "to_depot"
    CLUSTER = "cluster"
    CLUSTER_ID = "cluster_id"
    LEG_ID = "leg_id"
    EVENT_LAT = "Event_Lat"
    EVENT_LONG = "Event_Long"
    LINK_NAME = "link_name"
    C_WAY = "c_way"
    SECTION = "section"
    ROAD_TYPE = "road_type"
    ENTITY = "entity"
    REPRESENTATIVE = "reduce_flag"
    OVERNIGHT = 'Overnight'
    START_TIME = "start_time"
    END_TIME = "end_time"
    ENTITIES = "entities"
    ENTITY_LIST = "entity_list"
    RUNTIME = "runtime"
    MIN_RUNTIME = "min_runtime"
    MAX_RUNTIME = "max_runtime"
    MEDIAN_RUNTIME = "median_runtime"
    MEAN_RUNTIME = "mean_runtime"
    COUNT_RUNTIME = "count_runtime"
    MIN_RUNTIME_FT = "min_runtime_filter"
    MAX_RUNTIME_FT = "max_runtime_filter"
    MEDIAN_RUNTIME_FT = "median_runtime_filter"
    MEAN_RUNTIME_FT = "mean_runtime_filter"
    COUNT_RUNTIME_FT = "count_runtime_filter"
    COUNT_LEG_ID_FT = "count_leg_id_filter"
    HOUR_DEPARTED = 'Hour_departed'
    UNIQUE = "unique"
    COUNT_LEG_ID = "count_leg_id"



