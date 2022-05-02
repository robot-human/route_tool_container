#from re import S
from HEREgraph2 import HEREgraph
import numpy as np
import networkx as nx
import gpxpy
import os
from Tools import Haversine, getRandomLocation, distance
import pandas as pd
"summary"
#This function returns the full graph traffic signs list
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
    def __init__(self, route_type, desired_length, search_radius, charging_stations: dict, visit_charging_station: bool):
        self.route_type = route_type
        self.desired_length = desired_length
        self.search_radius = search_radius
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
    
    def midPointPath(self, G, start_node: int, end_node: int, mid_point: int):
        increment = 100
        path = nx.shortest_path(G, start_node, mid_point, weight='WEIGHT')
        for i in range(1,len(path)):
            link_data = G.get_edge_data(path[i-1],path[i])
            link_attributes = link_data[list(link_data.keys())[0]]
            link_attributes['WEIGHT'] = increment*link_attributes['WEIGHT']
        for i in range(len(path)-1,0,-1):
            link_data = G.get_edge_data(path[i],path[i-1])
            if(link_data != None):
                link_attributes = link_data[list(link_data.keys())[0]]
                link_attributes['WEIGHT'] = increment*link_attributes['WEIGHT']
        last_node = path.pop(len(path)-1)
        path_cont = nx.shortest_path(G, last_node, end_node, weight='WEIGHT')
        path.extend(path_cont)
        return path  
        
    def findRoute(self, G, start_node, end_node):
        if(self.route_type == 'point_to_point'):
            return self.pointToPointRoute(G, start_node, end_node)
        elif(self.route_type == 'closed_route'):
            return self.closedRoute(G, start_node, end_node)
        elif(self.route_type == 'point_to_anywhere'):
            try:
                return self.pointToPointRoute(G, start_node, end_node)
                route_bool = True
            except:
                print("couldn't find route")
        elif(self.route_type == 'point_to_charge_station'):
            print("Charge station")
            return self.pointToChargeStationRoute(G, start_node, end_node)
        else:
            print("Invalid route type")
            return None

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
    
    def setRoute(self, G, start_point, mid_point):
        increment = 5.0
        self.avg_speed = 0
        self.route = self.findRoute(G, start_point, mid_point)
        for i in range(1,len(self.route)):
            link_data = G.get_edge_data(self.route[i-1],self.route[i])
            #print(link_data)
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
        print(f"Average speed km/g = {self.avg_speed}")
        print(f"Driving time in hrs = {self.driving_time}")
        print(f"Number of desired features = {self.n_features}")
        print(f"Query points = {self.rank_points}")
        return None

    def setCSVFeatures(self, G, route_num: int):
        file_name = f"./gpx/route{route_num}_staticfeaturesfile.csv"
        feat_line = ",".join([str(item) for item in feature_list])
        head = "Route_name,LAT,LON,Link_length (m),Avg_speed (km/h),Speed_limit (km/h),Time (h),Accum_len (km),Accum_time (h),"+feat_line+",Road_roughness,Lane_divider_marker,Toll_booth,Functional_class"+"\n"
        features_file = open(file_name, "w")
        features_file.write(head)
        features_file.close()
        features_file = open(file_name, "a")
        len_accum = 0
        time_accum = 0
        self.feat_count = []
        start = [False]
        for feat in feature_list:
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
            link_length = 0.001*float(link_attributes['LINK_LENGTH'])
            if(str(link_attributes['SPEED_LIMIT']) == 'None'):
                time = link_length/float(link_attributes['AVG_SPEED'])
            else:
                time = link_length/float(link_attributes['SPEED_LIMIT'])
            len_accum = len_accum + link_length
            time_accum = time_accum + time
            feat_line = ",".join([str(item) for item in feat_list])
            str_line = str_line + "," + lat + "," + lon + "," + str(link_attributes['LINK_LENGTH']) + "," + str(link_attributes['AVG_SPEED'])+ "," + str(link_attributes['SPEED_LIMIT'])
            str_line = str_line + "," + str(time) + "," + str(len_accum) + "," + str(time_accum) + "," + feat_line + "," + lane_divider_dict[int(link_attributes['LANE_DIVIDER_MARKER'])] + "," + str(link_attributes['TOLL_BOOTH'])+ "," +str(link_attributes['FUNCTIONAL_CLASS'])+ "\n"
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
        start = [False,False,False,False,False,False,False,False,False,False,False,False]
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
            if(cfg['query_features']['boolean_features']['ramp']):
                start[2] = self.displayFeature(gpx, loc, link_attributes['RAMP'], next_link_attributes['RAMP'], ['Y'], start[2], "Ramp")
            if(cfg['query_features']['boolean_features']['paved']):
                start[3] = self.displayFeature(gpx, loc, link_attributes['PAVED'], next_link_attributes['PAVED'], ['Y'], start[3], "Paved")
            if(cfg['query_features']['boolean_features']['access']):
                start[4] = self.displayFeature(gpx, loc, link_attributes['LIMITED_ACCESS_ROAD'], next_link_attributes['LIMITED_ACCESS_ROAD'], ['Y'], start[4], "Limited access")
            if(cfg['query_features']['boolean_features']['both_ways']):
                start[5] = self.displayFeature(gpx, loc, link_attributes['TRAVEL_DIRECTION'], next_link_attributes['TRAVEL_DIRECTION'], ['B'], start[5], "Bothways")
            if(cfg['query_features']['boolean_features']['oneway']):
                start[6] = self.displayFeature(gpx, loc, link_attributes['TRAVEL_DIRECTION'], next_link_attributes['TRAVEL_DIRECTION'], ['F','T'], start[6], "One way")
            if(cfg['query_features']['boolean_features']['urban']):
                start[7] = self.displayFeature(gpx, loc, link_attributes['URBAN'], next_link_attributes['URBAN'], ['Y'], start[7], "Urban")
            if(cfg['query_features']['boolean_features']['overpass']):
                start[8] = self.displayFeature(gpx, loc, link_attributes['OVERPASS_UNDERPASS'], next_link_attributes['OVERPASS_UNDERPASS'], ['1'], start[8], "Overpass")
            if(cfg['query_features']['boolean_features']['underpass']):
                start[9] = self.displayFeature(gpx, loc, link_attributes['OVERPASS_UNDERPASS'], next_link_attributes['OVERPASS_UNDERPASS'], ['2'], start[9], "Underpass")
            if(cfg['query_features']['boolean_features']['one_lane']):
                start[10] = self.displayFeature(gpx, loc, link_attributes['LANE_CATEGORY'], next_link_attributes['LANE_CATEGORY'], [1], start[10], "One lane")
            if(cfg['query_features']['boolean_features']['multiple_lanes']):
                start[11] = self.displayFeature(gpx, loc, link_attributes['LANE_CATEGORY'], next_link_attributes['LANE_CATEGORY'], [2,3,4], start[11], "Multi lane")

            if(cfg['query_features']['boolean_features']['manoeuvre']):
                if(link_attributes['INTERSECTION'] != None):
                    if((int(link_attributes['INTERSECTION']) == 2) and (prev_link_manoeuvre == False)):
                        gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0],loc[1], name=f"Manoeuvre"))
                        self.n_features += 1  
                        prev_link_manoeuvre = True
                else:
                    prev_link_manoeuvre = False
            if(cfg['query_features']['boolean_features']['roundabout']):
                if(link_attributes['INTERSECTION'] != None):
                    if((int(link_attributes['INTERSECTION']) == 4) and (prev_link_roundabout == False)):
                        gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0],loc[1], name=f"Roundabout"))
                        self.n_features += 1
                        prev_link_roundabout = True
                else:
                    prev_link_roundabout = False
            
            if(cfg['query_features']['boolean_features']['tunnel']):
                if((link_attributes["TUNNEL"] == 'Y') and (prev_link_tunnel == False)):
                    gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0],loc[1], name=f"Tunnel"))
                    self.n_features += 1
                    prev_link_tunnel = True
                else:
                    prev_link_tunnel = False

            if(cfg['query_features']['boolean_features']['bridge']):
                if((link_attributes["BRIDGE"] == 'Y') and (prev_link_bridge == False)):
                    gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0],loc[1], name=f"Bridge"))
                    self.n_features += 1
                    prev_link_bridge = True
                else:
                    prev_link_bridge = False

            if(cfg['query_features']['boolean_features']['traffic_signs'] == 0):
                self.addSignWayPoint(gpx,loc,link_attributes,'stop_signs',20,edge_dir,cfg)
                self.addSignWayPoint(gpx,loc,link_attributes,'school_zone',31,edge_dir,cfg)
                self.addSignWayPoint(gpx,loc,link_attributes,'icy_road',28,edge_dir,cfg)
                self.addSignWayPoint(gpx,loc,link_attributes,'falling_rocks',30,edge_dir,cfg)
                self.addSignWayPoint(gpx,loc,link_attributes,'pedestrian',41,edge_dir,cfg)
                self.addSignWayPoint(gpx,loc,link_attributes,'crosswalk',41,edge_dir,cfg)
                self.addSignWayPoint(gpx,loc,link_attributes,'non_pedestrian',27,edge_dir,cfg)
                self.addSignWayPoint(gpx,loc,link_attributes,'non_pedestrian',59,edge_dir,cfg)
                self.addSignWayPoint(gpx,loc,link_attributes,'two_way',46,edge_dir,cfg)
                self.addSignWayPoint(gpx,loc,link_attributes,'urban',47,edge_dir,cfg)
                self.addSignWayPoint(gpx,loc,link_attributes,'lane_merge_r',6,edge_dir,cfg)
                self.addSignWayPoint(gpx,loc,link_attributes,'lane_merge_l',7,edge_dir,cfg)
                self.addSignWayPoint(gpx,loc,link_attributes,'lane_merge_c',8,edge_dir,cfg)
                self.addSignWayPoint(gpx,loc,link_attributes,'hills',18,edge_dir,cfg)
                self.addSignWayPoint(gpx,loc,link_attributes,'hills',19,edge_dir,cfg)
                self.addSignWayPoint(gpx,loc,link_attributes,'hills',26,edge_dir,cfg)
            if(cfg['query_features']['boolean_features']['traffic_signs']) and (len(link_attributes[f"TRAFFIC_SIGNS_{link_attributes['EDGE_DIRECTION']}"]) > 0):
                for sign in link_attributes[f"TRAFFIC_SIGNS_{edge_dir}"]:
                    tsign = int(sign)
                    gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0], loc[1], name=f"{traffics_sign_dict[tsign]}"))  
                    self.n_features += 1

            if((cfg['query_features']['boolean_features']['variable_speed']) and (11 in link_attributes[f"TRAFFIC_CONDITION_{link_attributes['EDGE_DIRECTION']}"])):
                gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0], loc[1], name=f"{traffic_condition_dict[11]}")) 
                self.n_features += 1
            if((cfg['query_features']['boolean_features']['traffic_lights']) and (16 in link_attributes[f"TRAFFIC_CONDITION_{link_attributes['EDGE_DIRECTION']}"])):
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

            gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(loc[0],loc[1])) 
        if((int(cfg['visit_charge_station']) == 1) or (cfg['route_type'] == "point_to_charge_station")):
            if(self.c_station != None):
                lat = int(self.charging_stations[self.c_station]['LAT'])/100000
                lon = int(self.charging_stations[self.c_station]['LON'])/100000
                CONNECTOR = self.charging_stations[self.c_station]["CONNECTORTYPE"]
                gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(lat,lon, name=CONNECTOR))
        #    station = self.closestChargingStation(G, cfg['start_location'],cfg['end_location'])
        #self.displayChargeStations(gpx, station)
        with open(gpx_file_name, "w") as f:
            f.write(gpx.to_xml())   
        f.close()
        self.routeRankPoints()
        self.displayRouteInfo()
        return None
    
    def addSignWayPoint(self,gpx,loc,attr,signName,signNumber,edgeDirection,cfg):
        if((cfg['query_features']['boolean_features'][signName]) and (signNumber in attr[f'TRAFFIC_SIGNS_{edgeDirection}'])):
            gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0], loc[1], name=f"{traffics_sign_dict[signNumber]}")) 
            self.n_features += 1

    def fillFeaturesCSV(self,attributes, next_attributes, start):
        feat_list = ['Not present' for i in range(len(feature_list)+1)]
        edge_dir = attributes['EDGE_DIRECTION']
        if(20 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[0] += 1
            feat_list[0] = 'Present'
        if(31 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[1] += 1
            feat_list[1] = 'Present'
        if(28 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[2] += 1
            feat_list[2] = 'Present'
        if(41 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[3] += 1
            feat_list[3] = 'Present'
        if(41 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[4] += 1
            feat_list[4] = 'Present'
        if((27 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']) or (59 in attributes[f'TRAFFIC_SIGNS_{edge_dir}'])):
            self.feat_count[5] += 1
            feat_list[5] = 'Present'
        if(16 in attributes[f'TRAFFIC_CONDITION_{edge_dir}']):
            self.feat_count[6] += 1
            feat_list[6] = 'Present'
        if(17 in attributes[f'TRAFFIC_CONDITION_{edge_dir}']):
            self.feat_count[7] += 1
            feat_list[7] = 'Present'
        if(6 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[8] += 1
            feat_list[8] = 'Present'
        if(7 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[9] += 1
            feat_list[9] = 'Present'
        if(8 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[10] += 1
            feat_list[10] = 'Present'
        if(int(attributes[f'FUNCTIONAL_CLASS']) <= 3):
            self.feat_count[11] += attributes['LINK_LENGTH']*0.001
            feat_list[11] = 'Present'
        if(int(attributes[f'FUNCTIONAL_CLASS']) >= 4):
            self.feat_count[12] += attributes['LINK_LENGTH']*0.001
            feat_list[12] = 'Present'
        if(attributes[f'TRAVEL_DIRECTION'] != "B"):
            self.feat_count[13] += attributes['LINK_LENGTH']*0.001
            feat_list[13] = 'Present'
        if(attributes[f'TRAVEL_DIRECTION'] == "B"):
            self.feat_count[14] += attributes['LINK_LENGTH']*0.001
            feat_list[14] = 'Present'
        if(47 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[15] += 1
            feat_list[15] = 'Present'
        if(str(attributes['LIMITED_ACCESS_ROAD']) != 'None'):
            self.feat_count[16] += attributes['LINK_LENGTH']*0.001
            feat_list[16] = 'Present'
        if(str(attributes['PAVED']) != 'None'):
            self.feat_count[17] += attributes['LINK_LENGTH']*0.001
            feat_list[17] = 'Present'
        if(str(attributes['RAMP']) == 'Y'):
            if((str(next_attributes['RAMP']) == 'Y') and (start[0] == False)):
                self.feat_count[18] += 1
                feat_list[18] = 'Present'
                start[0] = True
            elif(str(next_attributes['RAMP']) == 'N'):
                start[0] = False
        if(str(attributes['INTERSECTION']) == '2'):
            self.feat_count[19] += 1
            feat_list[19] = 'Present'
        if(str(attributes['INTERSECTION']) == '4'):
            self.feat_count[20] += 1
            feat_list[20] = 'Present'
        if(str(attributes['LANE_CATEGORY']) == '1'):
            self.feat_count[21] += attributes['LINK_LENGTH']*0.001
            feat_list[21] = 'Present'
        if((str(attributes['LANE_CATEGORY']) == '2') or (str(attributes['LANE_CATEGORY']) == '3')):
            self.feat_count[22] += attributes['LINK_LENGTH']*0.001
            feat_list[22] = 'Present'
        if(str(attributes['OVERPASS_UNDERPASS']) == '1'):
            self.feat_count[23] += 1
            feat_list[23] = 'Present'
        if(str(attributes['OVERPASS_UNDERPASS']) == '2'):
            self.feat_count[24] += 1
            feat_list[24] = 'Present'
        if(11 in attributes[f'TRAFFIC_CONDITION_{edge_dir}']):
            self.feat_count[25] += 1
            feat_list[25] = 'Present'
        if(18 in attributes[f'TRAFFIC_CONDITION_{edge_dir}']):
            self.feat_count[26] += 1
            feat_list[26] = 'Present'
        if(19 in attributes[f'TRAFFIC_CONDITION_{edge_dir}']):
            self.feat_count[27] += 1
            feat_list[27] = 'Present'
        if(21 in attributes[f'TRAFFIC_CONDITION_{edge_dir}']):
            self.feat_count[28] += 1
            feat_list[28] = 'Present'
        if(30 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[29] += 1
            feat_list[29] = 'Present'
        if((18 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']) or (19 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']) or (26 in attributes[f'TRAFFIC_SIGNS_{edge_dir}'])):
            self.feat_count[30] += 1
            feat_list[30] = 'Present'
        if(attributes['TUNNEL'] == 'Y'):
            self.feat_count[31] += 1
            feat_list[31] = 'Present'
        if(attributes['BRIDGE'] == 'Y'):
            self.feat_count[32] += 1
            feat_list[32] = 'Present'
        if(1 in attributes[f'BUMP_{edge_dir}']):
            self.feat_count[33] += 1
            feat_list[33] = 'Present'
        if(2 in attributes[f'BUMP_{edge_dir}']):
            self.feat_count[34] += 1
            feat_list[34] = 'Present'
        if(attributes[f'SPEED_BUMPS'] == 3):
            self.feat_count[35] += 1
            feat_list[35] = 'Present'
        feat_list[36] = attributes[f'ROAD_ROUGHNESS_{edge_dir}']
        if(attributes[f'FUNCTIONAL_CLASS'] == 1):
            self.feat_count[36] += attributes['LINK_LENGTH']*0.001
            self.feat_count[41] += 0.001*attributes['LINK_LENGTH']/float(attributes['AVG_SPEED'])
        if(attributes[f'FUNCTIONAL_CLASS'] == 2):
            self.feat_count[37] += attributes['LINK_LENGTH']*0.001
            self.feat_count[42] += 0.001*attributes['LINK_LENGTH']/float(attributes['AVG_SPEED'])
        if(attributes[f'FUNCTIONAL_CLASS'] == 3):
            self.feat_count[38] += attributes['LINK_LENGTH']*0.001
            self.feat_count[43] += 0.001*attributes['LINK_LENGTH']/float(attributes['AVG_SPEED'])
        if(attributes[f'FUNCTIONAL_CLASS'] == 4):
            self.feat_count[39] += attributes['LINK_LENGTH']*0.001
            self.feat_count[44] += 0.001*attributes['LINK_LENGTH']/float(attributes['AVG_SPEED'])
        if(attributes[f'FUNCTIONAL_CLASS'] == 5):
            self.feat_count[40] += attributes['LINK_LENGTH']*0.001
            self.feat_count[45] += 0.001*attributes['LINK_LENGTH']/float(attributes['AVG_SPEED'])
        return feat_list

traffics_sign_dict = {1 : "START OF NO OVERTAKING", 10 : "RAILWAY CROSSING UNPROTECTED", 11 : "ROAD NARROWS", 
                      12 : "SHARP CURVE LEFT 10 sharp curve", 13 : "SHARP CURVE RIGHT 10 sharp curve", 
                      14 : "WINDING ROAD STARTING LEFT", 15 : "WINDING ROAD STARTING RIGHT", 
                      16 : "START OF NO OVERTAKING TRUCKS", 17 : "END OF NO OVERTAKING TRUCKS", 
                      18 : "STEEP HILL UPWARDS", 19 : "STEEP HILL DOWNWARDS", 2 : "END OF NO OVERTAKING", 
                      20 : "STOP SIGN", 21 : "LATERAL WIND", 22 : "GENERAL WARNING 70-80", 23 : "RISK OF GROUNDING", 
                      24 : "GENERAL CURVE", 25 : "END OF ALL RESTRICTIONS", 26 : "GENERAL HILL", 
                      27 : "ANIMAL CROSSING 30 Deer Crossing", 28 : "ICY CONDITIONS", 
                      29 : "SLIPPERY ROAD 40 Sleppery", 3 : "PROTECTED OVERTAKING - EXTRA LANE", 
                      30 : "FALLING ROCKS", 31 : "SCHOOL ZONE school zone", 32 : "TRAMWAY CROSSING", 
                      33 : "CONGESTION HAZARD", 34 : "ACCIDENT HAZARD", 35 : "PRIORITY OVER ONCOMING TRAFFIC", 
                      36 : "YIELD TO ONCOMING TRAFFIC", 37 : "CROSSING WITH PRIORITY FROM THE RIGHT", 
                      4 : "PROTECTED OVERTAKING - EXTRA LANE RIGHT", 41 : "PEDESTRIAN CROSSING", 42 : "YIELD", 
                      43 : "DOUBLE HAIRPIN", 44 : "TRIPLE HAIRPIN", 45 : "EMBANKMENT", 46 : "TWO-WAY TRAFFIC", 
                      47 : "URBAN AREA", 48 : "HUMP BRIDGE", 49 : "UNEVEN ROAD", 
                      5 : "PROTECTED OVERTAKING - EXTRA LANE LEFT", 50 : "FLOOD AREA", 51 : "OBSTACLE", 
                      52 : "HORN SIGN", 53 : "NO ENGINE BRAKE", 54 : "END OF NO ENGINE BRAKE", 55 : "NO IDLING", 
                      56 : "TRUCK ROLLOVER", 57 : "LOW GEAR", 58 : "END OF LOW GEAR", 59 : "BICYCLE CROSSING", 
                      6 : "LANE MERGING FROM THE RIGHT", 60 : "YIELD TO BICYCLES", 61 : "NO TOWED CARAVAN ALLOWED", 
                      62 : "NO TOWED TRAILER ALLOWED", 63 : "NO CAMPER OR MOTORHOME ALLOWED", 64 : "NO TURN ON RED", 
                      65 : "TURN PERMITTED ON RED", 7 : "LANE MERGING FROM THE LEFT", 8 : "LANE MERGE CENTRE", 
                      9 : "RAILWAY CROSSING PROTECTED"}
traffic_condition_dict ={11 : "VARIABLE SPEED", 16 : "TRAFFIC_SIGNAL", 17: "TRAFFIC_SIGN", 18: "RAILWAY CROSSING",
                         19: "NO OVERTAKING", 21: "PROTECTED OVERTAKING", 38: "BLACKSPOT", 22: "EVACUATION ROUTE"}
lane_divider_dict = {0:"No Marker", 1:"Long dashed line", 2:"Double solid line", 3:"Single solid line",
                     4:"Inner solid - outer dashed line", 5:"Inner dashed - outer solid line", 6:"Short dashed line", 7:"Shaded area marking",
                     8:"Dashed blocks",9:"Physical divider < 3m",10:"Double dashed line",11:"No divider",12:"Crossing alert line",13:"Center turn lane",14:"Unknown"}
lane_type = {1:"REGULAR",2:"HOV",4:"REVERSIBLE",6:"HOV + REVERSIBLE",8:"EXPRESS",10:"HOV + EXPRESS",12:"REVERSIBLE + EXPRESS",
            14:"HOV + REVERSIBLE + EXPRESS",16:"ACCELERATION",18:"HOV + ACCELERATION",20:"REVERSIBLE + ACCELERATION",
            22:"HOV + REVERSIBLE + ACCELERATION",24:"EXPRESS + ACCELERATION",32:"DECELERATION",34:"HOV + DECELERATION",
            36:"REVERSIBLE + DECELERATION",38:"HOV + REVERSIBLE + DECELERATION",40:"EXPRESS + DECELERATION",
            64:"AUXILIARY",128:"SLOW",256:"PASSING",512:"SHOULDER",1024:"REGULATED ACCESS",2048:"TURN",
            4096:"CENTRE TURN",8192:"TRUCK PARKING",16384:"PARKING",32768:"VARIABLE DRIVING",65536:"BICYCLE"}
feature_list = ["stop_signs","school_zone","icy_road","pedestrian","crosswalk","non_pedestrian_crossing","traffic_lights","traffic_signs",
                "lane_merge_right","lane_merge_left","lane_merge_center","highway","avoid_highway","oneway","both_ways","urban","limited_access",
                "paved","ramp","manoeuvre","roundabout","one_lane","multiple_lanes","overpass","underpass","variable_speed","railway_crossing","no_overtaking",
                "overtaking","falling_rocks","hills","tunnel","bridge","bump","dip","speed_bumps",
                "functional_class_1","functional_class_2","functional_class_3","functional_class_4","functional_class_5",
                "functional_class_1 (h)","functional_class_2 (h)","functional_class_3 (h)","functional_class_4 (h)","functional_class_5 (h)"]