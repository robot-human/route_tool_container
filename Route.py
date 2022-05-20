#from re import S
from HEREgraph2 import HEREgraph
import numpy as np
import networkx as nx
import gpxpy
import os
from Tools import Haversine, getRandomLocation, distance
import pandas as pd
import datetime
import time
from resources import feature_dict,traffics_sign_dict,traffic_condition_dict,lane_divider_dict,lane_type


def getSigns(G, cfg):
    gpx = gpxpy.gpx.GPX()
    nodes = list(G.nodes)
    signs_list = []
    for i in range(1, len(nodes)):
        link_data = G.get_edge_data(nodes[i-1],nodes[i])
        if(link_data != None):
            loc_1 = G.nodes[nodes[i-1]]['LOC']
            loc_2 = G.nodes[nodes[i]]['LOC']
            link_id = list(link_data.keys())[0]
            link_attributes = link_data[link_id]
            if(link_attributes["TUNNEL"] != None):
                if('Y' in link_attributes["TUNNEL"]):
                    gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc_1[0], loc_1[1], name=f"Tunnel"))
            if(link_attributes["BRIDGE"] != None):
                if('Y' in link_attributes["BRIDGE"]):
                    gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc_1[0], loc_1[1], name=f"Bridge"))    
            if(len(link_attributes["TRAFFIC_CONDITION_T"]) > 0):
                sign = link_attributes["TRAFFIC_CONDITION_T"][0]
                signs_list.append([link_id,loc_2,loc_1])
                gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc_1[0], loc_1[1], name=f"traffic_condition_dict_T_{sign}"))
            if(len(link_attributes["TRAFFIC_CONDITION_F"]) > 0):
                sign = link_attributes["TRAFFIC_CONDITION_F"][0]
                signs_list.append([link_id,loc_1,loc_2])
                gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc_1[0], loc_1[1], name=f"traffic_condition_dict_F_{sign}"))
            if(len(link_attributes["TRAFFIC_SIGNS_T"]) > 0):
                sign = link_attributes["TRAFFIC_SIGNS_T"][0]
                signs_list.append([link_id,loc_2,loc_1])
                gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc_1[0], loc_1[1], name=f"traffic_condition_dict_T_{sign}"))
            if(len(link_attributes["TRAFFIC_SIGNS_F"]) > 0):
                sign = link_attributes["TRAFFIC_SIGNS_F"][0]
                signs_list.append([link_id,loc_1,loc_2])
                gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc_1[0], loc_1[1], name=f"traffic_condition_dict_F_{sign}"))
            if(link_attributes["INTERSECTION"] != None):
                if(int(link_attributes["INTERSECTION"]) == 2):
                    gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc_1[0], loc_1[1], name=f"Manouvre"))
                if(int(link_attributes["INTERSECTION"]) == 4):
                    gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc_1[0], loc_1[1], name=f"Roundabout"))
    with open(f"./gpx/route_signs_list.gpx", "w") as f:
        f.write(gpx.to_xml())   
    f.close()
    return signs_list

#Route class
class Route:
    def __init__(self, desired_length, charging_stations: dict, visit_charging_station: bool):
        #self.route_type = route_type
        self.desired_length = desired_length
        self.charging_stations = charging_stations
        self.c_station = None
        self.visit_charging_stationt = visit_charging_station
        self.route = []
        self.route_length = 0
        self.driving_time = 0
        self.n_features = 0
        self.rank_points = 0
        self.output_path = os.path.join(os.getcwd(), 'gpx/')
        self.features_file_name = f"./gpx/summary.csv"
        return None

    def clean(self):
        del self.route
        del self.charging_stations

    def auxRoute(self, G, start_loc, end_loc):
        start_node_distances = []
        end_node_distances = []
        #signs = getSigns(G)
        for s in signs:
            d1 = Haversine(s[1],start_loc)
            d2 = Haversine(s[2],end_loc)
            d = d1 + d2
            s.append(d1)
            s.append(d2)
            s.append(d)
        df = pd.DataFrame(signs,columns = ['link_id','loc_1','loc_2','distance_sum','start_distance','end_distance'])
        df.sort_values(by=['distance_sum','end_distance','start_distance'],ascending = [True, False, True], inplace=True)
        print(df)
    
    def closestChargingStation(self, G, start_node, end_node):
        nearest_cs = None
        s_loc = G.nodes[start_node]['LOC']
        e_loc = G.nodes[end_node]['LOC']
        ref_dist = 100000
        for cs in self.charging_stations:
            loc = (int(self.charging_stations[cs]['LAT'])/100000, int(self.charging_stations[cs]['LON'])/100000)
            dist = distance(s_loc,loc) + distance(e_loc,loc)
            if(dist < ref_dist):
                ref_dist = dist
                nearest_cs = loc
                self.c_station = cs
        return nearest_cs   
    
    def setPathWeights(self, G, path):
        increment = 2.8
        for i in range(1,len(path)):
            link_data = G.get_edge_data(path[i-1],path[i])
            link_attributes = link_data[list(link_data.keys())[0]]
            link_attributes['WEIGHT'] = increment*link_attributes['WEIGHT']
            if(link_attributes['WEIGHT'] < 0):
                link_attributes['WEIGHT'] = 0
        for i in range(len(path)-1,0,-1):
            link_data = G.get_edge_data(path[i],path[i-1])
            if(link_data != None):
                link_attributes = link_data[list(link_data.keys())[0]]
                link_attributes['WEIGHT'] = increment*link_attributes['WEIGHT']
                if(link_attributes['WEIGHT'] < 0):
                    link_attributes['WEIGHT'] = 0
        return None

    def midPointPath(self, G, start_node: int, end_node: int, mid_point: int):
        path = nx.shortest_path(G, start_node, mid_point, weight='WEIGHT')
        self.setPathWeights(G, path)
        last_node = path.pop(len(path)-1)
        path_cont = nx.shortest_path(G, last_node, end_node, weight='WEIGHT')
        path.extend(path_cont)
        return path  
        
    def findRoute(self, G, start_node, end_node, mid_points):
        if(len(mid_points) > 0):
            full_path = []
            prev_node = start_node
            for next_node in mid_points:
                path_cont = nx.shortest_path(G, prev_node, next_node, weight='WEIGHT')
                last_node = path_cont.pop(len(path_cont)-1)
                full_path.extend(path_cont)
                prev_node = next_node
            path_cont = nx.shortest_path(G, prev_node, end_node, weight='WEIGHT')
            last_node = path_cont.pop(len(path_cont)-1)
            full_path.extend(path_cont)
            return full_path
        else:
            return self.pointToPointRoute(G, start_node, end_node)

    def getRouteLength(self):
        return self.route_length
        
    def pointToPointRoute(self, G, start_node, end_node):
        if(self.visit_charging_stationt):
            visit_point = self.closestChargingStation(G, start_node, end_node)
            if(visit_point != None):
                mid_node, _ = G.findNodeFromCoord(visit_point)
                return self.midPointPath(G, start_node, end_node, mid_node)
            else:
                return nx.shortest_path(G, start_node, end_node, weight='WEIGHT')
        else:
            return nx.shortest_path(G, start_node, end_node, weight='WEIGHT')

    def closedRoute(self, G, start_node, end_node):
        if(self.visit_charging_stationt):
            visit_point = self.closestChargingStation(G, start_node, end_node)
            if(visit_point != None):
                mid_node, _ = G.findNodeFromCoord(visit_point)
                route = self.midPointPath(G, start_node, mid_node, end_node)
                route.pop(len(route)-1)
                route.extend(nx.shortest_path(G, mid_node, start_node, weight='WEIGHT'))
                return route
            else:
                return self.midPointPath(G, start_node, start_node, end_node)
        else:
            return self.midPointPath(G, start_node, start_node, end_node)
            
    def pointToChargeStationRoute(self, G, start_node, end_node):
        route_found = False
        non_route_available = []
        while(not route_found):
            ref = self.desired_length
            for cs in self.charging_stations:
                loc = (int(self.charging_stations[cs]['LAT'])/100000, int(self.charging_stations[cs]['LON'])/100000)
                dist = Haversine(G.nodes[start_node]['LOC'],loc)
                diff = abs(self.desired_length - dist)
                if((diff < ref) and (loc not in non_route_available)):
                    ref = diff
                    charging_st = loc
                    self.c_station = cs
            mid_node, _ = G.findNodeFromCoord(charging_st)
            try:
                route = self.midPointPath(G, start_node, end_node, mid_node)
                route_found = True
            except:
                non_route_available.append(charging_st)
                print(non_route_available)
        return route
    
    def setRoute(self, G, start_point, end_point, mid_points):
        increment = 1.8
        self.avg_speed = 0
        self.route = self.findRoute(G, start_point, end_point, mid_points)
        for i in range(1,len(self.route)):
            link_data = G.get_edge_data(self.route[i-1],self.route[i])
            link_attributes = link_data[list(link_data.keys())[0]]
            self.route_length += link_attributes['LINK_LENGTH']
            self.avg_speed += link_attributes['AVG_SPEED']
            self.driving_time += (0.001*link_attributes['LINK_LENGTH'])/link_attributes['AVG_SPEED']
            link_attributes['WEIGHT'] = increment*link_attributes['WEIGHT']
        self.avg_speed /= len(self.route)
        self.route_length = self.route_length/1000
        return None
     
    def displayChargeStations(self, gpx, station):
        #for s in self.charging_stations:
        if(str(station) != "None"):
            gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(int(self.charging_stations[station]['LAT'])/100000,int(self.charging_stations[station]['LON'])/100000, name=self.charging_stations[station]['CONNECTORTYPE'])) 
        return None

    def routeRankPoints(self):
        self.rank_points = (self.desired_length - abs(self.desired_length - self.route_length)) + self.n_features
        print(f"Desired distance difference {self.desired_length - abs(self.desired_length - self.route_length)}")
        print(f"Number of desired features {self.n_features}")
        return None
    
    def getRankPoints(self):
        return self.n_features
    
    def displayRouteInfo(self):
        print(f"Route length in km = {self.route_length}")
        print(f"Average speed km/h = {self.avg_speed}")
        print(f"Driving time in hrs = {self.driving_time}")
        print(f"Number of desired features = {self.n_features}")
        print(f"Query points = {self.rank_points}")
        return None

    def setCSVFeatures(self, G, route_num, units="km"):
        file_name = f"./gpx/route{route_num}_staticfeaturesfile.csv"
        feat_line = ",".join([str(item) for item in feature_dict])
        #head = "Route_name,LAT,LON,Link_length,Avg_speed,Speed_limit,Time(hrs),Accum_len,Accum_time(hrs),"+feat_line+",Road_roughness,Lane_divider_marker,Toll_booth,Functional_class"+"\n"
        head = "Route_name,LAT,LON,Link_length,Avg_speed,Speed_limit,Time,Accum_len,Accum_time(hrs),"+feat_line+"\n"
        features_file = open(file_name, "w")
        features_file.write(head)
        features_file.close()
        features_file = open(file_name, "a")
        len_accum = 0
        time_accum = 0
        self.feat_count = []
        start = [False]
        for feat in feature_dict:
            self.feat_count.append(0)
        for i in range(1,len((self.route))):
            str_line = str(route_num)
            link_data = G.get_edge_data(self.route[i-1],self.route[i])
            link_attributes = link_data[list(link_data.keys())[0]]
            if(i < len(self.route)-1):
                next_link_data = G.get_edge_data(self.route[i],self.route[i+1])
                next_link_attributes = next_link_data[list(next_link_data.keys())[0]]
            else:
                next_link_attributes = link_data[list(link_data.keys())[0]]
            feat_list = self.fillFeaturesCSV(link_attributes, next_link_attributes, start)
            lat = str(int(link_attributes['LAT'].split(",")[0])/100000)
            lon = str(int(link_attributes['LON'].split(",")[0])/100000)
            if(units == "Mi"):
                link_length = 0.000621371*float(link_attributes['LINK_LENGTH'])
                if(str(link_attributes['SPEED_LIMIT']) == 'None'):
                    time = link_length/(0.621371*float(link_attributes['AVG_SPEED']))
                else:
                    time = link_length/(0.621371*float(link_attributes['SPEED_LIMIT']))
            else:
                link_length = 0.001*float(link_attributes['LINK_LENGTH'])
                if(str(link_attributes['SPEED_LIMIT']) == 'None'):
                    time = link_length/float(link_attributes['AVG_SPEED'])
                else:
                    time = link_length/float(link_attributes['SPEED_LIMIT'])

            len_accum = len_accum + link_length
            time_accum = time_accum + time
            feat_line = ",".join([str(item) for item in feat_list])
            str_line = str_line + "," + lat + "," + lon + "," + str(link_attributes['LINK_LENGTH']) + "," + str(link_attributes['AVG_SPEED'])+ "," + str(link_attributes['SPEED_LIMIT'])
            str_line = str_line + "," + str(time) + "," + str(len_accum) + "," + str(time_accum) + "," + feat_line + "\n"
            features_file.write(str_line)

        feat_count_line = ",".join([str(item) for item in self.feat_count])
        features_count_file = open(self.features_file_name, "a")
        summary = str(route_num)+","+str(len_accum)+","+str(time_accum) 
        features_count_file.write(summary+","+feat_count_line+"\n")
        features_count_file.close()
        features_file.close()

    def displayFeature(self, gpx, loc, link_attributes, next_link_attributes, values, start, feat_name):
        if(link_attributes != None):
            if((start==False) and (link_attributes in values) and (next_link_attributes in values)):
                gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0],loc[1], name=f"Start of {feat_name}"))
                start = True
                self.n_features += 1
            elif((start==True) and (link_attributes not in values) and (next_link_attributes not in values)):
                gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0],loc[1], name=f"End of {feat_name}"))
                start = False
        return start
    
    def displayIntersection(self, gpx, loc, link_attributes, next_link_attributes, values, start, feat_name):
        if(link_attributes != None):
            if((start==False) and (link_attributes in values) and (next_link_attributes in values)):
                gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0],loc[1], name=f"Start of {feat_name}"))
                start = True
                self.n_features += 1
            elif((start==True) and (link_attributes in values) and (next_link_attributes not in values)):
                gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0],loc[1], name=f"End of {feat_name}"))
                start = False
        return start

    def displayRoadGeom(self, gpx, link_attributes, loc):
        if(link_attributes["TUNNEL"] == 'Y'):
            gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0],loc[1], name=f"Tunnel"))
            self.n_features += 1
        if(link_attributes["BRIDGE"] == 'Y'):
            gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0],loc[1], name=f"Bridge"))
            self.n_features += 1
        return None
           
    def setGPXFile(self, G, route_num: int, path_directory: str, cfg: dict):
        gpx_file_name = f'./{path_directory}/route{route_num}_staticfeaturesfile.gpx'
        gpx = gpxpy.gpx.GPX()
        gpx_track = gpxpy.gpx.GPXTrack(name=gpx_file_name)
        gpx.tracks.append(gpx_track)
        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)
        start = [False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False]
        ref_speed_limit = None
        
        for i in range(1,len(self.route)):
            loc = G.nodes[self.route[i-1]]['LOC']
            link_data = G.get_edge_data(self.route[i-1],self.route[i])
            link_attributes = link_data[list(link_data.keys())[0]]
            if(i < len(self.route)-1):
                next_link_data = G.get_edge_data(self.route[i],self.route[i+1])
                next_link_attributes = next_link_data[list(next_link_data.keys())[0]]
            else:
                next_link_attributes = link_data[list(link_data.keys())[0]]
            edge_dir = link_attributes['EDGE_DIRECTION']
            if(cfg['query_features']['boolean_features']['highway']):
                start[0] = self.displayFeature(gpx, loc, link_attributes['FUNCTIONAL_CLASS'], next_link_attributes['FUNCTIONAL_CLASS'], [1,2,3], start[0], "highway")
            if(cfg['query_features']['boolean_features']['avoid_highway']):
                start[1] = self.displayFeature(gpx, loc, link_attributes['FUNCTIONAL_CLASS'], next_link_attributes['FUNCTIONAL_CLASS'], [4,5], start[1], "avoid_highway")
            if(cfg['query_features']['boolean_features']['urban']):
                start[2] = self.displayFeature(gpx, loc, link_attributes['URBAN'], next_link_attributes['URBAN'], ['Y'], start[2], "Urban")
            if(cfg['query_features']['boolean_features']['oneway']):
                start[3] = self.displayFeature(gpx, loc, link_attributes['TRAVEL_DIRECTION'], next_link_attributes['TRAVEL_DIRECTION'], ['F','T'], start[3], "One way")
            if(cfg['query_features']['boolean_features']['both_ways']):
                start[4] = self.displayFeature(gpx, loc, link_attributes['TRAVEL_DIRECTION'], next_link_attributes['TRAVEL_DIRECTION'], ['B'], start[4], "Bothways")
            if(cfg['query_features']['boolean_features']['limited_access']):
                start[5] = self.displayFeature(gpx, loc, link_attributes['LIMITED_ACCESS_ROAD'], next_link_attributes['LIMITED_ACCESS_ROAD'], ['Y'], start[5], "Limited access")
            if(cfg['query_features']['boolean_features']['paved']):
                start[6] = self.displayFeature(gpx, loc, link_attributes['PAVED'], next_link_attributes['PAVED'], ['Y'], start[6], "Paved")
            if(cfg['query_features']['boolean_features']['ramp']):
                start[7] = self.displayFeature(gpx, loc, link_attributes['RAMP'], next_link_attributes['RAMP'], ['Y'], start[7], "Ramp")
            if(cfg['query_features']['boolean_features']['manoeuvre']):
                start[8] = self.displayIntersection(gpx, loc, link_attributes['INTERSECTION'], next_link_attributes['INTERSECTION'], [2], start[8], "Manoeuvre")
            if(cfg['query_features']['boolean_features']['roundabout']):
                start[9] = self.displayIntersection(gpx, loc, link_attributes['INTERSECTION'], next_link_attributes['INTERSECTION'], [4], start[9], "Roundabout")
            if(cfg['query_features']['boolean_features']['one_lane']):
                start[10] = self.displayFeature(gpx, loc, link_attributes['LANE_CATEGORY'], next_link_attributes['LANE_CATEGORY'], [1], start[10], "One lane")
            if(cfg['query_features']['boolean_features']['multiple_lanes']):
                start[11] = self.displayFeature(gpx, loc, link_attributes['LANE_CATEGORY'], next_link_attributes['LANE_CATEGORY'], [2,3,4], start[11], "Multi lane")
            if(cfg['query_features']['boolean_features']['overpass']):
                start[12] = self.displayFeature(gpx, loc, link_attributes['OVERPASS_UNDERPASS'], next_link_attributes['OVERPASS_UNDERPASS'], ['1'], start[12], "Overpass")
            if(cfg['query_features']['boolean_features']['underpass']):
                start[13] = self.displayFeature(gpx, loc, link_attributes['OVERPASS_UNDERPASS'], next_link_attributes['OVERPASS_UNDERPASS'], ['2'], start[13], "Underpass")
            
            if((cfg['query_features']['boolean_features']['variable_speed']) and (11 in link_attributes[f"TRAFFIC_CONDITION_{link_attributes['EDGE_DIRECTION']}"])):
                gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0], loc[1], name=f"{traffic_condition_dict[11]}")) 
                self.n_features += 1
            if((cfg['query_features']['boolean_features']['traffic_light']) and (16 in link_attributes[f"TRAFFIC_CONDITION_{link_attributes['EDGE_DIRECTION']}"])):
                gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0], loc[1], name=f"{traffic_condition_dict[16]}")) 
                self.n_features += 1
            if((cfg['query_features']['boolean_features']['railway_crossing']) and (18 in link_attributes[f"TRAFFIC_CONDITION_{link_attributes['EDGE_DIRECTION']}"])):
                gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0], loc[1], name=f"{traffic_condition_dict[18]}")) 
                self.n_features += 1
            if((cfg['query_features']['boolean_features']['no_overtaking']) and (19 in link_attributes[f"TRAFFIC_CONDITION_{link_attributes['EDGE_DIRECTION']}"])):
                gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0], loc[1], name=f"{traffic_condition_dict[19]}")) 
                self.n_features += 1
            if((cfg['query_features']['boolean_features']['overtaking']) and (21 in link_attributes[f"TRAFFIC_CONDITION_{link_attributes['EDGE_DIRECTION']}"])):
                gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0], loc[1], name=f"{traffic_condition_dict[21]}")) 
                self.n_features += 1

            if(cfg['query_features']['boolean_features']['stop_sign']):
                self.addSignWayPoint(gpx,loc,link_attributes,20,edge_dir)
            if(cfg['query_features']['boolean_features']['school_sign']):
                self.addSignWayPoint(gpx,loc,link_attributes,31,edge_dir)
            if(cfg['query_features']['boolean_features']['icy_sign']):
                self.addSignWayPoint(gpx,loc,link_attributes,28,edge_dir)
            if(cfg['query_features']['boolean_features']['crosswalk_sign']):
                self.addSignWayPoint(gpx,loc,link_attributes,41,edge_dir)
            if(cfg['query_features']['boolean_features']['falling_rocks_sign']):
                self.addSignWayPoint(gpx,loc,link_attributes,30,edge_dir)
            if(cfg['query_features']['boolean_features']['animal_crossing_sign']):
                self.addSignWayPoint(gpx,loc,link_attributes,27,edge_dir)
            if(cfg['query_features']['boolean_features']['tway_sign']):
                self.addSignWayPoint(gpx,loc,link_attributes,46,edge_dir)
            if(cfg['query_features']['boolean_features']['merge_r_sign']):
                self.addSignWayPoint(gpx,loc,link_attributes,6,edge_dir)
            if(cfg['query_features']['boolean_features']['merge_l_sign']):
                self.addSignWayPoint(gpx,loc,link_attributes,7,edge_dir)
            if(cfg['query_features']['boolean_features']['merge_c_sign']):
                self.addSignWayPoint(gpx,loc,link_attributes,8,edge_dir)
            if(cfg['query_features']['boolean_features']['hills_sign']):
                self.addSignWayPoint(gpx,loc,link_attributes,18,edge_dir)
            if(cfg['query_features']['boolean_features']['hills_sign']):
                self.addSignWayPoint(gpx,loc,link_attributes,19,edge_dir)
            if(cfg['query_features']['boolean_features']['hills_sign']):
                self.addSignWayPoint(gpx,loc,link_attributes,26,edge_dir)

            if(cfg['query_features']['boolean_features']['tunnel']):
                start[14] = self.displayFeature(gpx, loc, link_attributes['TUNNEL'], next_link_attributes['TUNNEL'], ['Y'], start[14], "Tunnel")
            if(cfg['query_features']['boolean_features']['bridge']):
                start[15] = self.displayFeature(gpx, loc, link_attributes['BRIDGE'], next_link_attributes['BRIDGE'], ['Y'], start[15], "Bridge")

            if((cfg['query_features']['boolean_features']['speed_bumps']) and (3 == int(link_attributes[f"SPEED_BUMPS"]))):
                gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0], loc[1], name=f"Speed_bump")) 
                self.n_features += 1
            
            if((cfg['query_features']['boolean_features']['toll_booth']) and (link_attributes[f"TOLL_BOOTH"] != None)):
                gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0], loc[1], name=f"Toll_booth")) 
                self.n_features += 1

            gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(loc[0],loc[1],elevation=0,time=datetime.datetime(2022, 1, 1)))
        if((int(cfg['visit_charge_station']) == 1) or (cfg['route_type'] == "point_to_charge_station")):
            if(self.c_station != None):
                lat = int(self.charging_stations[self.c_station]['LAT'])/100000
                lon = int(self.charging_stations[self.c_station]['LON'])/100000
                CONNECTOR = self.charging_stations[self.c_station]["CONNECTORTYPE"]
                gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(lat,lon, name=CONNECTOR))
        #    station = self.closestChargingStation(G, cfg['start_location'],cfg['end_location'])
        with open(gpx_file_name, "w") as f:
            f.write(gpx.to_xml())   
        f.close()
        #self.routeRankPoints()
        #self.displayRouteInfo()
        del gpx
        return None
    
    def addSignWayPoint(self,gpx,loc,attr,signNumber,edgeDirection):
        if(signNumber in attr[f'TRAFFIC_SIGNS_{edgeDirection}']):
            gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0], loc[1], name=f"{traffics_sign_dict[signNumber]}")) 
            self.n_features += 1

    def fillFeaturesCSV(self, attributes, next_attributes, start):
        feat_list = ['Not present' for i in range(len(feature_dict))]
        edge_dir = attributes['EDGE_DIRECTION']
        #highway
        if(int(attributes[f'FUNCTIONAL_CLASS']) <= 3):
            self.feat_count[feature_dict['highway']] += attributes['LINK_LENGTH']*0.001
            feat_list[feature_dict['highway']] = 'Present'
        #avoid highway
        if(int(attributes[f'FUNCTIONAL_CLASS']) >= 4):
            self.feat_count[feature_dict['avoid_highway']] += attributes['LINK_LENGTH']*0.001
            feat_list[feature_dict['avoid_highway']] = 'Present'
        if(attributes['URBAN'] == 'Y'):
            self.feat_count[feature_dict['urban']] += attributes['LINK_LENGTH']*0.001
            feat_list[feature_dict['urban']] = 'Present'
        #One way
        if(attributes[f'TRAVEL_DIRECTION'] != "B"):
            self.feat_count[feature_dict['oneway']] += attributes['LINK_LENGTH']*0.001
            feat_list[feature_dict['oneway']] = 'Present'
        #Both ways
        if(attributes[f'TRAVEL_DIRECTION'] == "B"):
            self.feat_count[feature_dict['both_ways']] += attributes['LINK_LENGTH']*0.001
            feat_list[feature_dict['both_ways']] = 'Present'
        #Limited acces
        if(attributes['LIMITED_ACCESS_ROAD'] == 'Y'):
            self.feat_count[feature_dict['limited_access']] += attributes['LINK_LENGTH']*0.001
            feat_list[feature_dict['limited_access']] = 'Present'
        #Paved
        if(attributes['PAVED'] == 'Y'):
            self.feat_count[feature_dict['paved']] += attributes['LINK_LENGTH']*0.001
            feat_list[feature_dict['paved']] = 'Present'
        #Ramp
        if(str(attributes['RAMP']) == 'Y'):
            if(str(next_attributes['RAMP']) == 'Y'):
                feat_list[feature_dict['ramp']] = 'Present'
                if(start[0] == False):
                    self.feat_count[feature_dict['ramp']] += 1
                    start[0] = True
            elif(str(next_attributes['RAMP']) == 'N'):
                start[0] = False
        #Manoeuvre
        if(str(attributes['INTERSECTION']) == '2'):
            self.feat_count[feature_dict['manoeuvre']] += 1
            feat_list[feature_dict['manoeuvre']] = 'Present'
        #Roundabout
        if(str(attributes['INTERSECTION']) == '4'):
            self.feat_count[feature_dict['roundabout']] += 1
            feat_list[feature_dict['roundabout']] = 'Present'
        #One lane
        if(str(attributes['LANE_CATEGORY']) == '1'):
            self.feat_count[feature_dict['one_lane']] += attributes['LINK_LENGTH']*0.001
            feat_list[feature_dict['one_lane']] = 'Present'
        #Multiple lanes
        if((str(attributes['LANE_CATEGORY']) == '2') or (str(attributes['LANE_CATEGORY']) == '3')):
            self.feat_count[feature_dict['multiple_lanes']] += attributes['LINK_LENGTH']*0.001
            feat_list[feature_dict['multiple_lanes']] = 'Present'
        #Overpass
        if(str(attributes['OVERPASS_UNDERPASS']) == '1'):
            self.feat_count[feature_dict['overpass']] += 1
            feat_list[feature_dict['overpass']] = 'Present'
        #Underpass
        if(str(attributes['OVERPASS_UNDERPASS']) == '2'):
            self.feat_count[feature_dict['underpass']] += 1
            feat_list[feature_dict['underpass']] = 'Present'
        
        #Traffic conditions
        if(11 in attributes[f'TRAFFIC_CONDITION_{edge_dir}']):
            self.feat_count[feature_dict['variable_speed']] += 1
            feat_list[feature_dict['variable_speed']] = 'Present'
        if(16 in attributes[f'TRAFFIC_CONDITION_{edge_dir}']):
            self.feat_count[feature_dict['traffic_lights']] += 1
            feat_list[feature_dict['traffic_lights']] = 'Present'
        if(18 in attributes[f'TRAFFIC_CONDITION_{edge_dir}']):
            self.feat_count[feature_dict['railway_crossing']] += 1
            feat_list[feature_dict['railway_crossing']] = 'Present'
        if(19 in attributes[f'TRAFFIC_CONDITION_{edge_dir}']):
            self.feat_count[feature_dict['no_overtaking']] += 1
            feat_list[feature_dict['no_overtaking']] = 'Present'
        if(21 in attributes[f'TRAFFIC_CONDITION_{edge_dir}']):
            self.feat_count[feature_dict['overtaking']] += 1
            feat_list[feature_dict['overtaking']] = 'Present'
        if(17 in attributes[f'TRAFFIC_CONDITION_{edge_dir}']):
            self.feat_count[feature_dict['traffic_signs']] += 1
            feat_list[feature_dict['traffic_signs']] = 'Present'

        #Traffic signs
        if(20 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[feature_dict['stop_signs']] += 1
            feat_list[feature_dict['stop_signs']] = 'Present'
        if(31 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[feature_dict['school_zone']] += 1
            feat_list[feature_dict['school_zone']] = 'Present'
        if(28 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[feature_dict['icy_road']] += 1
            feat_list[feature_dict['icy_road']] = 'Present'
        if(41 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[feature_dict['crosswalk']] += 1
            feat_list[feature_dict['crosswalk']] = 'Present'
        if(27 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[feature_dict['animal_crossing']] += 1
            feat_list[feature_dict['animal_crossing']] = 'Present'
        if(46 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[feature_dict['two_way']] += 1
            feat_list[feature_dict['two_way']] = 'Present'
        if(6 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[feature_dict['lane_merge_right']] += 1
            feat_list[feature_dict['lane_merge_right']] = 'Present'
        if(7 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[feature_dict['lane_merge_left']] += 1
            feat_list[feature_dict['lane_merge_left']] = 'Present'
        if(8 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[feature_dict['lane_merge_center']] += 1
            feat_list[feature_dict['lane_merge_center']] = 'Present'
        if(30 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[feature_dict['falling_rocks']] += 1
            feat_list[feature_dict['falling_rocks']] = 'Present'
        if((18 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']) or (19 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']) or (26 in attributes[f'TRAFFIC_SIGNS_{edge_dir}'])):
            self.feat_count[feature_dict['hills']] += 1
            feat_list[feature_dict['hills']] = 'Present'

        if(attributes['TUNNEL'] == 'Y'):
            self.feat_count[feature_dict['tunnel']] += 1
            feat_list[feature_dict['tunnel']] = 'Present'
        if(attributes['BRIDGE'] == 'Y'):
            self.feat_count[feature_dict['bridge']] += 1
            feat_list[feature_dict['bridge']] = 'Present'
        
        if(attributes[f'ROAD_ROUGHNESS_{edge_dir}'] == 'Good'):
            self.feat_count[feature_dict['road_roughness_good']] += attributes['LINK_LENGTH']*0.001
            feat_list[feature_dict['road_roughness_good']] = 'Present'
        if(attributes[f'ROAD_ROUGHNESS_{edge_dir}'] == "Fair"):
            self.feat_count[feature_dict['road_roughness_fair']] += attributes['LINK_LENGTH']*0.001
            feat_list[feature_dict['road_roughness_fair']] = 'Present'
        if(attributes[f'ROAD_ROUGHNESS_{edge_dir}'] == "Poor"):
            self.feat_count[feature_dict['road_roughness_poor']] += attributes['LINK_LENGTH']*0.001
            feat_list[feature_dict['road_roughness_poor']] = 'Present'

        if(attributes[f'SPEED_BUMPS'] == 3):
            self.feat_count[feature_dict['speed_bump']] += 1
            feat_list[feature_dict['speed_bump']] = 'Present'
        
        if(attributes[f'TOLL_BOOTH'] != None):
            self.feat_count[feature_dict['toll_station']] += 1
            feat_list[feature_dict['toll_station']] = 'Present'

        return feat_list