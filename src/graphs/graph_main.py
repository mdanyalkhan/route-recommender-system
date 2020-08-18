from RoadGraph.util import *
import RoadGraph
import src.utilities.file_directories as fd


if __name__ == "__main__":

    edges = gpd.read_file(fd.LbbDirectories.edges_path)
    nodes = gpd.read_file(fd.LbbDirectories.nodes_path)
    net = RoadGraph.StdRoadGraphBuilder().create_graph(nodes, edges, weight_type='distance')
