
class RoadGraph:

    def __init__(self, netx_graph, nodes_gdf, edges_gdf):
        self.net = netx_graph
        self.nodes = nodes_gdf
        self.edges = edges_gdf