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
#UPDATED_CODE_01062022

N_ROUTES = cfg.get('routes_number')
s_tiles = getTiles(cfg.get('gps_locations'),13, 13)
chargingStations = getChargingStationsList(s_tiles, session)

def createCSVFile():
    features_file_name = f"./temp/summary.csv"
    head = ",".join([str(item) for item in feature_dict])
    head = head +',functional_class_1_time'+',functional_class_2_time'+',functional_class_3_time'+',functional_class_4_time'+',functional_class_5_time'
    features_file = open(features_file_name, "w")
    features_file.write("route_length,route_estimated_time(hrs),"+head+"\n")
    features_file.close()

if __name__ == '__main__':
    tracemalloc.start()
    start_time = time.time()
    
    removeGPXFiles("./temp/")
    removeGPXFiles("./gpx/")
    createCSVFile()
    session = requests.Session()


    start_time_01 = time.time()
    tiles = getTiles(cfg.get('gps_locations'),9, 13)
    end_time_01 = time.time()
    print("Get tiles time: ",end_time_01/3600)

    start_time_02 = time.time()
    g = graphFromTileList(tiles, cfg, session) 
    
    g.saveEdgesToNumpy()
    g.saveNodesToNumpy()
    end_time_02 = time.time()/3600.0
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
        
        route.setGPXFile(g, i, "./temp", cfg)       
        route.setCSVFeatures(g, i, units=cfg.get('units'))
        rank_points = route.getRankPoints()
        values.append((i,rank_points))
        i+=1

    routes_ranking_points = np.array(values, dtype=dtype)
    routes_ranking_points = np.sort(routes_ranking_points, order='points')  
    summary_file = open(f'./temp/summary.csv', "r")
    summary =  open(f'./gpx/summary.csv', "w")
    lines = summary_file.readlines()
    lines_array = []
    for line in lines:
        lines_array.append(line)
    summary_file.close()
    summary.write('route_num,'+lines_array[0])
    for i in range(N_ROUTES):
        n = routes_ranking_points[len(routes_ranking_points)-i-1][0]
        summary.write(str(i)+','+lines_array[n+1])
        csv_file = open(f'./temp/route{n}_staticfeaturesfile.csv', "r")
        f =  open(f'./gpx/route{i}_staticfeaturesfile.csv', "w")
        f.write(csv_file.read())
        f.close()
        csv_file.close()

        gpx_file = open(f'./temp/route{n}_staticfeaturesfile.gpx', "r")
        f =  open(f'./gpx/route{i}_staticfeaturesfile.gpx', "w")
        f.write(gpx_file.read())
        f.close()
        gpx_file.close()
    summary.close()

    


    end_time_03 = time.time()
  
    end_time = time.time()
    total_time = end_time - start_time
    tiles_time = end_time_01 - start_time_01
    graph_time = end_time_02 - start_time_02
    route_time = end_time_03 - start_time_03
    tracemalloc.stop()