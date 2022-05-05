import os
from os.path import isfile
from configparser import ConfigParser

config_ini_file_name = 'config.ini'
input_file_name = 'request_input.txt'
default_dict = {
    'route_type': 'point_to_point', 
    'start_gps': '', 
    'end_gps': '0',
    'number_of_routes':'1',
    'units': 'km',
    'search_radius': '60.0', 
    'desired_route_length': '10.0', 
    'visit_charge_station': '1', 
    'stop_signs': '0', 
    'school_zone': '0', 
    'icy_road': '0', 
    'pedestrian': '0', 
    'crosswalk': '0', 
    'non_pedestrian_crossing': '0', 
    'traffic_lights': '0', 
    'traffic_signs': '0', 
    'lane_merge_right': '0', 
    'lane_merge_left': '0', 
    'lane_merge_center': '0',
    'lane_marker_long_dashed' : '0',
    'lane_marker_short_dashed' : '0',
    'lane_marker_double_dashed' : '0',
    'lane_marker_double_solid' : '0',
    'lane_marker_single_solid' : '0',
    'lane_marker_inner_solid_outter_dashed' : '0',
    'lane_marker_inner_dashed_outter_solid' : '0',
    'lane_marker_no_divider' : '0',
    'lane_marker_physical_divider' : '0',
    'highway': '0', 
    'avoid_highway': '0', 
    'oneway': '0', 
    'both_ways': '0', 
    'urban': '0', 
    'limited_access': '0', 
    'paved': '0', 
    'ramp': '0', 
    'manoeuvre': '0', 
    'roundabout': '0', 
    'one_lane': '0', 
    'multiple_lanes': '0', 
    'overpass': '0', 
    'underpass': '0', 
    'variable_speed': '0', 
    'railway_crossing': '0', 
    'no_overtaking': '0', 
    'overtaking': '0', 
    'falling_rocks': '0', 
    'two_way': '0', 
    'hills': '0', 
    'tunnel': '0', 
    'bridge': '0'
    }

if not isfile(os.path.join(os.getcwd(), input_file_name)):
    print("input file doesn't exist")
else:
    with open(input_file_name,'r') as input_file:
        input = input_file.readlines()
    for i in range(1,len(input)):
        if(input[i] != "\n"):
            print(input[i])
            line = input[i].split("=")
            var = line[0].replace(" ", "").lower()
            val = line[1].replace(" ", "").replace("\n","")
            default_dict[var] = val
    input_file.close()

f = open(config_ini_file_name, "w")
f.write("[config]\n")
for k in default_dict.keys():
    print(k,default_dict[k])
    f.write(k+"="+default_dict[k]+"\n")
f.close()