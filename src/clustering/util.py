import numpy as np
import re

def haversine_np(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)

    All args must be of equal length.

    """
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2

    c = 2 * np.arcsin(np.sqrt(a))
    km = 6367 * c

    return km

def alpha_num_order(mystring):
    # """ Returns all numbers on 2 digits to let sort the string with numeric order.
    # """
    return ''.join([format(int(x), '02d') if x.isdigit() else x for x in re.split(r'(\d+)', mystring)])

def add_entity_type(row):
    if 'M' in row['road']:
        my_type = "motorway"
    else:
        my_type = "A-road"

    return my_type

def sort_list(my_list):
    return sorted(my_list, key=alpha_num_order)