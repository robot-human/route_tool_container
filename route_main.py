import pandas as pd
import requests 
import time
import os
from Config import cfg
from Tools import removeGPXFiles, Haversine, getRandomLocation
from HERErequest import  getTiles, getChargingStationsList
from HEREgraph2 import graphFromTileList
from Route import Route, getSigns
from resources import feature_dict
import tracemalloc


session = requests.Session()
#UPDATED_CODE_05052022

N_ROUTES = cfg.get('routes_number')
s_tiles = getTiles(cfg.get('gps_locations'),13, 13)
chargingStations = getChargingStationsList(s_tiles, session)

def createCSVFile():
    features_file_name = f"./gpx/summary.csv"
    head = ",".join([str(item) for item in feature_dict])
    features_file = open(features_file_name, "w")
    features_file.write("route_num,route_length,route_estimated_time(hrs),"+head+"\n")
    features_file.close()

if __name__ == '__main__':
    tracemalloc.start()
    start_time = time.time()
    
    removeGPXFiles("./gpx/")
    createCSVFile()
    session = requests.Session()

    start_time_01 = time.time()
    tiles = getTiles(cfg.get('gps_locations'),9, 13)
    end_time_01 = time.time()

    start_time_02 = time.time()
    g = graphFromTileList(tiles, cfg['query_features'], session) 
    
    g.saveEdgesToNumpy()
    g.saveNodesToNumpy()
    end_time_02 = time.time()
    
    
    start_time_03 = time.time()
    start_node, _ = g.findNodeFromCoord(cfg.get('start_location'))

    if(cfg.get('route_type') == 'point_to_anywhere'):
        end_loc = getRandomLocation(cfg.get('start_location'), cfg.get('desired_route_length'))
        end_node, _ = g.findNodeFromCoord(end_loc)
    else:
        end_node, _ = g.findNodeFromCoord(cfg.get('end_location'))
    mid_nodes = []
    for loc in cfg.get('mid_locations'):
        mid_n, _ = g.findNodeFromCoord(loc)
        mid_nodes.append(mid_n)

    routes_list = list()
    i = 0
        
    best_route = 0
    ref_rank_points = 0
    while(i < N_ROUTES):
        route_bool = False
        print(f"Route number {i}")
        route = Route(cfg.get('desired_route_length_km'),chargingStations, int(cfg.get('visit_charge_station')))
        while(route_bool == False):
            #try:
            route.setRoute(g, start_node, end_node, mid_nodes)
            route_bool = True
            #except:
            #    print("except route")
            #    end_loc = getRandomLocation(cfg.get('start_location'), cfg.get('desired_route_length'))
            #    end_node, _ = g.findNodeFromCoord(end_loc)
        
        route.setGPXFile(g, i, "./gpx", cfg)       
        route.setCSVFeatures(g, i, units=cfg.get('units'))
        #rank_points = route.getRankPoints()
        #print(100*tracemalloc.get_traced_memory()[0]/tracemalloc.get_traced_memory()[1])
        #route.clean()
        #print(100*tracemalloc.get_traced_memory()[0]/tracemalloc.get_traced_memory()[1])
        #del route
        #print(100*tracemalloc.get_traced_memory()[0]/tracemalloc.get_traced_memory()[1])
        #if(rank_points > ref_rank_points):
        #    ref_rank_points=rank_points
        #    best_route=i
        i+=1
        #print("")

    #print(f"Best route was route number: {best_route}")
    end_time_03 = time.time()
  
    end_time = time.time()
    total_time = end_time - start_time
    tiles_time = end_time_01 - start_time_01
    graph_time = end_time_02 - start_time_02
    route_time = end_time_03 - start_time_03
    tracemalloc.stop()