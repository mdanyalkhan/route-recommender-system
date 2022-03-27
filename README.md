# Route Recommender System
This project explores the applicability of graphs as a potential 
means of designing a route recommender system suitable for Royal Mail
Heavy Goods Vehicles.

Note that this repo was part of a university project that I undertook during my MSc in Computing - the repo is no longer actively maintained.

## Pre-requisites

The following Python libraries are required beforehand in order to 
use the various functions and classes developed in this project:

* Networkx v2.4
* Pandas v1.0.3
* Geopandas v0.6.1
* Shapely v1.7.0
* Numpy v1.18.1
* Matplotlib v3.1.3
* Scipy v1.5.1

The following data sets are also required to be able to immediately
make use of the functions and classes developed in this project:

* OS roads data: https://www.ordnancesurvey.co.uk/business-government/products/open-map-roads
* Built-up areas data: https://geoportal.statistics.gov.uk/datasets/built-up-areas-december-2011-boundaries-v2/geoservice

**Note**: This project is based on the unix operating system. Although
it is still possible to build a road graph, its full capabilities 
will not be available if this project is downloaded on a Windows 
Operating System.

## Summary of Capabilities

All classes and functions used in this project are primarily included
within the `RoadGraph` python package, this includes the following:

* `stdroadgraph` module
* `util` module
* `preprocessing` package
* `graphreduce` package
* `analysis` package

## `stdroadgraph` Module

This module holds the `StdRoadGraph` class, which, if instantiated,
represents a graph instant of the UK road network. The class provides
functions designed to identify the shortest paths between any given
node pair, and also allows the user to determine key properties
of the graph.

```
#Instantiation of an StdRoadGraph
edges_gdf <- #Geopandas standardised DataFrame of the graph edges
nodes_gdf <- #Geopandas standardised DataFrame of the graph nodes
net <- #Corresponding networkx.DiGraph object of road graph

road_graph = StdRoadGraph(net, nodes_gdf, edges_gdf) 

#Find the shortest path between two nodes
path, cost = road_graph.shortest_path_between_nodes(source_node = 'A', target_node = 'B')
path, cost, path_edges_gdf, path_nodes_gdf = road_graph.shortest_path_between_nodes('A', 'B', get_gdfs=True)

#Set temporary road closure and calculate shortest path
road_graph.set_road_closure(from_node='A', to_node='B')
path, cost = road_graph.shortest_path_between_nodes('E', 'F')
road_graph.remove_road_closure(from_node='A', to_node='B')
```

## `preprocessing` package
This package offers the following set of classes:

* `StdGdfConverter` - an abstract class designed to convert
all geo-spatial data frames into a standardised format. This
class can be overridden by a child class with specific
functions that enable the conversion of a specific geo-spatial 
data set to the standardised format.
* `OSToStdGdfConverter` - a child class of `StdGdfConverter`, designed
specifically for the OS Open Roads data set.
* `StdNodesEdgesGdfBuilder` - constructs the edges and nodes 
data frames based on the inputted standardised roads data set.
* `StdNodesEdgesGdfConnector` - Merges multiple adjacent nodes and
edges data frames into a single pair of connected data frames.
* `StdRoadGraphBuilder` - Builds the `StdRoadGraph` object. 
Also builds the `networkx.DiGraph` object based 
on the nodes and edges data frames. 

Under a Unix-based Operating System, the following single function
needs to be executed using a single geo-spatial data set:

```
in_path <- path containing the target geo-spatial shapefile
out_path <- path to save intermediate results and final road graph
builder = StdRoadGraphBuilder()

road_graph = builder.build_road_graph(in_path, out_path)
```

Note that if more than one shapefile will be used to build the 
the road graph object, the following pre-processing function
may be necessary to run beforehand, particularly if they
are the OS Open Roads data set (where overlap between 
adjacent tiles is prevalent):

```
util.filter_minor_roads_and_remove_duplicates_from_os_roads(in_path, out_path)
road_graph = builder.build_road_graph(in_path, out_path)
```

Under a Windows Operating System, the `build_road_graph` function
is unlikely to work, notwithstanding this, a road graph
can still be generated as shown here:

```
util.filter_minor_roads_and_remove_duplicates_from_os_roads(in_path, out_path)
orig_gdf = geopandas.read_file(out_path)
std_gdf = OSToStdGdfConverter().convert_to_std_gdf(orig_gdf)
edges, nodes = StdNodesEdgesGdfBuilder().build_nodes_and_edges_gdf(std_gdf)
net = StdRoadGraphBuilder().create_graph(nodes, edges)
road_graph = StdRoadGraph(net, nodes, edges)
```

## `graphreduce` package
This package offers the two following classes to convert
the underlying road graph into the set of nodes and edges
corresponding to the routes identified within a 
Royal Mail telemetry data set. 

* `RoadAssignment` - Assigns the nearest node to every ping in the
given telemetry data set.
* `RoutesGraph` - Generates a reduced road graph based
purely on the routes identified within the given
telemetry data set. 

```
isotrack_data <- Royal Mail telemetry data set
edges_gdf <- #Geopandas standardised DataFrame of the graph edges
nodes_gdf <- #Geopandas standardised DataFrame of the graph nodes
RoadAssignment().assign_nearest_nodes(isotrack_data, edges_gdf, nodes_gdf)
routes_graph = RoutesGraph().generate_stdRoadGraph_from_isotrack(isotrack_data, road_graph) 
```

## `analysis` package

This package offers the following two modules that enable us 
to conduct vulnerability analysis of the road graph:

* `vulnerabilityanalyser` - this module provides the 
`VulnerabilityAnalyser` class, which provides
functions that actively identify critical road sections
within the road network.

```
key_sites <- #Geopandas dataframe of Royal Mail Key sites
vuln_analyser = VulnerabilityAnalyser(road_graph)
node_results = vuln_analyser.srn_vulnerability_two_sites_nodes(key_sites, 'location_name', 'site_a', 'site_b')
grid_results = vuln_analyser.srn_vulnerability_two_sites_grid(key_sites, 'location_name', 'site_a', 'site_b',
                                                              dimension_km=2.0)
```

* `closureanalysis` - Provides the series of functions to calculate
the impact the planned set of road closures have on the
journey times between any given depot pair.

The following is  a sample application of the functions in `closureanalysis`

```
closure_path <- path to folder containing list of shapefile edges representing
                the set of planned road closures.
results_mat, results_dict = journey_time_impact_closure_shp_path(road_graph, key_sites, closure_path)
output_res_dict_to_csv(results_dict, out_path)
output_res_dict_shortest_path_as_shp(road_graph, results_dict, out_path)
```
