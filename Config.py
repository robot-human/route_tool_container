from os.path import isfile
import os
from configparser import ConfigParser
from Tools import Haversine, getRandomLocation

sample_separation = 0.001
margin = 0.02
maximum_gps_coordinates = 500
cfg = None
                         
if not isfile(os.path.join(os.getcwd(), 'config.ini')):
    print("config file doesn't exist")
else:
    cfgParser = ConfigParser()
    cfgParser.read(os.path.join(os.getcwd(), 'config.ini'))
    sections = cfgParser.sections()
    if len(sections) == 0 or 'config' not in sections:
        print("config file doesn't include [config] section")
    else:
        #route_type = cfgParser.get('config', 'route_type')
        route_type = 'point_to_point'
        routes_num = int(cfgParser.get('config', 'number_of_routes'))
        visit_cs = cfgParser.get('config', 'visit_charge_station')
        
        units = cfgParser.get('config', 'units')
        if(units == "mi"):
            #search_radius = 1.60934*float(cfgParser.get('config', 'search_radius'))
            desired_route_length = 1.60934*float(cfgParser.get('config', 'desired_route_length'))
        else:
            #search_radius = float(cfgParser.get('config', 'search_radius'))
            desired_route_length = float(cfgParser.get('config', 'desired_route_length'))

        if(cfgParser.get('config', 'start_gps') == ""):
            start_gps = 42.702324,-83.254979
        else:
            print("Not None")
            format = cfgParser.get('config', 'start_gps').find(".")
            if(format == -1):
                temp = cfgParser.get('config', 'start_gps').split(',')
                start_gps = (float(temp[0]+"."+temp[1]), float(temp[2]+"."+temp[3]))
            else:
                temp = cfgParser.get('config', 'start_gps').split(',')
                start_gps = (float(temp[0]), float(temp[1]))
        
        if(cfgParser.get('config', 'end_gps') == ""):
            end_gps = getRandomLocation(start_gps, desired_route_length*0.95)
        else:
            format = cfgParser.get('config', 'end_gps').find(".")
        
        format = cfgParser.get('config', 'end_gps').find(".")
        if(format == -1):
            temp = cfgParser.get('config', 'end_gps').split(',')
            n_mid_points = int(len(temp)/4)
            end_gps = (float(temp[4*(n_mid_points-1)]+"."+temp[4*(n_mid_points-1)+1]), float(temp[4*(n_mid_points-1)+2]+"."+temp[4*(n_mid_points-1)+3]))
            mid_gps = []
            lat_max = max(start_gps[0],end_gps[0]) + margin
            lon_max = max(start_gps[1],end_gps[1]) + margin
            lat_min = min(start_gps[0],end_gps[0]) - margin
            lon_min = min(start_gps[1],end_gps[1]) - margin
            for i in range(n_mid_points-1):
                next_point = (float(temp[4*i]+"."+temp[(4*i) + 1]),float(temp[(4*i)+2]+"."+temp[(4*i)+3]))
                lat_max = max(lat_max,next_point[0])
                lon_max = max(lon_max,next_point[1])
                lat_min = min(lat_min,next_point[0])
                lon_min = min(lon_min,next_point[1])
                mid_gps.append((next_point[0],next_point[1]))
        else:
            temp = cfgParser.get('config', 'end_gps').split(',')
            n_mid_points = int(len(temp)/2)
            end_gps = (float(temp[2*(n_mid_points-1)]), float(temp[2*(n_mid_points-1)+1]))
            mid_gps = []
            lat_max = max(start_gps[0],end_gps[0]) + margin
            lon_max = max(start_gps[1],end_gps[1]) + margin
            lat_min = min(start_gps[0],end_gps[0]) - margin
            lon_min = min(start_gps[1],end_gps[1]) - margin
            for i in range(n_mid_points-1):
                next_point = (float(temp[2*i]),float(temp[(2*i)+1]))
                lat_max = max(lat_max,next_point[0])
                lon_max = max(lon_max,next_point[1])
                lat_min = min(lat_min,next_point[0])
                lon_min = min(lon_min,next_point[1])
                mid_gps.append((next_point[0],next_point[1]))
        
        
        
        lat_max = lat_max + margin
        lon_max = lon_max + margin
        lat_min = lat_min - margin
        lon_min = lon_min - margin

        distance = Haversine(start_gps,end_gps)
        if((distance < 0.5) and (len(mid_gps) == 0)):
            mid_gps.append(getRandomLocation(start_gps, desired_route_length/2.8))
            #route_type = "closed_route"

        if(route_type == 'point_to_anywhere'):
            route_type = "point_to_point"
            end_gps = getRandomLocation(start_gps, desired_route_length*0.95)
            print(end_gps)

                    
        lat_interval = lat_max - lat_min
        lon_interval = lon_max - lon_min
        
        resolution = [abs(int(lat_interval/sample_separation)),abs(int(lon_interval/sample_separation))]
        lat_step = lat_interval / (resolution[0] - 1)
        lon_step = lon_interval / (resolution[1] - 1)
        
        gps_locations = []
        for i in range(resolution[0]):
            for j in range(resolution[1]):
                gps_locations.append((lat_min + lat_step * i, lon_min + lon_step * j))
        
        #Lane markers
        lane_markers = []
        if(cfgParser.getint('config', 'lane_marker_long_dashed')):
            lane_markers.append(1)
        if(cfgParser.getint('config', 'lane_marker_short_dashed')):
            lane_markers.append(6)
        if(cfgParser.getint('config', 'lane_marker_double_dashed')):
            lane_markers.append(10)
        if(cfgParser.getint('config', 'lane_marker_double_solid')):
            lane_markers.append(2)
        if(cfgParser.getint('config', 'lane_marker_single_solid')):
            lane_markers.append(3)
        if(cfgParser.getint('config', 'lane_marker_inner_solid_outter_dashed')):
            lane_markers.append(4)
        if(cfgParser.getint('config', 'lane_marker_inner_dashed_outter_solid')):
            lane_markers.append(5)
        if(cfgParser.getint('config', 'lane_marker_no_divider')):
            lane_markers.append(11)
        if(cfgParser.getint('config', 'lane_marker_physical_divider')):
            lane_markers.append(9)
        if(len(lane_markers) > 0):
            lane_markers_bool = 1
        else:
            lane_markers_bool = 0

        #Highway feature list setup
        if(cfgParser.getint('config', 'highway')):
            functional_class_list = [1,2, 3]
            speed_category_list = [1,2,3,4]
        elif(cfgParser.getint('config', 'avoid_highway')):
            functional_class_list = [4,5]
            speed_category_list = [5,6,7,8]
        else:
            functional_class_list = [1,2,3,4,5]
            speed_category_list = [1,2,3,4,5,6,7,8]
        
        #Ramp list setup        
        if(cfgParser.getint('config', 'ramp')):
            ramp_list = ['S','Y']
        else:
            ramp_list = ['Y','N']
        
        #Paved list setup
        if(cfgParser.getint('config', 'paved')):
            paved_list = ['S','Y']
        else:
            paved_list = ['Y','N']
        
        #Limited access list setup
        if(cfgParser.getint('config', 'limited_access')):
            limited_access_list = ['S','Y']
        else:
            limited_access_list = ['Y','N']
        
        #Bothways, oneway list setup
        if((cfgParser.getint('config', 'oneway')==1) and (cfgParser.getint('config', 'both_ways')==0)):
            direction_list = ['F','T']
        elif((cfgParser.getint('config', 'oneway')==0) and (cfgParser.getint('config', 'both_ways')==1)):
            direction_list = ['B']
        else:
            direction_list = ['F','T','B']
        
        #Urban list setup
        if(cfgParser.getint('config', 'urban')):
            urban_list = ['S','Y']
        else:
            urban_list = ['Y','N']
       
        #Overpass Underpass list setup
        overpass_list = []
        if(cfgParser.getint('config', 'overpass')):
            overpass_list.append(1)
        else:
            overpass_list.append(-1)
        if(cfgParser.getint('config', 'underpass')):
            overpass_list.append(2)
        else:
            overpass_list.append(-2)
        
        #Intersection list setup
        intersection_list = []
        if(cfgParser.getint('config', 'manoeuvre')):
            intersection_list.append(2)
        else:
            intersection_list.append(-2)
        if(cfgParser.getint('config', 'roundabout')):
            intersection_list.append(4)
        else:
            intersection_list.append(-4)
        if((cfgParser.getint('config', 'manoeuvre')==0) and (cfgParser.getint('config', 'roundabout')==0)):
            intersection_list = [-2,-4,1,2,3,4,5,6]
        
        #One lane road vs multi lane list setup
        if(cfgParser.getint('config', 'one_lane')):
            lane_list = [1]
        elif(cfgParser.getint('config', 'multiple_lanes')):
            lane_list = [2,3]
        elif((cfgParser.getint('config', 'multiple_lanes')==0) and(cfgParser.getint('config', 'one_lane')==0)):
            lane_list = [1,2,3]
        
        if(cfgParser.getint('config', 'tunnel')):
            tunnel_list = ['S','Y']
        else:
            tunnel_list = ['Y','N']
        if(cfgParser.getint('config', 'bridge')):
            bridge_list = ['Y']
        else:
            bridge_list = ['Y','N']
        
        traffic_condition_list = []
        display_condition = True
        display_signs = True
        vs = cfgParser.getint('config', 'variable_speed')
        tl = cfgParser.getint('config', 'traffic_lights')
        rc = cfgParser.getint('config', 'railway_crossing')
        nover = cfgParser.getint('config', 'no_overtaking')
        over = cfgParser.getint('config', 'overtaking')
        ts = cfgParser.getint('config', 'traffic_signs')
        if(vs==0 and tl==0 and rc==0 and nover==0 and over==0 and ts == 0):
            display_condition = False
            traffic_condition_list = [11,16,17,18,19,21,22,38]
        if(vs):
            traffic_condition_list.append(11)
        if(tl):
            traffic_condition_list.append(16)
        if(rc):
            traffic_condition_list.append(18)
        if(nover):
            traffic_condition_list.append(19)
        if(over):
            traffic_condition_list.append(21)
        if(ts):
            traffic_condition_list.append(17)
            traffic_signs_list = [i for i in range(66)]
        else:
            traffic_signs_list = []
            stop = cfgParser.getint('config', 'stop_signs')
            icy = cfgParser.getint('config', 'icy_road')
            rocks = cfgParser.getint('config', 'falling_rocks')
            school = cfgParser.getint('config', 'school_zone')
            crosswalk = cfgParser.getint('config', 'crosswalk')
            animal_crossing = cfgParser.getint('config', 'animal_crossing')
            tway = cfgParser.getint('config', 'two_way')
            urban = cfgParser.getint('config', 'urban')
            merge_r = cfgParser.getint('config', 'lane_merge_right')
            merge_l = cfgParser.getint('config', 'lane_merge_left')
            merge_c = cfgParser.getint('config', 'lane_merge_center')
            hills = cfgParser.getint('config', 'hills')
            if(stop==0 and icy==0 and rocks==0 and school==0 and crosswalk==0 and animal_crossing==0 and tway==0 and urban==0 and merge_r==0 and merge_l==0 and merge_c==0 and hills==0):   
                traffic_signs_list = [i for i in range(66)]
                display_signs = False
            if(stop):
                traffic_signs_list.append(20)
            if(icy):
                traffic_signs_list.append(28)
            if(rocks):
                traffic_signs_list.append(30)
            if(school):
                traffic_signs_list.append(31)
            if(crosswalk):
                traffic_signs_list.append(41)
            if(animal_crossing):
                traffic_signs_list.append(27)
            if(tway):
                traffic_signs_list.append(46)
            if(urban):
                traffic_signs_list.append(47)
            if(merge_r):
                traffic_signs_list.append(6)
            if(merge_l):
                traffic_signs_list.append(7)
            if(merge_c):
                traffic_signs_list.append(8) 
            if(hills):
                traffic_signs_list.extend([18,19,26])
        try:
            min_speed = cfgParser.getint('config', 'min_speed')
            boolean_speed_min = True
        except:
            min_speed = 0
            boolean_speed_min = False
        try:
            max_speed = cfgParser.getint('config', 'max_speed')
            if(max_speed == 0):
                max_speed = 200
                boolean_speed_max = False
            else:
                boolean_speed_max = True
        except:
            max_speed = 200
            boolean_speed_max = False
            
        boolean_features = {'stop_signs':cfgParser.getint('config', 'stop_signs'),'icy_road':cfgParser.getint('config', 'icy_road'),
                            'falling_rocks':cfgParser.getint('config', 'falling_rocks'),'school_zone':cfgParser.getint('config', 'school_zone'),
                            'crosswalk':cfgParser.getint('config', 'crosswalk'),
                            'animal_crossing':cfgParser.getint('config', 'animal_crossing'),'two_way':cfgParser.getint('config', 'two_way'),
                            'urban':cfgParser.getint('config', 'urban'),'lane_merge_r':cfgParser.getint('config', 'lane_merge_right'),
                            'lane_merge_l':cfgParser.getint('config', 'lane_merge_left'),'lane_merge_c':cfgParser.getint('config', 'lane_merge_center'),
                            'hills':cfgParser.getint('config', 'hills'),'traffic_signs':cfgParser.getint('config', 'traffic_signs'),
                            'highway':cfgParser.getint('config', 'highway'),'avoid_highway':cfgParser.getint('config', 'avoid_highway'),
                            'tunnel':cfgParser.getint('config', 'tunnel'),'bridge':cfgParser.getint('config', 'bridge'),
                            'variable_speed':cfgParser.getint('config', 'variable_speed'),'traffic_lights':cfgParser.getint('config', 'traffic_lights'),
                            'railway_crossing':cfgParser.getint('config', 'railway_crossing'),'no_overtaking':cfgParser.getint('config', 'no_overtaking'),
                            'overtaking':cfgParser.getint('config', 'overtaking'),    
                            'ramp':cfgParser.getint('config', 'ramp'),'paved':cfgParser.getint('config', 'paved'),
                            'access':cfgParser.getint('config', 'limited_access'),'both_ways':cfgParser.getint('config', 'both_ways'),
                            'oneway':cfgParser.getint('config', 'oneway'),'urban':cfgParser.getint('config', 'urban'),'overpass':cfgParser.getint('config', 'overpass'),
                            'underpass':cfgParser.getint('config', 'underpass'),'manoeuvre':cfgParser.getint('config', 'manoeuvre'),
                            'roundabout':cfgParser.getint('config', 'roundabout'),'one_lane':cfgParser.getint('config', 'one_lane'),
                            'multiple_lanes':cfgParser.getint('config', 'multiple_lanes'),'lane_markers_bool':lane_markers_bool}

        attr_features = {'FUNCTIONAL_CLASS':functional_class_list, 'SPEED_CATEGORY':speed_category_list, 'TRAVEL_DIRECTION':direction_list,  'URBAN':urban_list, 'LIMITED_ACCESS_ROAD':limited_access_list, 'PAVED':paved_list, 'RAMP':ramp_list, 
                        'INTERSECTION_CATEGORY':intersection_list, 'LANE_CATEGORY':lane_list, 'OVERPASS_UNDERPASS':overpass_list}
        sign_features = {'CONDITION_TYPE':traffic_condition_list,'SIGN_TYPE':traffic_signs_list,'display_condition':display_condition,'display_signs':display_signs}
        
        geom_features = {'TUNNEL':tunnel_list, 'BRIDGE':bridge_list}

        speed_features = {'SPEED_MIN' : min_speed,'SPEED_MAX' : max_speed, 'boolean_speed_min':boolean_speed_min,'boolean_speed_max':boolean_speed_max}
            
        query_features = {'boolean_features':boolean_features,'attr_features':attr_features, 'sign_features':sign_features, 'geom_features':geom_features, 
                          'speed_features':speed_features, 'lane_markers':lane_markers}
        
        cfg = { 'route_type': route_type,
                'routes_number':routes_num,
                'start_location': start_gps,
                'end_location': end_gps,
                'mid_locations':mid_gps,
                'units':units,
                'desired_route_length_km':desired_route_length,
                'visit_charge_station':visit_cs,
                'min_boundaries':(lat_min,lon_min),
                'max_boundaries':(lat_max,lon_max),
                'gps_locations': gps_locations,
                'query_features':query_features
                }

