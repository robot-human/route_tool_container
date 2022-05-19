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
        routes_num = int(cfgParser.get('config', 'number_of_routes'))
        visit_cs = cfgParser.get('config', 'visit_charge_station')
        route_type = 'point_to_point'
        
        units = cfgParser.get('config', 'units')
        if((units == "mi") or (units.lower() == "m")):
            desired_route_length = 1.60934*float(cfgParser.get('config', 'desired_route_length'))
        else:
            desired_route_length = float(cfgParser.get('config', 'desired_route_length'))

        if(cfgParser.get('config', 'start_gps') == ""):
            start_gps = 42.702324,-83.254979
        else:
            format = cfgParser.get('config', 'start_gps').find(".")
            if(format == -1):
                temp = cfgParser.get('config', 'start_gps').split(',')
                start_gps = (float(temp[0]+"."+temp[1]), float(temp[2]+"."+temp[3]))
            else:
                temp = cfgParser.get('config', 'start_gps').split(',')
                start_gps = (float(temp[0]), float(temp[1]))
        mid_gps = []
        if(cfgParser.get('config', 'end_gps') == ""):
            end_gps = getRandomLocation(start_gps, desired_route_length*0.95)
            lat_max = max(start_gps[0],end_gps[0]) + margin
            lon_max = max(start_gps[1],end_gps[1]) + margin
            lat_min = min(start_gps[0],end_gps[0]) - margin
            lon_min = min(start_gps[1],end_gps[1]) - margin
        else:
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
            mid_gps.append(getRandomLocation(start_gps, desired_route_length/3.0))

        if(route_type == 'point_to_anywhere'):
            route_type = "point_to_point"
            end_gps = getRandomLocation(start_gps, desired_route_length*0.8)

                    
        lat_interval = lat_max - lat_min
        lon_interval = lon_max - lon_min
        
        resolution = [abs(int(lat_interval/sample_separation)),abs(int(lon_interval/sample_separation))]
        lat_step = lat_interval / (resolution[0] - 1)
        lon_step = lon_interval / (resolution[1] - 1)
        
        gps_locations = []
        for i in range(resolution[0]):
            for j in range(resolution[1]):
                gps_locations.append((lat_min + lat_step * i, lon_min + lon_step * j))
        
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

        #Urban list setup
        if(cfgParser.getint('config', 'urban')):
            urban_list = ['S','Y']
        else:
            urban_list = ['Y','N']

        #Bothways, oneway list setup
        if((cfgParser.getint('config', 'oneway')==1) and (cfgParser.getint('config', 'both_ways')==0)):
            direction_list = ['F','T']
        elif((cfgParser.getint('config', 'oneway')==0) and (cfgParser.getint('config', 'both_ways')==1)):
            direction_list = ['B']
        else:
            direction_list = ['F','T','B']

        #Limited access list setup
        if(cfgParser.getint('config', 'limited_access')):
            limited_access_list = ['S','Y']
        else:
            limited_access_list = ['Y','N']
    
        #Paved list setup
        if(cfgParser.getint('config', 'paved')):
            paved_list = ['S','Y']
        else:
            paved_list = ['Y','N']
        
        #Ramp list setup        
        if(cfgParser.getint('config', 'ramp')):
            ramp_list = ['S','Y']
        else:
            ramp_list = ['Y','N']
        
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

        #Speed category
        speed_category=[]
        if(cfgParser.getint('config', 'speed_130km_80mph')):
            speed_category.append(1)
        if(cfgParser.getint('config', 'speed_101kph_to_130kph_65_to_80mph')):
            speed_category.append(2)
        if(cfgParser.getint('config', 'speed_91kph_to_100kph_55mph_to_64mph')):
            speed_category.append(3)
        if(cfgParser.getint('config', 'speed_71kph_to_90kph_41mph_to_54mph')):
            speed_category.append(4)
        if(cfgParser.getint('config', 'speed_51kph_to_70kph_31mph_to_40mph')):
            speed_category.append(5)
        if(cfgParser.getint('config', 'speed_31kph_to_50kph_21mph_to_30mph')):
            speed_category.append(6)
        if(cfgParser.getint('config', 'speed_11kph_to_30kph_6mph_to_20mph')):
            speed_category.append(7)
        if(cfgParser.getint('config', 'speed_11kph_6mph')):
            speed_category.append(8)
        if(len(speed_category) > 0):
            speed_category_bool=True
        else:
            speed_category_bool=False

        vs = cfgParser.getint('config', 'variable_speed')
        tl = cfgParser.getint('config', 'traffic_lights')
        rc = cfgParser.getint('config', 'railway_crossing')
        nover = cfgParser.getint('config', 'no_overtaking')
        over = cfgParser.getint('config', 'overtaking')
        ts = cfgParser.getint('config', 'traffic_signs')
        traffic_condition_list = []
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
            display_condition = True
            traffic_signs_list = [i for i in range(66)]
        else:
            stop = cfgParser.getint('config', 'stop_signs')
            school = cfgParser.getint('config', 'school_zone')
            icy = cfgParser.getint('config', 'icy_road')
            crosswalk = cfgParser.getint('config', 'crosswalk')
            rocks = cfgParser.getint('config', 'falling_rocks')
            animal_crossing = cfgParser.getint('config', 'animal_crossing')
            tway = cfgParser.getint('config', 'two_way')
            merge_r = cfgParser.getint('config', 'lane_merge_right')
            merge_l = cfgParser.getint('config', 'lane_merge_left')
            merge_c = cfgParser.getint('config', 'lane_merge_center')
            hills = cfgParser.getint('config', 'hills')
            traffic_signs_list = []
            if(stop==0 and icy==0 and rocks==0 and school==0 and crosswalk==0 and animal_crossing==0 and tway==0 and merge_r==0 and merge_l==0 and merge_c==0 and hills==0):   
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
            if(merge_r):
                traffic_signs_list.append(6)
            if(merge_l):
                traffic_signs_list.append(7)
            if(merge_c):
                traffic_signs_list.append(8) 
            if(hills):
                traffic_signs_list.extend([18,19,26])
        if(len(traffic_condition_list) > 0):
            display_condition = True
        else:
            display_condition = False
        if(len(traffic_signs_list) > 0):
            display_signs = True
        else:
            display_signs = False
        
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
        
        #Lane type
        lane_type = []
        if(cfgParser.getint('config', 'lane_marker_long_dashed')):
            lane_type.append(1)
        if(cfgParser.getint('config', 'lane_marker_short_dashed')):
            lane_type.append(6)
        if(cfgParser.getint('config', 'hov')):
            lane_type.append(2)
        if(cfgParser.getint('config', 'reversible')):
            lane_type.append(4)
        if(cfgParser.getint('config', 'express')):
            lane_type.append(8)
        if(cfgParser.getint('config', 'slow')):
            lane_type.append(128)
        if(cfgParser.getint('config', 'auxiliary')):
            lane_type.append(64)
        if(cfgParser.getint('config', 'shoulder')):
            lane_type.append(512)
        if(cfgParser.getint('config', 'passing')):
            lane_type.append(256)
        if(cfgParser.getint('config', 'turn')):
            lane_type.append(2048)
        if(cfgParser.getint('config', 'parking')):
            lane_type.append(16384)
        if(cfgParser.getint('config', 'center_turn')):
            lane_type.append(4096)
        if(cfgParser.getint('config', 'bikelane')):
            lane_type.append(65536)
        if(len(lane_type) > 0):
            lane_type_bool = 1
        else:
            lane_type_bool = 0

        
        
        """
        boolean_features = {'stop_signs':cfgParser.getint('config', 'stop_signs'),'icy_road':cfgParser.getint('config', 'icy_road'),
                            'falling_rocks':cfgParser.getint('config', 'falling_rocks'),'school_zone':cfgParser.getint('config', 'school_zone'),
                            'crosswalk':cfgParser.getint('config', 'crosswalk'),'speed_category':speed_category_bool,
                            'animal_crossing':cfgParser.getint('config', 'animal_crossing'),'two_way':cfgParser.getint('config', 'two_way'),
                            'urban':cfgParser.getint('config', 'urban'),'lane_merge_r':cfgParser.getint('config', 'lane_merge_right'),
                            'lane_merge_l':cfgParser.getint('config', 'lane_merge_left'),'lane_merge_c':cfgParser.getint('config', 'lane_merge_center'),
                            'hills':cfgParser.getint('config', 'hills'),'traffic_signs':cfgParser.getint('config', 'traffic_signs'),
                            'highway':cfgParser.getint('config', 'highway'),'avoid_highway':cfgParser.getint('config', 'avoid_highway'),
                            'tunnel':cfgParser.getint('config', 'tunnel'),'bridge':cfgParser.getint('config', 'bridge'),
                            'variable_speed':cfgParser.getint('config', 'variable_speed'),'traffic_lights':cfgParser.getint('config', 'traffic_lights'),
                            'railway_crossing':cfgParser.getint('config', 'railway_crossing'),'no_overtaking':cfgParser.getint('config', 'no_overtaking'),
                            'overtaking':cfgParser.getint('config', 'overtaking'),'ramp':cfgParser.getint('config', 'ramp'),
                            'paved':cfgParser.getint('config', 'paved'),'limited_access':cfgParser.getint('config', 'limited_access'),
                            'both_ways':cfgParser.getint('config', 'both_ways'),'oneway':cfgParser.getint('config', 'oneway'),
                            'urban':cfgParser.getint('config', 'urban'),'overpass':cfgParser.getint('config', 'overpass'),
                            'underpass':cfgParser.getint('config', 'underpass'),'manoeuvre':cfgParser.getint('config', 'manoeuvre'),
                            'roundabout':cfgParser.getint('config', 'roundabout'),'one_lane':cfgParser.getint('config', 'one_lane'),
                            'multiple_lanes':cfgParser.getint('config', 'multiple_lanes'),'lane_markers_bool':lane_markers_bool,
                            'road_roughness_good':road_roughness_good,'road_roughness_fair':road_roughness_fair,
                            'road_roughness_poor':road_roughness_poor,'lane_type_bool':lane_type_bool,'speed_bumps':cfgParser.getint('config', 'speed_bumps'),
                            'toll_booth':cfgParser.getint('config', 'toll_station')}

        #, 'SPEED_CATEGORY':speed_category_list
        attr_features = {'FUNCTIONAL_CLASS':functional_class_list, 'TRAVEL_DIRECTION':direction_list,  'URBAN':urban_list, 'LIMITED_ACCESS_ROAD':limited_access_list, 
                         'PAVED':paved_list, 'RAMP':ramp_list, 'INTERSECTION_CATEGORY':intersection_list, 'LANE_CATEGORY':lane_list, 'OVERPASS_UNDERPASS':overpass_list,
                         'SPEED_CAT':speed_category}
        
        
        geom_features = {'TUNNEL':tunnel_list, 'BRIDGE':bridge_list}

        speed_features = {'SPEED_MIN' : min_speed,'SPEED_MAX' : max_speed, 'boolean_speed_min':boolean_speed_min,'boolean_speed_max':boolean_speed_max}
            
        lane_features = {'LANE_MARKERS':lane_markers,'LANE_TYPE':lane_type}

        query_features = {'boolean_features':boolean_features,'attr_features':attr_features, 'sign_features':sign_features, 'geom_features':geom_features, 
                          'speed_features':speed_features, 'lane_features':lane_features}
        
        """

        boolean_features = {'highway':cfgParser.getint('config', 'highway'),'avoid_highway':cfgParser.getint('config', 'avoid_highway'),
                            'urban':cfgParser.getint('config', 'urban'),'oneway':cfgParser.getint('config', 'oneway'),
                            'both_ways':cfgParser.getint('config', 'both_ways'),'limited_access':cfgParser.getint('config', 'limited_access'),
                            'paved':cfgParser.getint('config', 'paved'), 'ramp':cfgParser.getint('config', 'ramp'),
                            'manoeuvre':cfgParser.getint('config', 'manoeuvre'),'roundabout':cfgParser.getint('config', 'roundabout'),
                            'one_lane':cfgParser.getint('config', 'one_lane'),'multiple_lanes':cfgParser.getint('config', 'multiple_lanes'),
                            'overpass':cfgParser.getint('config', 'overpass'),'underpass':cfgParser.getint('config', 'underpass'),
                            'speed_category':speed_category_bool,'variable_speed':vs,'traffic_light':tl,'railway_crossing':rc,
                            'no_overtaking':nover,'overtaking':over,'traffic_sign':ts,'stop_sign':stop,'school_sign':school,'icy_sign':icy,
                            'crosswalk_sign':crosswalk,'falling_rocks_sign':rocks,'animal_crossing_sign':animal_crossing,
                            'tway_sign':tway,'merge_r_sign':merge_r,'merge_l_sign':merge_l,'merge_c_sign':merge_c,'hills_sign':hills,
                            'tunnel':cfgParser.getint('config', 'tunnel'),'bridge':cfgParser.getint('config', 'bridge'),
                            'road_roughness_good':cfgParser.getint('config', 'road_good'),'road_roughness_fair':cfgParser.getint('config', 'road_fair'),
                            'road_roughness_poor':cfgParser.getint('config', 'road_poor'), 'speed_bumps':cfgParser.getint('config', 'speed_bumps'),
                            'toll_booth':cfgParser.getint('config', 'toll_station'),'lane_markers_bool':lane_markers_bool,
                            'lane_type_bool':lane_type_bool}

        sign_features = {'CONDITION_TYPE':traffic_condition_list,'SIGN_TYPE':traffic_signs_list}
        lane_features = {'LANE_MARKERS':lane_markers,'LANE_TYPE':lane_type}
        query_features = {'boolean_features':boolean_features,'sign_features':sign_features,'lane_features':lane_features}

        cfg = { 'route_type': route_type,
                'routes_number':routes_num,
                'start_location': start_gps,
                'end_location': end_gps,
                'mid_locations':mid_gps,
                'units':units,
                'desired_route_length':desired_route_length,
                'visit_charge_station':visit_cs,
                'min_boundaries':(lat_min,lon_min),
                'max_boundaries':(lat_max,lon_max),
                'gps_locations': gps_locations,
                'query_features':query_features
                }