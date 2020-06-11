from geodataframebuilder.geo_data_frame_builder import *


class GeoLineDataFrameBuilder(GeoDataFrameBuilder):

    def _build_geometry_object(self, coords: list):
        """
        Returns coords into a linestring geometry object
        :param coords: list of tuples containing coordinates of line object
        :return: line_string: LineString geometry object in string format
        """
        # convert to geometry line object
        line_string = "LINESTRING ("
        for index, coord in enumerate(coords):
            line_string += str(coord[0]) + ' ' + str(coord[1])
            if index < len(coords) - 1:
                line_string += ', '
        line_string += ")"

        return line_string
