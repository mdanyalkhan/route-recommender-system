from abc import ABC, abstractmethod
import geopandas as gpd


class ToStdConverter(ABC):

    @abstractmethod
    def convert_to_std_gdf(self, gdf: gpd.GeoDataFrame, roads_to_exclude=None) -> gpd.GeoDataFrame:
        pass

    @abstractmethod
    def convert_multiple_to_std_gdfs(self, in_path: str, out_path: str, roads_to_exclude=None) -> None:
        pass

    @abstractmethod
    def convert_multiple_and_merge_to_single_std_gdf(self, folder_path: str, roads_to_exclude=None) \
            -> gpd.GeoDataFrame:
        pass
