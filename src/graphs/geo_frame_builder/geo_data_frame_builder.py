import pandas as pd
import geopandas as gpd
from shapely import wkt

class GeoDataFrameBuilder(object):
    """
    An abstract geo_frame_builder class used to build  geodataframe
    """

    def build_geo_frame(self, coords: list, crs: str):
        """
        Abstract function to build geo dataframe
        :param coords: coordinates to use to build basic dataframe
        :param crs: coordinate system of geometry
        """
        geom_str = self._build_geometry_object(coords)
        df = pd.DataFrame(
            {'id': [1],
             "geometry": [geom_str]})

        df['geometry'] = df['geometry'].apply(wkt.loads)
        gdf = gpd.GeoDataFrame(df, geometry='geometry')
        gdf.crs = {'init': crs}
        return gdf

    def _build_geometry_object(self, coords: list):
        pass
