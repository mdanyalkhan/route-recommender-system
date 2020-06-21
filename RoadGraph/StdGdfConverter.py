from abc import ABC, abstractmethod
import geopandas as gpd
from RoadGraph.StdColNames import *


class NotToStandardColumnsError(Exception):
    def __init__(self, message="Generated dataframe is not to standards"):
        self.message = message
        super().__init__(self.message)


class StdGdfConverter(ABC):

    def __init__(self, srn_list=None):
        self.srn_list = srn_list
        self.std_column_names = [STD_ROAD_NO, STD_ROAD_TYPE, STD_LENGTH, STD_IS_SRN, STD_IS_DIREC]

    def convert_to_std_gdf(self, orig_gdf: gpd.GeoDataFrame, out_path: str = None) -> gpd.GeoDataFrame:
        """
        Overriding function that performs conversion of the original geospatial dataframe into the
        standardised dataframe.
        :param orig_gdf: Original (raw) geodataframe
        :param out_path: File path optional parameter if writing out of the standardised geodataframe is required
        :return: Standardised geodataframe
        """
        std_gdf = self._build_std_gdf(orig_gdf)

        if std_gdf.columns.tolist() != self.std_column_names:
            raise NotToStandardColumnsError

        if out_path is not None and type(out_path) == str:
            std_gdf.to_file(out_path)

        return std_gdf

    def convert_to_std_gdf_from_path(self, in_path: str, out_path: str = None) -> gpd.GeoDataFrame:
        """
        Function converts the shapefile saved at 'in_path' into a standardised geodataframe

        :param in_path: location of the target shapefile
        :param out_path: File path optional parameter if writing out of the standardised geodataframe is required
        :return: Standardised geodataframe
        """
        orig_gdf = gpd.read_file(in_path)
        return self.convert_to_std_gdf(orig_gdf, out_path)

    @abstractmethod
    def _build_std_gdf(self, orig_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Abstract function that performs the conversion of the original geodataframe into the standardised
        version. This is to be overloaded by subclasses.
        :param orig_gdf: Original (raw) geodataframe
        """
        pass
