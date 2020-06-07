from src.graphs.geo_frame_builder.geo_data_frame_builder import *


class GeoPolyDataFrameBuilder(GeoDataFrameBuilder):

    def _build_geometry_object(self, coords: list):
        """
        Returns coords into a linestring geometry object
        :param coords: list of tuples containing coordinates of line object
        :return: poly_string: LineString geometry object in string format
        """

        # Ensure list of coordinates closed
        if coords[0] != coords[-1]:
            coords.append(coords[0])

        # convert to geometry polygon object
        poly_string = "POLYGON (("
        for index, coord in enumerate(coords):
            poly_string += str(coord[0]) + ' ' + str(coord[1])
            if index < len(coords) - 1:
                poly_string += ', '
        poly_string += "))"

        return poly_string