import geopandas as gpd
from scipy.spatial import cKDTree

import RoadGraph
import numpy as np

edges_path = RoadGraph.parent_directory_at_level(__file__, 4) + "/Operational_Data/lbb/out/final/edges.shp"
isotrack_path = f'{RoadGraph.parent_directory_at_level(__file__, 4)}/Operational_Data/lbb/out/compare_to_telemetry/' \
                f'HW_SW/isotrack_all_paths.shp'

def generate_point_line_dict(edges_gdf: gpd.GeoDataFrame):

    points = edges_gdf['geometry'].apply(RoadGraph.extract_list_of_coords_from_geom_object).tolist()
    std_index = edges_gdf[RoadGraph.STD_INDEX].tolist()

    d = {}

    for i in range(len(points)):
        cur_line = std_index[i]
        line_of_points = points[i]
        for point in line_of_points:
            d[point] = cur_line

    return d

def find_edges_corresponding_to_isotrack_data(graph_point_map: dict, edges_gdf: gpd.GeoDataFrame,
                                              isotrack_data: gpd.GeoDataFrame):

    points = list(graph_point_map.keys())
    points_x = [point[0] for point in points]
    points_y = [point[1] for point in points]

    shortest_path_coords = np.dstack([points_x, points_y])[0]
    tree = cKDTree(shortest_path_coords)

    isotrack_coords = []
    for _, point in isotrack_data.iterrows():
        isotrack_coords.extend(RoadGraph.extract_list_of_coords_from_geom_object(point['geometry']))
    isotrack_x = [coord[0] for coord in isotrack_coords]
    isotrack_y = [coord[1] for coord in isotrack_coords]
    isotrack_coords = np.dstack([isotrack_x, isotrack_y])[0]

    _, indices = tree.query(isotrack_coords, k=1)
    indices = list(set(indices))

    return indices

if __name__ == '__main__':
    edges_gdf = gpd.read_file(edges_path)
    isotrack_gdf = gpd.read_file(isotrack_path)

    d = generate_point_line_dict(edges_gdf)
    find_edges_corresponding_to_isotrack_data(d, edges_gdf, isotrack_gdf)