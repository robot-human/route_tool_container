import numpy as np
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
#UPDATED_CODE_25052022

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
    print("Get tiles time: ",end_time_01)

    start_time_02 = time.time()
    g = graphFromTileList(tiles, cfg['query_features'], session) 
    
    g.saveEdgesToNumpy()
    g.saveNodesToNumpy()
    end_time_02 = time.time()
    print("Graph time: ",end_time_02)
    
    
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
        
    dtype = [('route', int), ('points', int)]
    values = []
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
        rank_points = route.getRankPoints()
        values.append((i,rank_points))

        i+=1

    routes_ranking_points = np.array(values, dtype=dtype)
    routes_ranking_points = np.sort(routes_ranking_points, order='points')  
    print(routes_ranking_points)
    end_time_03 = time.time()
  
    end_time = time.time()
    total_time = end_time - start_time
    tiles_time = end_time_01 - start_time_01
    graph_time = end_time_02 - start_time_02
    route_time = end_time_03 - start_time_03
    tracemalloc.stop()