from shapely.geometry import MultiLineString


def extract_list_of_coords_from_geom_object(geom_object) -> [(int, int)]:
    """
    Returns a list version of the coordinates stored in line_object
    :param geom_object: Either a LineString or MultiLineString object
    :return: list of coordinates of line_object
    """
    list_of_coords = []
    if type(geom_object) is MultiLineString:
        list_of_lines = list(geom_object)
        for line in list_of_lines:
            list_of_coords.extend(list(line.coords))
    else:
        list_of_coords = list(geom_object.coords)
    return list_of_coords

def extract_coord_at_index(geom_object, index: int) -> (float, float):
    """
    Returns the coordinates from a LineString or MultiLineString object
    :param geom_object: LineString or MultilineString object
    :param index: index of the line_object to extract coordinates from
    :return coordinates in a tuple from line_object at index
    """

    list_of_coords = extract_list_of_coords_from_geom_object(geom_object)
    return list_of_coords[index]