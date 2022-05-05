import pandas as pd
import requests 
import time
import os
from Config import cfg
from Tools import removeGPXFiles, Haversine, getRandomLocation
from HERErequest import  getTiles, getChargingStationsList
from HEREgraph2 import graphFromTileList
from Route import Route, getSigns


session = requests.Session()
#UPDATED_CODE_05052022

N_ROUTES = cfg.get('routes_number')
s_tiles = getTiles(cfg.get('gps_locations'),13, 13)
chargingStations = getChargingStationsList(s_tiles, session)

"""
id =[]
type=[]
lat=[]
lon=[]
for c in chargingStations:
    id.append(c)
    type.append(chargingStations[c]['CONNECTORTYPE'])
    lat.append(chargingStations[c]['LAT'])
    lon.append(chargingStations[c]['LON'])

d = {'TYPE':type,'LAT':lat,'LON':lon}
df=pd.DataFrame(data=d,index=id)
df.to_csv("/Users/humanrobot/Desktop/cs_filt_1.csv")
"""

feature_list = ["stop_signs","school_zone","icy_road","pedestrian","crosswalk","non_pedestrian_crossing","traffic_lights","traffic_signs",
                "lane_merge_right","lane_merge_left","lane_merge_center","highway","avoid_highway","oneway","both_ways","urban","limited_access",
                "paved","ramp","manoeuvre","roundabout","one_lane","multiple_lanes","overpass","underpass","variable_speed","railway_crossing",
                "no_overtaking","overtaking","falling_rocks","hills","tunnel","bridge","bump","dip","speed_bumps",
                "functional_class_1","functional_class_2","functional_class_3","functional_class_4","functional_class_5",
                "functional_class_1(hrs)","functional_class_2(hrs)","functional_class_3(hrs)","functional_class_4(hrs)","functional_class_5(hrs)"]
def createCSVFile():
    features_file_name = f"./gpx/summary.csv"
    head = ",".join([str(item) for item in feature_list])
    features_file = open(features_file_name, "w")
    features_file.write("route_num,route_length,route_estimated_time(hrs),"+head+"\n")
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
    
    #getSigns(g, cfg)
    #route = Route(cfg.get('route_type'), cfg.get('desired_route_length_km'), float(cfg.get('search_radius_km')),chargingStations, int(cfg.get('visit_charge_station')))
    #route.auxRoute(g, cfg.get('start_location'),cfg.get('end_location'))
    
    best_route = 0
    ref_rank_points = 0
    while(i < N_ROUTES):
        route_bool = False
        print(f"Route number {i}")
        route = Route(cfg.get('desired_route_length_km'),chargingStations, int(cfg.get('visit_charge_station')))
        while(route_bool == False):
            try:
                route.setRoute(g, start_node, end_node, mid_nodes)
                route_bool = True
            except:
                end_loc = getRandomLocation(cfg.get('start_location'), cfg.get('desired_route_length'))
                end_node, _ = g.findNodeFromCoord(end_loc)
        
        route.setGPXFile(g, i, "./gpx", cfg)       
        route.setCSVFeatures(g, i, units=cfg.get('units'))
        rank_points = route.getRankPoints()
        routes_list.append(route)
        if(rank_points > ref_rank_points):
            ref_rank_points=rank_points
            best_route=i
        i+=1
        print("")

    print(f"Best route was route number: {best_route}")
    end_time_03 = time.time()
  
    end_time = time.time()
    total_time = end_time - start_time
    tiles_time = end_time_01 - start_time_01
    graph_time = end_time_02 - start_time_02
    route_time = end_time_03 - start_time_03