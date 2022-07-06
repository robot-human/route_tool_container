import os
import networkx as nx 
import requests
from requests.sessions import session
import numpy as np
from HERErequest import getLinksFromTile
from multiprocessing import Pool
from functools import partial

#from HERErequest import coordsToTile, getTileRequest,  displayUsageCount, incrementApiCount, getLinksFromTile
#from Tools import getIdxList, getSubDict, getIdxListCount
#from multiprocessing import Pool
#from functools import partial

#from myThread import myThread
#import random
#level_layerID_map = {9:1, 10:2, 11:3, 12:4, 13:5}


def graphFromDict(links_dict: dict):
    g = HEREgraph()
    drop_ids = []
    for link_id in links_dict:
        attr = links_dict[link_id]
        try:
            link_direction = attr['TRAVEL_DIRECTION']
            ref_node_id = int(attr['REF_NODE_ID'])
            nonref_node_id = int(attr['NONREF_NODE_ID'])
            lat = attr['LAT'].split(',')
            lon = attr['LON'].split(',')
            if(len(lat) > 2):
                print(len(lat),len(lon))
            if link_direction == 'B':
                attr['EDGE_DIRECTION'] = 'F'
                g.add_edge(ref_node_id, nonref_node_id, int(link_id), **attr)
                attr['EDGE_DIRECTION'] = 'T'
                g.add_edge(nonref_node_id, ref_node_id, int(link_id), **attr)
            if link_direction == 'F':
                attr['EDGE_DIRECTION'] = 'F'
                g.add_edge(ref_node_id, nonref_node_id, int(link_id), **attr)
            if link_direction == 'T':
                attr['EDGE_DIRECTION'] = 'T'
                g.add_edge(nonref_node_id, ref_node_id, int(link_id), **attr)
            g.add_node(ref_node_id, LOC=(int(lat[0])/(10.0**5),int(lon[0])/(10.0**5)))
            #for i in range(1,len(lat)):
            g.add_node(nonref_node_id, LOC=((int(lat[0])+int(lat[1]))/(10.0**5), (int(lon[0])+int(lon[1]))/(10.0**5))) 
        except:
            drop_ids.append(link_id)                          
    return g
    
def getGraphFromTile(tile: tuple, cfg: dict, session: requests.Session=None):
    if not session: session = requests.Session() 
    links_dict = getLinksFromTile(tile, cfg, session)
    graph = graphFromDict(links_dict)
    return graph 

def graphFromTileList(tiles: list, query: dict, session):
    ng = HEREgraph()
    #with Pool(processes=4) as p:
    #    part = partial(getGraphFromTile, session=session)
    #    for tile in tiles:
    #        new_graph = p.map(part, tile, query)
    #        ng.updateGraph(new_graph)
    
    for tile in tiles:
        new_graph = getGraphFromTile(tile, query, session=session)
        ng.updateGraph(new_graph)
    return ng

#HERE graph class, extends MultiDiGraph from nx library
class HEREgraph(nx.MultiDiGraph):

    def __init__(self, incoming_graph_data=None, **attr):
        super().__init__(incoming_graph_data=incoming_graph_data, **attr)
        return None

    def addToCache(self, tile: tuple, cache_path: str):
        cache_file_path = os.path.join(cache_path, f'{tile[0]}-{tile[1]}-{tile[2]}.pickle')
        nx.write_gpickle(self, cache_file_path)
        return None
        
    def updateGraph(self, new_graph: nx.MultiDiGraph):
        self.add_edges_from([(e[0], e[1], e[2], new_graph[e[0]][e[1]][e[2]]) for e in new_graph.edges])
        self.add_nodes_from(new_graph.nodes.data())
        return None
        
    def saveEdgesToNumpy(self):
        self.np_edges = np.array(list(self.edges))
        return None
    
    def saveNodesToNumpy(self):        
        self.np_nodes_data = np.array([(data[0], data[1]['LOC'][0], data[1]['LOC'][1]) for data in self.nodes.data()])
        return None
      
    def findNodeFromCoord(self, loc: tuple):
        node_coord = np.array(loc)
        temp = self.np_nodes_data[:, 1:] - node_coord
        temp2 = temp * temp
        distance = temp2[:, 0] + temp2[:, 1]
        min_id = np.argmin(distance)
        minimum_distance = distance[min_id] ** 0.5
        return int(self.np_nodes_data[min_id, 0]), minimum_distance  
