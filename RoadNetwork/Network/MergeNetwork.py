
# Start with nodes in SRN Network
# Filter by roundabouts first
#Drop all roads in OS that is already included in the SRN database
#For every roundabout
    # Filter os data by dead end nodes
    # Calculate proximity of dead end nodes to roundabout coordinate
    # Where dead end nodes are below some threshold:
        #Set all From_Node and To_node in edges database to the roundabout node
        #Drop dead end nodes from database
#Filter by dead nodes in SRN Network
    #For every dead end node:
    #Calculate proximity of nodes with respect to this dead end node
    #If below some proximity:
        #Set edges databases containing these nodes to the dead end node
        #Delete these nodes

#Perform the same operation for the OS Network database
#Once complete, then merge nodes and edges databases into one.
