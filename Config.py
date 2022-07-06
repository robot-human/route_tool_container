from os.path import isfile
import os
from configparser import ConfigParser
from Tools import Haversine, getRandomLocation

sample_separation = 0.0005
margin = 0.01
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

        if((lon_min > -170) and (lon_max < -45)):
            region = "us"
        elif((lon_min > -18) and (lon_max < 49)):
            region = "eu"
        else:
            region = "un"

        distance = Haversine(start_gps,end_gps)
        if((distance < 0.05) and (len(mid_gps) == 0)):
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

        tl = cfgParser.getint('config', 'traffic_lights')
        rc = cfgParser.getint('config', 'railway_crossing_signs')
        nover = cfgParser.getint('config', 'no_overtaking_signs')
        ts = cfgParser.getint('config', 'traffic_signs')
        traffic_condition_list = []
        if(tl):
            traffic_condition_list.append(16)
        if(rc):
            traffic_condition_list.append(18)
        if(nover):
            traffic_condition_list.append(19)
        if(ts):
            traffic_condition_list.append(17)
            display_condition = True
            rc = 1
            nover = 1
            stop = 1
            school = 1
            icy = 1
            crosswalk = 1
            rocks = 1
            animal_crossing = 1
            merge_r = 1
            merge_l = 1
            hills = 1
            traffic_signs_list = [i for i in range(66)]
        else:
            stop = cfgParser.getint('config', 'stop_signs')
            school = cfgParser.getint('config', 'school_zone_signs')
            icy = cfgParser.getint('config', 'icy_road_signs')
            crosswalk = cfgParser.getint('config', 'crosswalk_signs')
            rocks = cfgParser.getint('config', 'falling_rocks_signs')
            animal_crossing = cfgParser.getint('config', 'animal_crossing_signs')
            merge_r = cfgParser.getint('config', 'lane_merge_right_signs')
            merge_l = cfgParser.getint('config', 'lane_merge_left_signs')
            hills = cfgParser.getint('config', 'hills_signs')
            traffic_signs_list = []
            #if(stop==0 and icy==0 and rocks==0 and school==0 and crosswalk==0 and animal_crossing==0 and merge_r==0 and merge_l==0 and hills==0):   
            #    display_signs = False
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
            if(merge_r):
                traffic_signs_list.append(6)
            if(merge_l):
                traffic_signs_list.append(7)
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
        if(cfgParser.getint('config', 'lane_marker_no_marker')):
            lane_type.append(0)
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
        if(cfgParser.getint('config', 'hov_lane')):
            lane_type.append(2)
        if(cfgParser.getint('config', 'reversible_lane')):
            lane_type.append(4)
        if(cfgParser.getint('config', 'express_lane')):
            lane_type.append(8)
        if(cfgParser.getint('config', 'slow_lane')):
            lane_type.append(128)
        if(cfgParser.getint('config', 'auxiliary_lane')):
            lane_type.append(64)
        if(cfgParser.getint('config', 'shoulder_lane')):
            lane_type.append(512)
        if(cfgParser.getint('config', 'passing_lane')):
            lane_type.append(256)
        if(cfgParser.getint('config', 'turn_lane')):
            lane_type.append(2048)
        if(cfgParser.getint('config', 'parking_lane')):
            lane_type.append(16384)
        if(cfgParser.getint('config', 'center_turn_lane')):
            lane_type.append(4096)
        if(len(lane_type) > 0):
            lane_type_bool = 1
        else:
            lane_type_bool = 0

        boolean_features = {'highway':cfgParser.getint('config', 'highway'),'avoid_highway':cfgParser.getint('config', 'avoid_highway'),
                            'urban':cfgParser.getint('config', 'urban'),'oneway':cfgParser.getint('config', 'oneway'),
                            'both_ways':cfgParser.getint('config', 'both_ways'),'limited_access':cfgParser.getint('config', 'limited_access'),
                            'not_paved':cfgParser.getint('config', 'not_paved'), 'ramp':cfgParser.getint('config', 'ramp'),
                            'manoeuvre':cfgParser.getint('config', 'manoeuvre'),'roundabout':cfgParser.getint('config', 'roundabout'),
                            'one_lane':cfgParser.getint('config', 'one_lane'),'multiple_lanes':cfgParser.getint('config', 'multiple_lanes'),
                            'speed_category':speed_category_bool,'traffic_light':tl,'railway_crossing':rc,
                            'no_overtaking':nover,'traffic_sign':ts,'stop_sign':stop,'school_sign':school,'icy_sign':icy,
                            'crosswalk_sign':crosswalk,'falling_rocks_sign':rocks,'animal_crossing_sign':animal_crossing,
                            'merge_r_sign':merge_r,'merge_l_sign':merge_l,'hills_sign':hills,
                            'tunnel':cfgParser.getint('config', 'tunnel'),'bridge':cfgParser.getint('config', 'bridge'),
                            'road_roughness_good':cfgParser.getint('config', 'road_good'),'road_roughness_fair':cfgParser.getint('config', 'road_fair'),
                            'road_roughness_poor':cfgParser.getint('config', 'road_poor'), 'speed_bumps':cfgParser.getint('config', 'speed_bumps'),
                            'toll_booth':cfgParser.getint('config', 'toll_station'),'lane_markers_bool':lane_markers_bool,
                            'lane_type_bool':lane_type_bool,'parking_lot':cfgParser.getint('config', 'parking_lot')}

        attr_features = {'SPEED_CAT':speed_category}
        sign_features = {'CONDITION_TYPE':traffic_condition_list,'SIGN_TYPE':traffic_signs_list}
        lane_features = {'LANE_MARKERS':lane_markers,'LANE_TYPE':lane_type}
        query_features = {'boolean_features':boolean_features,'attr_features':attr_features,'sign_features':sign_features,'lane_features':lane_features}

        cfg = { 'route_type': route_type,
                'routes_number':routes_num,
                'start_location': start_gps,
                'end_location': end_gps,
                'mid_locations':mid_gps,
                'units':units,
                'region':region,
                'desired_route_length':desired_route_length,
                'visit_charge_station':visit_cs,
                'min_boundaries':(lat_min,lon_min),
                'max_boundaries':(lat_max,lon_max),
                'gps_locations': gps_locations,
                'query_features':query_features
                }