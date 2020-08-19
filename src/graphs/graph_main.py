from RoadGraph.util import *
import RoadGraph
import src.utilities.file_directories as fd
from src.utilities.aux_func import parent_directory_at_level, loadNetworkResults

if __name__ == "__main__":

   # route_edges_path = f"{parent_directory_at_level(__file__, 4)}/Operational_Data/lbb/reduced/HW_SW/road_graph/edges.shp"
   # route_nodes_path = f"{parent_directory_at_level(__file__, 4)}/Operational_Data/lbb/reduced/HW_SW/road_graph/nodes.shp"
   route_net_path = f"{parent_directory_at_level(__file__, 4)}/Operational_Data/lbb/reduced/HW_SW/road_graph/roadGraph.pickle"
   key_sites = f"{parent_directory_at_level(__file__, 4)}/Operational_Data/rm_sites/rm_locations.shp"
   route_graph = loadNetworkResults(route_net_path)

   route_graph.set_road_closure('A_683', 'A_684')
   route_graph.set_road_closure('A_1081','A_1080')
   route_graph.set_road_closure('F_1510', 'F_1507')
   _, _, s_edges, s_nodes = route_graph.shortest_path_between_key_sites('HEATHROW WORLDWIDE DC', 'SOUTH WEST DC',
                                                                        gpd.read_file(key_sites), 'location_n',
                                                                        get_gdfs=True)

   s_edges.to_file(f"{parent_directory_at_level(__file__, 4)}/Operational_Data/lbb/reduced/HW_SW/shortest_path_sample/edges.shp")
   s_nodes.to_file(f"{parent_directory_at_level(__file__, 4)}/Operational_Data/lbb/reduced/HW_SW/shortest_path_sample/nodes.shp")

