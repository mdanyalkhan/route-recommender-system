# Route Recommender System
This project explores the applicability of graphs as a potential 
means of designing a route recommender system suitable for Royal Mail
Heavy Goods Vehicles. 

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

## Usage

All classes and functions used in this project are primarily included
within the `RoadGraph` python package, this includes the following:

* `stdroadgraph` module
* `util` module
* `preprocessing` package
* `graphreduce` package
* `analysis` package

### `stdroadgraph` Module

This module holds the `StdRoadGraph` class, which, if instantiated,
represents a graph instant of the UK road network. The class provides
functions designed to identify the shortest paths between any given
node pair, and also allows the user to determine key properties
of the graph.

```
#Instantiation of an StdRoadGraph
edges_gdf <- #Geopandas standardised DataFrame of the graph edges
nodes_gdf <- #Some geopandas standardised DataFrame of the graph nodes
net <- #Corresponding networkx.DiGraph object of road graph

road_graph = StdRoadGraph(net, nodes_gdf, edges_gdf) 
```
