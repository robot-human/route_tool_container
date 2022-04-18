import requests 
import time
import os
from Config import cfg
from Tools import removeGPXFiles, Haversine, getRandomLocation
from HERErequest import  getTiles, getChargingStationsList
from HEREgraph2 import graphFromTileList
from Route import Route, getSigns



session = requests.Session()
#UPDATED_CODE_31012022

N_ROUTES = 5
s_tiles = getTiles(cfg.get('gps_locations'),13, 13)
chargingStations = getChargingStationsList(s_tiles, session)

feature_list = ["stop_signs","school_zone","icy_road","pedestrian","crosswalk","non_pedestrian_crossing","traffic_lights","traffic_signs",
                "lane_merge_right","lane_merge_left","lane_merge_center","highway","avoid_highway","oneway","both_ways","urban","limited_access",
                "paved","ramp","manoeuvre","roundabout","one_lane","multiple_lanes","overpass","underpass","variable_speed","railway_crossing",
                "no_overtaking","overtaking","falling_rocks","hills","tunnel","bridge"]
def createCSVFile():
    features_file_name = f"./gpx/features_count.csv"
    head = ",".join([str(item) for item in feature_list])
    features_file = open(features_file_name, "w")
    features_file.write("route_num,route_length,route_estimated_time,"+head+"\n")
    features_file.close()

if __name__ == '__main__':
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
    #print("")
    #print(f"Minimum distance between start and end point = {Haversine(cfg.get('start_location'), cfg.get('end_location'))}")
    #print(f"Desired route length = {cfg.get('desired_route_length_km')}")
    #print("")
    start_node, _ = g.findNodeFromCoord(cfg.get('start_location'))
    end_node, _ = g.findNodeFromCoord(cfg.get('end_location'))
    routes_list = list()
    i = 0
    
    getSigns(g, cfg)
    #route = Route(cfg.get('route_type'), cfg.get('desired_route_length_km'), float(cfg.get('search_radius_km')),chargingStations, int(cfg.get('visit_charge_station')))
    #route.auxRoute(g, cfg.get('start_location'),cfg.get('end_location'))
    
    best_route = 0
    ref_rank_points = 0
    while(i < N_ROUTES):
        print(f"Route number {i}")
        route = Route(cfg.get('route_type'), cfg.get('desired_route_length_km'), float(cfg.get('search_radius_km')),chargingStations, int(cfg.get('visit_charge_station')))
        route.setRoute(g, start_node, end_node)
        route.setCSVFeatures(g, i)
        route.setGPXFile(g, i, "./gpx", cfg)
        rank_points = route.getRankPoints()
        routes_list.append(route)
        if(rank_points > ref_rank_points):
            ref_rank_points=rank_points
            best_route=i
        i+=1
        print("")

    print(f"Best route was route number: {best_route}")
    #routes_list[best_route].setGPXFile(g, 0, "gpx")
    end_time_03 = time.time()
  
    end_time = time.time()
    total_time = end_time - start_time
    tiles_time = end_time_01 - start_time_01
    graph_time = end_time_02 - start_time_02
    route_time = end_time_03 - start_time_03

    #print("")
    #print(f'Total time {total_time}')
    #print(f'Tiles time {tiles_time}')
    #print(f'Graph time {graph_time}')
    #print(f'Route time {route_time}')
    