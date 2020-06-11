from GeoDataFrameAux.geo_data_frame_builder import *


class GeoPointDataFrameBuilder(GeoDataFrameBuilder):

    def _build_geometry_object(self, coords: list):
        """
        Returns coords into a Point geometry object
        :param coords: list of tuples containing coordinates of Point object
        :return: line_string: LineString geometry object in string format
        """
        # convert to geometry line object

        return "POINT (" + str(coords[0]) + " " + str(coords[1]) + ")"
