from abc import ABC, abstractmethod
import geopandas as gpd
from RoadGraph.StdColNames import *


class StdGdfConverter(ABC):

    def __init__(self, srn_list=None):
        self.srn_list = srn_list

    def convert_to_std_gdf(self, orig_gdf: gpd.GeoDataFrame, out_path: str = None) -> gpd.GeoDataFrame:
        pass

    def convert_to_std_gdf_from_path(self, in_path: str, out_path: str = None) -> gpd.GeoDataFrame:
        pass

    @abstractmethod
    def _build_std_gdf(self, orig_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        pass
