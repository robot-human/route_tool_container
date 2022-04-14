from re import S
from HEREgraph2 import HEREgraph
import numpy as np
import networkx as nx
import gpxpy
import os
from Tools import Haversine, getRandomLocation, distance
import pandas as pd

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
        self.visit_charging_stationt = visit_charging_station
        self.route = []
        self.route_length = 0
        self.driving_time = 0
        self.n_features = 0
        self.rank_points = 0
        self.output_path = os.path.join(os.getcwd(), 'gpx/')
        return None
    
    def auxRoute(self, G, start_loc, end_loc):
        start_node_distances = []
        end_node_distances = []
        signs = getSigns(G)
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
        s_loc = G.nodes[start_node]['LOC']
        e_loc = G.nodes[end_node]['LOC']
        ref_dist = 10000
        for cs in self.charging_stations:
            loc = (int(self.charging_stations[cs]['LAT'])/100000, int(self.charging_stations[cs]['LON'])/100000)
            dist = distance(s_loc,loc) + distance(e_loc,loc)
            if(dist < ref_dist):
                ref_dist = dist
                nearest_cs = loc
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
            return self.pointToAnywhereRoute(G, start_node)
        elif(self.route_type == 'point_to_charge_station'):
            return self.pointToChargeStationRoute(G, start_node)
        else:
            print("Invalid route type")
            return None
    def getRouteLength(self):
        return self.route_length
        
    def pointToPointRoute(self, G, start_node, end_node):
        if(self.visit_charging_stationt):
            visit_point = self.closestChargingStation(G, start_node, end_node)
            mid_node, _ = G.findNodeFromCoord(visit_point)
            return self.midPointPath(G, start_node, end_node, mid_node)
        else:
            return nx.shortest_path(G, start_node, end_node, weight='WEIGHT')
    def closedRoute(self, G, start_node, end_node):
        if(self.visit_charging_stationt):
            visit_point = self.closestChargingStation(G, start_node, end_node)
            mid_node, _ = G.findNodeFromCoord(visit_point)
            route = self.midPointPath(G, start_node, mid_node, end_node)
            route.pop(len(route)-1)
            route.extend(nx.shortest_path(G, mid_node, start_node, weight='WEIGHT'))
            return route     
        else:
            return self.midPointPath(G, start_node, start_node, end_node)

    def pointToAnywhereRoute(self, G, start_node):
        if(self.visit_charging_stationt):
            startLoc = G.nodes[start_node]['LOC']
            endLocation = getRandomLocation(startLoc, self.search_radius)
            end_node, _ = G.findNodeFromCoord(endLocation)
            visit_point = self.closestChargingStation(G, start_node, end_node)
            mid_node, _ = G.findNodeFromCoord(visit_point)
            return self.midPointPath(G, start_node, end_node, mid_node)
        else:
            startLoc = G.nodes[start_node]['LOC']
            endLocation = getRandomLocation(startLoc, self.search_radius)
            end_node, _ = G.findNodeFromCoord(endLocation)
            return nx.shortest_path(G, start_node, end_node, weight='WEIGHT')

    def pointToChargeStationRoute(self, G, start_node):
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
            mid_node, _ = G.findNodeFromCoord(charging_st)
            try:
                route = self.midPointPath(G, start_node, start_node, mid_node)
                route_found = True
            except:
                non_route_available.append(charging_st)
                print(non_route_available)
        return route
    
    def setRoute(self, G, start_point, mid_point):
        increment = 5.0
        self.route = self.findRoute(G, start_point, mid_point)
        for i in range(1,len(self.route)):
            link_data = G.get_edge_data(self.route[i-1],self.route[i])
            link_attributes = link_data[list(link_data.keys())[0]]
            self.route_length += link_attributes['LINK_LENGTH']
            self.driving_time += (1/link_attributes['AVG_SPEED'])*(link_attributes['LINK_LENGTH']/1000)
            link_attributes['WEIGHT'] = increment*link_attributes['WEIGHT']
        self.route_length = self.route_length/1000
        return None
     
    def displayChargeStations(self,gpx):
        for s in self.charging_stations:
            gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(int(self.charging_stations[s]['LAT'])/100000,int(self.charging_stations[s]['LON'])/100000, name=self.charging_stations[s]['CONNECTORTYPE'])) 
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
        print(f"Driving time in hrs = {self.driving_time}")
        print(f"Number of desired features = {self.n_features}")
        print(f"Query points = {self.rank_points}")
        return None

    def displayRoadGeom(self, gpx, link_attributes, loc):
        if(link_attributes["TUNNEL"] == 'Y'):
            gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0],loc[1], name=f"Tunnel"))
            self.n_features += 1
        if(link_attributes["BRIDGE"] == 'Y'):
            gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0],loc[1], name=f"Bridge"))
            self.n_features += 1
        return None

    def displayFeature(self, gpx, loc, link_attributes, values, start, feat_name):
        if(link_attributes != None):
            if(start==False and (link_attributes in values)):
                gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0],loc[1], name=f"Start of {feat_name}"))
                start = True
                self.n_features += 1
            elif(start==True and (link_attributes not in values)):
                gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0],loc[1], name=f"End of {feat_name}"))
                start = False
        return start

    def createCSVFile(self):
        self.features_file_name = f"./gpx/features_count.csv"
        head = ",".join([str(item) for item in feature_list])
        self.feat_count = []
        for feat in feature_list:
            self.feat_count.append(0)
        features_file = open(self.features_file_name, "w")
        features_file.write(head+"\n")
        features_file.close()

    def setCSVFeatures(self, G, route_num: int):
        self.createCSVFile()
        file_name = f"./gpx/route{route_num}_features.csv"
        head = "Route_name,LAT,LON,Link_length,Avg_speed,Time,Accum_len,Accum_time\n"
        features_file = open(file_name, "w")
        features_file.write(head)
        features_file.close()
        features_file = open(file_name, "a")
        len_accum = 0
        time_accum = 0
        for i in range(1,len((self.route))):
            str_line = str(route_num)
            link_data = G.get_edge_data(self.route[i-1],self.route[i])
            link_attributes = link_data[list(link_data.keys())[0]]
            self.fillFeaturesCSV(link_attributes)
            lat = str(link_attributes['LAT'].split(",")[0])
            lon = str(link_attributes['LON'].split(",")[0])
            link_length = 0.001*float(link_attributes['LINK_LENGTH'])
            time = 1/(float(link_attributes['AVG_SPEED'])/link_length)
            len_accum = len_accum + link_length
            time_accum = time_accum + time
            str_line = str_line + "," + lat + "," + lon + "," + str(link_attributes['LINK_LENGTH']) + "," + str(link_attributes['AVG_SPEED'])
            str_line = str_line + "," + str(time) + "," + str(len_accum) + "," + str(time_accum) + "\n"
            features_file.write(str_line)

        feat_line = ",".join([str(item) for item in self.feat_count])
        features_file = open(self.features_file_name, "a")
        features_file.write(feat_line)
        features_file.close()

        print(self.feat_count)
        print("")
        print("************  RESUME *************")
        print("Length:   ",len_accum)
        print("Time:     ",time_accum*1.4)
        print("")
        features_file.close()

    def setGPXFile(self, G, route_num: int, path_directory: str, cfg: dict):
        gpx_file_name = f'./{path_directory}/route{route_num}_staticfeaturesfile.gpx'
        static_features_file_name = f"./{path_directory}/route{route_num}_staticfeaturesfile.csv"
        features_file = open(static_features_file_name, "w")
        features_file.write("Route_name,LAT,LON,feature_type_id,feature_type\n")
        features_file.close()
        features_file = open(static_features_file_name, "a")
        gpx = gpxpy.gpx.GPX()
        gpx_track = gpxpy.gpx.GPXTrack(name=gpx_file_name)
        gpx.tracks.append(gpx_track)
        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)
        start = [False,False,False,False,False,False,False,False,False,False,False,False]
        ref_speed_limit = None
        
        for i in range(1,len((self.route))):
            loc = G.nodes[self.route[i-1]]['LOC']
            link_data = G.get_edge_data(self.route[i-1],self.route[i])
            link_attributes = link_data[list(link_data.keys())[0]]
            if(str(link_attributes['LANE_DIVIDER_MARKER']) != 'None'):
                lane_divider = f"{lane_divider_dict[link_attributes['LANE_DIVIDER_MARKER']]}"
            else:
                lane_divider = None
            speed_limit = link_attributes['SPEED_LIMIT']
            if(speed_limit != None):
                features_file.write(f"{gpx_file_name},{loc[0]},{loc[1]},{speed_limit},SPEED_LIMIT\n")
            if(speed_limit != ref_speed_limit):
                gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0],loc[1], name=f"Speed limit: {speed_limit}"))
                ref_speed_limit = speed_limit
              
            if(cfg['query_features']['boolean_features']['highway']):
                start[0] = self.displayFeature(gpx, loc, link_attributes['FUNCTIONAL_CLASS'], [1,2,3], start[0], "highway")
            if(cfg['query_features']['boolean_features']['avoid_highway']):
                start[1] = self.displayFeature(gpx, loc, link_attributes['FUNCTIONAL_CLASS'], [4,5], start[1], "avoid_highway")
            if(cfg['query_features']['boolean_features']['ramp']):
                start[2] = self.displayFeature(gpx, loc, link_attributes['RAMP'], ['Y'], start[2], "Ramp")
            if(cfg['query_features']['boolean_features']['paved']):
                start[3] = self.displayFeature(gpx, loc, link_attributes['PAVED'], ['Y'], start[3], "Paved")
            if(cfg['query_features']['boolean_features']['access']):
                start[4] = self.displayFeature(gpx, loc, link_attributes['LIMITED_ACCESS_ROAD'], ['Y'], start[4], "Limited access")
            if(cfg['query_features']['boolean_features']['both_ways']):
                start[5] = self.displayFeature(gpx, loc, link_attributes['TRAVEL_DIRECTION'], ['B'], start[5], "Bothways")
            if(cfg['query_features']['boolean_features']['oneway']):
                start[6] = self.displayFeature(gpx, loc, link_attributes['TRAVEL_DIRECTION'], ['F','T'], start[6], "One way")
            if(cfg['query_features']['boolean_features']['urban']):
                start[7] = self.displayFeature(gpx, loc, link_attributes['URBAN'], ['Y'], start[7], "Urban")
            if(cfg['query_features']['boolean_features']['overpass']):
                start[8] = self.displayFeature(gpx, loc, link_attributes['OVERPASS_UNDERPASS'], ['1'], start[8], "Overpass")
            if(cfg['query_features']['boolean_features']['underpass']):
                start[9] = self.displayFeature(gpx, loc, link_attributes['OVERPASS_UNDERPASS'], ['2'], start[9], "Underpass")
            if(cfg['query_features']['boolean_features']['one_lane']):
                start[10] = self.displayFeature(gpx, loc, link_attributes['LANE_CATEGORY'], [1], start[12], "One lane")
            if(cfg['query_features']['boolean_features']['multiple_lanes']):
                start[11] = self.displayFeature(gpx, loc, link_attributes['LANE_CATEGORY'], [2,3,4], start[13], "Multi lane")

            if(cfg['query_features']['boolean_features']['manoeuvre']):
                if(link_attributes['INTERSECTION'] != None):
                    if(int(link_attributes['INTERSECTION']) == 2):
                        gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0],loc[1], name=f"Manoeuvre"))
                        self.n_features += 1  
            if(cfg['query_features']['boolean_features']['roundabout']):
                if(link_attributes['INTERSECTION'] != None):
                    if(int(link_attributes['INTERSECTION']) == 4):
                        gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0],loc[1], name=f"Roundabout"))
                        self.n_features += 1


            if(len(link_attributes[f"TRAFFIC_CONDITION_{link_attributes['EDGE_DIRECTION']}"]) > 0):
                for sig in link_attributes[f"TRAFFIC_CONDITION_{link_attributes['EDGE_DIRECTION']}"]:
                    tsignal = int(sig)
                    gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0], loc[1], name=f"{traffic_condition_dict[tsignal]}"))
                    features_file.write(f"{gpx_file_name},{loc[0]},{loc[1]},{tsignal},{traffic_condition_dict[tsignal]}\n")
                    self.n_features += 1
            if(len(link_attributes[f"TRAFFIC_SIGNS_{link_attributes['EDGE_DIRECTION']}"]) > 0):
                for sign in link_attributes[f"TRAFFIC_SIGNS_{link_attributes['EDGE_DIRECTION']}"]:
                    tsign = int(sign)
                    gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(loc[0], loc[1], name=f"{traffics_sign_dict[tsign]}"))  
                    features_file.write(f"{gpx_file_name},{loc[0]},{loc[1]},{tsign},{traffics_sign_dict[tsign]}\n")
                    self.n_features += 1
            
            self.displayRoadGeom(gpx, link_attributes, loc)
            
            gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(loc[0],loc[1], name=f"Lane divider marker: {lane_divider}, Speed limit: {speed_limit}")) 
        features_file.close()
        self.displayChargeStations(gpx)
        with open(gpx_file_name, "w") as f:
            f.write(gpx.to_xml())   
        f.close()
        self.routeRankPoints()
        self.displayRouteInfo()
        return None
    
    def fillFeaturesCSV(self,attributes):
        print(attributes)
        edge_dir = attributes['EDGE_DIRECTION']
        if(20 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[0] += 1
        if(31 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[1] += 1
        if(28 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[2] += 1
        if(41 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[3] += 1
        if(41 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[4] += 1
        if((27 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']) or (59 in attributes[f'TRAFFIC_SIGNS_{edge_dir}'])):
            self.feat_count[5] += 1
        if(16 in attributes[f'TRAFFIC_CONDITION_{edge_dir}']):
            self.feat_count[6] += 1
        if(17 in attributes[f'TRAFFIC_CONDITION_{edge_dir}']):
            self.feat_count[7] += 1
        if(6 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[8] += 1
        if(7 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[9] += 1
        if(8 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[10] += 1
        if(int(attributes[f'FUNCTIONAL_CLASS']) <= 3):
            self.feat_count[11] += attributes['LINK_LENGTH']*0.001
        if(int(attributes[f'FUNCTIONAL_CLASS']) >= 4):
            self.feat_count[12] += attributes['LINK_LENGTH']*0.001
        if(attributes[f'TRAVEL_DIRECTION'] != "B"):
            self.feat_count[13] += attributes['LINK_LENGTH']*0.001
        if(attributes[f'TRAVEL_DIRECTION'] == "B"):
            self.feat_count[14] += attributes['LINK_LENGTH']*0.001
        if(47 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[15] += 1
        if(str(attributes['LIMITED_ACCESS_ROAD']) != 'None'):
            self.feat_count[16] += 1
        if(str(attributes['PAVED']) != 'None'):
            self.feat_count[17] += 1
        if(str(attributes['RAMP']) != 'None'):
            self.feat_count[18] += 1
        if(str(attributes['INTERSECTION']) == '2'):
            self.feat_count[19] += 1
        if(str(attributes['INTERSECTION']) == '4'):
            self.feat_count[20] += 1
        if(str(attributes['LANE_CATEGORY']) == '1'):
            self.feat_count[21] += 1
        if((str(attributes['LANE_CATEGORY']) == '2') or (str(attributes['LANE_CATEGORY']) == '3')):
            self.feat_count[22] += 1
        if(str(attributes['OVERPASS_UNDERPASS']) == '1'):
            self.feat_count[23] += 1
        if(str(attributes['OVERPASS_UNDERPASS']) == '2'):
            self.feat_count[24] += 1
        if(11 in attributes[f'TRAFFIC_CONDITION_{edge_dir}']):
            self.feat_count[25] += 1
        if(18 in attributes[f'TRAFFIC_CONDITION_{edge_dir}']):
            self.feat_count[26] += 1
        if(19 in attributes[f'TRAFFIC_CONDITION_{edge_dir}']):
            self.feat_count[27] += 1
        if(21 in attributes[f'TRAFFIC_CONDITION_{edge_dir}']):
            self.feat_count[28] += 1
        if(30 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']):
            self.feat_count[29] += 1
        if((18 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']) or (19 in attributes[f'TRAFFIC_SIGNS_{edge_dir}']) or (26 in attributes[f'TRAFFIC_SIGNS_{edge_dir}'])):
            self.feat_count[30] += 1
        if(attributes['TUNNEL'] == 'Y'):
            self.feat_count[31] += 1
        if(attributes['BRIDGE'] == 'Y'):
            self.feat_count[32] += 1

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
                     4:"Inner solid, outer dashed line", 5:"Inner dashed, outer solid line", 6:"Short dashed line", 7:"Shaded area marking",
                     8:"Dashed blocks",9:"Physical divider < 3m",10:"Double dashed line",11:"No divider",12:"Crossing alert line",13:"Center turn lane"}

feature_list = ["stop_signs","school_zone","icy_road","pedestrian","crosswalk","non_pedestrian_crossing","traffic_lights","traffic_signs",
                "lane_merge_right","lane_merge_left","lane_merge_center","highway","avoid_highway","oneway","both_ways","urban","limited_access",
                "paved","ramp","manoeuvre","roundabout","one_lane","multiple_lanes","overpass","underpass","variable_speed","railway_crossing","no_overtaking",
                "overtaking","falling_rocks","hills","tunnel","bridge",]