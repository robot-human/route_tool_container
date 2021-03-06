from math import floor
import requests
import json
from time import sleep
import gpxpy
import os
#from multiprocessing import Pool
#from functools import partial
#import pandas as pd
#sae j1772
#European standard CCS2 with DC port and Type 2 with AC port.

tiles_cache_path = "./tiles_cache/"

base_url = 'https://fleet.ls.hereapi.com'
resource_url = {'get_specific_layer_tile':'/1/tile.json',
                'list_layer_attributes':'/1/doc/layer.json',
                'list_available_layers':'/1/doc/layers.json'}

APP_ID = 'u_mAl_GQlXOPuFueGYLatXGLrJLpgHsMb8QmNKlHwfY'
APP_CODE = 'UUWISlzU8orDegoNz_Y9-Ht0iiHRZKk7jrcRLjMEoSE'

level_layerID_map = {9:1, 10:2, 11:3, 12:4, 13:5}
api_usage_count = 0
INCREMENT_ = 100

road_roughn_cat = {1:"Good",2:"Fair",3:"Poor"}

#This function downloads and stores data from HERE maps api
#   Input: a list of tiles
#   Output: None
def fillCache(tiles: list, session):
    for tile in tiles:
        tileToCache(tile, f'LINK_FC{level_layerID_map[tile[2]]}', tiles_cache_path, session)
        tileToCache(tile, f'LINK_ATTRIBUTE_FC{level_layerID_map[tile[2]]}', tiles_cache_path, session)
        tileToCache(tile, f'LANE_FC{level_layerID_map[tile[2]]}', tiles_cache_path, session)
        tileToCache(tile, f'TRAFFIC_SIGN_FC{level_layerID_map[tile[2]]}', tiles_cache_path, session)
        tileToCache(tile, f'ROAD_GEOM_FC{level_layerID_map[tile[2]]}', tiles_cache_path, session)
        tileToCache(tile, f'EVCHARGING_POI', tiles_cache_path, session)
    return None

#This function is used for access to tile/layer map data, first checks if the tile/layer data is in cache, 
#if not makes the request for the data to HERE maps api
#   Input: tile, layer, directory path, and a session
#   Output: tile/layer map data
def tileToCache(tile:tuple, layer:str, path: str, session:requests.Session=None):
    try:
        cache_file_path = f'{tiles_cache_path}/{layer}-{tile[2]}-{tile[0]}-{tile[1]}.json'           
        with open(cache_file_path) as json_file:
            tile_data = json.load(json_file)
    except:
        print(f"request data from {layer}")
        tile_data = getTileRequest(tile, layer, session)['Rows']
        tileToFile(tile_data, tile, layer, path)
    return tile_data

#This function takes the gps location and the tile level, and finds the tile that contains the gps location
#   Input: gps location and tile level
#   Output: tile coordinates
def coordsToTile(loc: tuple, level: int):
    tileSize = 180.0 / (2**level)
    tiley = floor((loc[0] +  90.0) / tileSize)
    tilex = floor((loc[1] + 180.0) / tileSize)
    tile = (tilex,tiley,level)
    return tile

#This function returns a list of tiles which covers the gps locations
#   Input: gps locations list, start layer level, end layer level
#   Output: a list of tiles coordinates
def getTiles(locations: list, start_level: int, end_level: int):
    tiles = list()
    for level in range(start_level,end_level+1):
        for loc in locations:
            tile = coordsToTile(loc,level)
            if tile not in tiles:
                tiles.append(tile)
    return tiles

#This function increments the count of api calls
#   Input: None
#   Output: None
def incrementApiCount():
    global api_usage_count
    api_usage_count += 1
    return None

#This function makes the HERE maps api request and load to a json file 
#   Input: url, a layer parameter dictionary, and a session 
#   Output: json file    
def getAPIResponse(url:str, params:dict, session: requests.Session=None):
    if not session: session = requests.Session()
    res = session.get(url , params=params)
    sleep(0.05)
    incrementApiCount()
    return json.loads(res.content)
    
#This function takes a tile coordinate list and a desired layer and makes the data request from HERE maps api
#   Input: tile coordinates, a layer name, and a session
#   Output: A HERE maps api response
def getTileRequest(tile:tuple, layer:str, session:requests.Session=None):
    params = {'layer': layer,
              'level': tile[2],
              'tilex': tile[0],
              'tiley': tile[1],
              'apiKey': APP_CODE}
    return getAPIResponse(base_url + resource_url['get_specific_layer_tile'], params=params)

#This function stores the tile/layer data as a json file in memory
#   Input: Here maps data of a tile/layer dictionary, tile coordinates, layer name, and directory path
#   Output: None 
def tileToFile(tileDict:dict, tile:tuple, layer:str, path = tiles_cache_path):
    with open(f'{path}{layer}-{tile[2]}-{tile[0]}-{tile[1]}.json', 'w+') as out_file:
        json.dump(tileDict, out_file)
    out_file.close()
    return None

#This function checks if the tile/layer data is in memory, if not makes the request to HERE maps api
#   Input: tile coordinates, layer name, session
#   Output: the tile/layer data in json format
def checkTileFromCache(tile:tuple, layer:str, session:requests.Session=None):
    try:
        cache_file_path = f'{tiles_cache_path}{layer}-{tile[2]}-{tile[0]}-{tile[1]}.json'           
        with open(cache_file_path) as json_file:
            tile_data = json.load(json_file)
        return tile_data
    except:
        print(f"request data from {layer}-{tile[2]}-{tile[0]}-{tile[1]}.json")
        try:
            tile_data = getTileRequest(tile, layer, session)['Rows']
            tileToFile(tile_data, tile, layer)
            return tile_data
        except:
            print("Empty layer")
            return None

#This function request the lane layer tile data and fills the link attribute dictionary
#   Input: link attributes dictionary, tile coordinate, session
#   Output: link attributes dictionary with lane data 
def requestLaneTile(links_dict: dict, tile: tuple, session: requests.Session=None):
    lane_attributes = checkTileFromCache(tile, f'LANE_FC{level_layerID_map[tile[2]]}', session)
    if(str(lane_attributes) != "None"):
        for attr in lane_attributes:
            try:
                link_id = attr['LINK_ID']
                links_dict[link_id]['LANE_TRAVEL_DIRECTION'] = attr['LANE_TRAVEL_DIRECTION']
        
                if (str(attr['LANE_TYPE']) != 'None'):
                    links_dict[link_id]['LANE_TYPE'] = int(attr['LANE_TYPE'])
                if(str(attr['LANE_DIVIDER_MARKER']) != 'None'):
                    links_dict[link_id]['LANE_DIVIDER_MARKER'] = int(attr['LANE_DIVIDER_MARKER'])
                    links_dict[link_id]['CENTER_DIVIDER_MARKER'] = attr['CENTER_DIVIDER_MARKER']
                if(str(attr['VEHICLE_TYPES']) != 'None'):
                    links_dict[link_id]['VEHICLE_TYPES'] = int(attr['VEHICLE_TYPES'])
                if(str(attr['DIRECTION_CATEGORY']) != 'None'): 
                    links_dict[link_id]['DIRECTION_CATEGORY'] = int(attr['DIRECTION_CATEGORY'])
                if(str(attr['WIDTH']) != 'None'): 
                    links_dict[link_id]['WIDTH'] = float(attr['WIDTH'])
            except:
                print("Lane layer empty")
    return links_dict

#This function request the traffic signs layer tile data and fills the link attribute dictionary
#   Input: link attributes dictionary, tile coordinate, the desired features dictionary, session
#   Output: link attributes dictionary with traffic signs data 
def requestSignsTile(links_dict: dict, tile: tuple, features_query: dict, session: requests.Session=None):
    links_signs_attributes = checkTileFromCache(tile, f'TRAFFIC_SIGN_FC{level_layerID_map[tile[2]]}', session)
    if(str(links_signs_attributes) != "None"):
        for attr in links_signs_attributes:
            try:
                link_ids = attr['LINK_IDS'].split(',')[0]
                if(link_ids[0] in ['-','B']):
                    link_id = link_ids[1:]
                    sign_dir = link_ids[0]
                    if(sign_dir == '-'):
                        sign_dir = 'T' 
                    else:
                        sign_dir = 'B'
                else:
                    link_id = link_ids[0:]
                    sign_dir = 'F'
                if(attr['CONDITION_TYPE'] != None):            
                    if(sign_dir == 'F'):
                        links_dict[link_id]['TRAFFIC_CONDITION_F'].append(int(attr['CONDITION_TYPE']))
                    elif(sign_dir == 'T'):
                        links_dict[link_id]['TRAFFIC_CONDITION_T'].append(int(attr['CONDITION_TYPE']))
                    else:
                        links_dict[link_id]['TRAFFIC_CONDITION_F'].append(int(attr['CONDITION_TYPE']))
                        links_dict[link_id]['TRAFFIC_CONDITION_T'].append(int(attr['CONDITION_TYPE']))                    
                if(attr['TRAFFIC_SIGN_TYPE'] != None):
                    if(sign_dir == 'F'):
                        links_dict[link_id]['TRAFFIC_SIGNS_F'].append(int(attr['TRAFFIC_SIGN_TYPE']))
                    elif(sign_dir == 'T'):
                        links_dict[link_id]['TRAFFIC_SIGNS_T'].append(int(attr['TRAFFIC_SIGN_TYPE']))
                    else:
                        links_dict[link_id]['TRAFFIC_SIGNS_F'].append(int(attr['TRAFFIC_SIGN_TYPE']))
                        links_dict[link_id]['TRAFFIC_SIGNS_T'].append(int(attr['TRAFFIC_SIGN_TYPE']))
                if((sign_dir == 'F') or (sign_dir == 'T')):
                    links_dict[link_id]['WEIGHT'] += setSignsWeight(attr, features_query)
                else:
                    links_dict[link_id]['WEIGHT'] += setSignsWeight(attr, features_query)
            except:
                print("Signs layer empty")
    return links_dict

#This function request the road layer tile data and fills the link attribute dictionary
#   Input: link attributes dictionary, tile coordinate, the desired features dictionary, session
#   Output: link attributes dictionary with road data 
def requestRoadGeomTile(links_dict: dict,  tile: tuple, features_query: dict, session: requests.Session=None):
    road_geom = checkTileFromCache(tile, f'ROAD_GEOM_FC{level_layerID_map[tile[2]]}', session)
    if(str(road_geom) != "None"):
        for geom in road_geom:
            try:
                link_id = geom['LINK_ID']   
                links_dict[link_id]['TUNNEL'] = geom['TUNNEL']
                links_dict[link_id]['BRIDGE'] = geom['BRIDGE']
                links_dict[link_id]['WEIGHT'] += setRoadGeomWeight(geom, features_query)
            except:
                print("Road Geom layer empty")
    return links_dict

#This function request the traffic pattern layer tile data and fills the link attribute dictionary
#   Input: link attributes dictionary, tile coordinate, session
#   Output: link attributes dictionary with traffic pattern data 
def requestTrafficPatternTile(links_dict: dict,  tile: tuple, session: requests.Session=None):
    traffic_pattern = checkTileFromCache(tile, f'TRAFFIC_PATTERN_FC{level_layerID_map[tile[2]]}', session)
    if(str(traffic_pattern) != "None"):
        for pattern in traffic_pattern:
            try:
                link_id = pattern['LINK_ID']   
                links_dict[link_id]['AVG_SPEED'] = float(pattern['FREE_FLOW_SPEED'])
                links_dict[link_id]['AVG_SPEED (Mi/h)'] = 0.621371*float(pattern['FREE_FLOW_SPEED'])
            except:
                print("Traffic Pattern layer empty")
    return links_dict

#This function request the speed limits layer tile data and fills the link attribute dictionary
#   Input: link attributes dictionary, tile coordinate, session
#   Output: link attributes dictionary with speed limits data  
def requestSpeedLimitTile(links_dict: dict,  tile: tuple, features_query: dict, session: requests.Session=None):
    links_speed_limit = checkTileFromCache(tile, f'SPEED_LIMITS_FC{level_layerID_map[tile[2]]}', session)
    if(str(links_speed_limit) != "None"):
        for limit in links_speed_limit:
            try:
                link_id = limit['LINK_ID']
                if(links_dict[link_id]['TRAVEL_DIRECTION'] == 'T'):   
                    links_dict[link_id]['SPEED_LIMIT'] = int(limit['TO_REF_SPEED_LIMIT'])
                    links_dict[link_id]['SPEED_LIMIT (Mi/h)'] = 0.621371*int(limit['TO_REF_SPEED_LIMIT'])
                    links_dict[link_id]['WEIGHT'] += setSpeedWeight(int(limit['TO_REF_SPEED_LIMIT']), features_query)
                else:
                    links_dict[link_id]['SPEED_LIMIT'] = int(limit['FROM_REF_SPEED_LIMIT'])
                    links_dict[link_id]['SPEED_LIMIT (Mi/h)'] = 0.621371*int(limit['FROM_REF_SPEED_LIMIT'])
                    links_dict[link_id]['WEIGHT'] += setSpeedWeight(int(limit['FROM_REF_SPEED_LIMIT']), features_query)
            except:
                print("Speed Limit layer empty")
    return links_dict

def requestSpeedBumpsTile(links_dict: dict,  tile: tuple, session: requests.Session=None):
    links_speed_limit = checkTileFromCache(tile, f'SPEED_LIMITS_COND_FC{level_layerID_map[tile[2]]}', session)
    if(str(links_speed_limit) != "None"):
        for limit in links_speed_limit:
            try:
                link_id = limit['LINK_ID']
                links_dict[link_id]['SPEED_BUMPS'] = int(limit['SPEED_LIMIT_TYPE'])
            except:
                print("Speed Bumps layer empty")
    return links_dict

def requestADASTile(links_dict: dict,  tile: tuple, features_query: dict, session: requests.Session=None):
    links_adas = checkTileFromCache(tile, f'ADAS_ATTRIB_FC{level_layerID_map[tile[2]]}', session)
    if(str(links_adas) != "None"):
        for layer in links_adas:
            try:
                link_id = layer['LINK_ID']
                links_dict[link_id]['HPX'] = layer['HPX']
                links_dict[link_id]['HPY'] = layer['HPY']
                links_dict[link_id]['HPZ'] = layer['HPZ']
            except:
                print("ADAS layer empty")
    return links_dict

def requestRoadRoughnessTile(links_dict: dict,  tile: tuple, features_query: dict, session: requests.Session=None):
    road_layer = checkTileFromCache(tile, f'ROAD_ROUGHNESS_FC{level_layerID_map[tile[2]]}', session)
    if(str(road_layer) != "None"):
        for layer in road_layer:
            try:
                link_id = layer['LINK_ID']
                if(layer['FROM_AVAILABLE_ROUGHN_TYP'] != None):
                    l = layer['FROM_AVAILABLE_ROUGHN_TYP'].split(",")
                    links_dict[link_id]['BUMP_F'] = [int(i) for i in l]
                if(layer['TO_AVAILABLE_ROUGHN_TYP'] != None):
                    l = layer['TO_AVAILABLE_ROUGHN_TYP'].split(",")
                    links_dict[link_id]['BUMP_T'] = [int(i) for i in l]
                if(layer['FROM_AVG_ROUGHN_CAT'] != None):
                    links_dict[link_id]['ROAD_ROUGHNESS_F'] = road_roughn_cat[int(layer['FROM_AVG_ROUGHN_CAT'])]
                if(layer['TO_AVG_ROUGHN_CAT'] != None):
                    links_dict[link_id]['ROAD_ROUGHNESS_T'] = road_roughn_cat[int(layer['TO_AVG_ROUGHN_CAT'])]
            except:
                print("Road Roughness layer empty")
    return links_dict

def requestTollBoothTile(links_dict: dict,  tile: tuple, features_query: dict, session: requests.Session=None):
    toll_layer = checkTileFromCache(tile, f'TOLL_BOOTH_FC{level_layerID_map[tile[2]]}', session)
    if(str(toll_layer) != "None"):
        for layer in toll_layer:
            try:
                link_id = layer['LINK_ID']   
                links_dict[link_id]['TOLL_LOC'] = layer['LAT']+","+layer['LON']
                links_dict[link_id]['TOLL_BOOTH'] = layer['NAME']
            except:
                print("Toll Booth layer empty")
    return links_dict

#This function request the charge stations layer tiles data and fills the link attribute dictionary
#   Input: link attributes dictionary, tile coordinate, session
#   Output: link attributes dictionary with speed limits data   
def getChargingStationsList(tiles: tuple, session): 
    stations_dict ={}
    for tile in tiles:
        stations = checkTileFromCache(tile, f'EVCHARGING_POI', session)
        for s in stations:
            #print(s['NAMES'],s['CONNECTORTYPE'])
            if(str(s['CONNECTORTYPE']) != str(None)):
                string = s['CONNECTORTYPE'].split("                   ")
                if('combo' in string[0]):
                    if(len(string) == 1):
                        alt_string = string[0].split(";")
                        cs_type = alt_string[len(alt_string) - 1]
                    else:
                        cs_type = string[7]
                    if((cs_type == "ChargePoint") or (cs_type == "Electrify America")):
                        stations_dict[s['LINK_ID']] = {'CONNECTORTYPE':s['CONNECTORTYPE'],'SIDE_OF_STREET':s['SIDE_OF_STREET'],'LAT':s['LAT'],'LON':s['LON']}
    return stations_dict

#This function request the link layer and link attributes layer tile data and creates the link attribute dictionary
#   Input: tile coordinate, the desired features dictionary, session
#   Output: link attributes dictionary
def getLinksFromTile(tile: tuple, query: dict, session: requests.Session=None): 
    if not session: session = requests.Session() 
    links = checkTileFromCache(tile, f'LINK_FC{level_layerID_map[tile[2]]}', session)
    links_basic_attributes = checkTileFromCache(tile, f'LINK_ATTRIBUTE_FC{level_layerID_map[tile[2]]}', session)
    
    links_dict = {}
    if(str(links) != "None"):
        for link in links:
            links_dict[link['LINK_ID']] = {'REF_NODE_ID' : link['REF_NODE_ID'],
                                           'NONREF_NODE_ID' : link['NONREF_NODE_ID'],
                                           'LINK_LENGTH' : float(link['LINK_LENGTH']),
                                           'LINK_LENGTH (ft)' : 3.28084*float(link['LINK_LENGTH']),
                                           'LAT': link['LAT'],
                                           'LON': link['LON'],
                                           'WEIGHT': 100*float(link['LINK_LENGTH'])}
    if(str(links_basic_attributes) != "None"):   
        for attr in links_basic_attributes:
            link_id = attr['LINK_ID']
            links_dict[link_id]['BUMP_F'] = []
            links_dict[link_id]['BUMP_T'] = []
            links_dict[link_id]['ROAD_ROUGHNESS_F'] = "Unkown"
            links_dict[link_id]['ROAD_ROUGHNESS_T'] = "Unkown"
            links_dict[link_id]['SPEED_BUMPS'] = None
            links_dict[link_id]['TRAVEL_DIRECTION'] = attr['TRAVEL_DIRECTION']
            links_dict[link_id]['FUNCTIONAL_CLASS'] = int(attr['FUNCTIONAL_CLASS'])
            links_dict[link_id]['RAMP'] = setAttribute(query['attr_features']['RAMP'], attr['RAMP'])
            links_dict[link_id]['PAVED'] = setAttribute(query['attr_features']['PAVED'], attr['PAVED'])
            links_dict[link_id]['LIMITED_ACCESS_ROAD'] = setAttribute(query['attr_features']['LIMITED_ACCESS_ROAD'], attr['LIMITED_ACCESS_ROAD'])
            links_dict[link_id]['URBAN'] = setAttribute(query['attr_features']['URBAN'], attr['URBAN']) 
            links_dict[link_id]['INTERSECTION'] = None
            if(attr['INTERSECTION_CATEGORY'] != None): 
                if(int(attr['INTERSECTION_CATEGORY']) == 2): 
                    links_dict[link_id]['INTERSECTION'] = int(attr['INTERSECTION_CATEGORY'])
                if(int(attr['INTERSECTION_CATEGORY']) == 4): 
                    #if(-4 not in query['attr_features']['INTERSECTION_CATEGORY']):
                    links_dict[link_id]['INTERSECTION'] = int(attr['INTERSECTION_CATEGORY'])

            links_dict[link_id]['VEHICLE_TYPES'] = attr['VEHICLE_TYPES']
            links_dict[link_id]['SPEED_CATEGORY'] = int(attr['SPEED_CATEGORY'])
            links_dict[link_id]['LANE_CATEGORY'] = int(attr['LANE_CATEGORY'])
            links_dict[link_id]['PHYSICAL_NUM_LANES'] = attr['PHYSICAL_NUM_LANES']
            links_dict[link_id]['OVERPASS_UNDERPASS'] = attr['OVERPASS_UNDERPASS']

            links_dict[link_id]['HPX'] = None
            links_dict[link_id]['HPY'] = None
            links_dict[link_id]['HPZ'] = None

            links_dict[link_id]['SPEED_LIMIT'] = None   
            links_dict[link_id]['SPEED_LIMIT (Mi/h)'] = None        
            links_dict[link_id]['LANE_TYPE'] = None
            links_dict[link_id]['LANE_DIVIDER_MARKER'] = 14
            links_dict[link_id]['VEHICLE_TYPES'] = None
            links_dict[link_id]['DIRECTION_CATEGORY'] = None
            links_dict[link_id]['WIDTH'] = None
        
            links_dict[link_id]['TRAFFIC_CONDITION_F'] = []
            links_dict[link_id]['TRAFFIC_CONDITION_T'] = []
            links_dict[link_id]['TRAFFIC_SIGNS_F'] = []
            links_dict[link_id]['TRAFFIC_SIGNS_T'] = []
            links_dict[link_id]['TUNNEL'] = None
            links_dict[link_id]['BRIDGE'] = None
            links_dict[link_id]['TOLL_BOOTH'] = None
            links_dict[link_id]['TOLL_LOC'] = None
            links_dict[link_id]['AVG_SPEED'] = 80
            links_dict[link_id]['AVG_SPEED (Mi/h)'] = 0.621371*80
            links_dict[link_id]['WEIGHT'] += setAttrWeight(attr, query['attr_features'])
        
        
    links_dict = requestADASTile(links_dict, tile, session)
    links_dict = requestLaneTile(links_dict, tile, session)
    links_dict = requestSignsTile(links_dict, tile, query['sign_features'], session)
    links_dict = requestSpeedLimitTile(links_dict, tile, query['speed_features'], session)
    links_dict = requestSpeedBumpsTile(links_dict, tile, session)
    links_dict = requestRoadGeomTile(links_dict, tile, query['geom_features'], session)
    links_dict = requestRoadRoughnessTile(links_dict, tile, query['geom_features'], session)
    links_dict = requestTrafficPatternTile(links_dict, tile, session)
    links_dict = requestTollBoothTile(links_dict, tile, session)
    links_dict = setWeights(links_dict,query)
    return links_dict

def setWeights(links_dict,query):
    for link_id in links_dict:
        links_dict[link_id]['WEIGHT'] += setRoadGeomWeight(links_dict[link_id], query['geom_features'], increment = INCREMENT_)
    return links_dict
    
def setAttribute(query, attr):
    if('S' in query):
        return attr
    else:
        return None
    
#This function assigns a weight value for each link based on the desired link attributes features
#   Input: the link attributes dictionary, the desired features dictionary, a weight increment
#   Output: weight value
def setAttrWeight(attributes: dict, features_query: dict, increment = INCREMENT_):
    weight = 0
    if((int(attributes['FUNCTIONAL_CLASS']) not in features_query['FUNCTIONAL_CLASS']) and (int(attributes['SPEED_CATEGORY']) not in features_query['SPEED_CATEGORY'])):
        weight += increment
    if(str(attributes['TRAVEL_DIRECTION']) not in features_query['TRAVEL_DIRECTION']):
        weight += increment
    if(str(attributes['URBAN']) not in  features_query['URBAN']):
        weight += increment
    if(('S' in features_query['LIMITED_ACCESS_ROAD']) and (str(attributes['LIMITED_ACCESS_ROAD']) not in features_query['LIMITED_ACCESS_ROAD'])):
        weight += increment  
    if(('S' in features_query['PAVED']) and (str(attributes['PAVED']) not in  features_query['PAVED'])):
        weight += increment
    if(('S' in features_query['RAMP']) and (str(attributes['RAMP']) not in  features_query['RAMP'])):
        weight += increment
    if(attributes['INTERSECTION_CATEGORY'] != None):
        if(int(attributes['INTERSECTION_CATEGORY']) not in features_query['INTERSECTION_CATEGORY']):
            weight += increment
    if(int(attributes['LANE_CATEGORY']) not in features_query['LANE_CATEGORY']):
        weight += increment
    if(attributes['OVERPASS_UNDERPASS'] != None):
        if(int(attributes['OVERPASS_UNDERPASS']) not in features_query['OVERPASS_UNDERPASS']):
            weight += increment
    return weight
 
#This function assigns a weight value for each link based on the desired traffic signs features
#   Input: the link attributes dictionary, the desired features dictionary, a weight increment
#   Output: weight value 
def setSignsWeight(attributes: dict, features_query: dict, increment = 0):
    weight = 0    
    if(features_query['display_condition']): 
        if(attributes['CONDITION_TYPE'] == None):
            weight += increment
        else:
            if(int(attributes['CONDITION_TYPE']) not in features_query['CONDITION_TYPE']):
                weight += increment
    if(features_query['display_signs']):
        if(attributes['TRAFFIC_SIGN_TYPE'] == None):
            weight += increment
        else:
            if(int(attributes['TRAFFIC_SIGN_TYPE']) not in features_query['SIGN_TYPE']):
                weight += increment
    return weight
    
#This function assigns a weight value for each link based on the desired traffic signs features
#   Input: the link attributes dictionary, the desired features dictionary, a weight increment
#   Output: weight value 
def setRoadGeomWeight(attributes: dict, features_query: dict, increment = INCREMENT_):
    weight = 0    
    if(('S' in features_query['TUNNEL']) and (attributes['TUNNEL'] != None)):
        if(attributes['TUNNEL'] == 'N'):
            weight += increment
    if(attributes['BRIDGE'] != None):
        if(attributes['BRIDGE'] not in features_query['BRIDGE']):
            weight += increment
    return weight
    
def setSpeedWeight(speed_lim: int, features_query: dict, increment = INCREMENT_):
    weight = 0    
    if((features_query['boolean_speed_min'])):
        if(speed_lim < int(features_query['SPEED_MIN'])):
            weight += increment*2
    if((features_query['boolean_speed_max'])):
        if(speed_lim > int(features_query['SPEED_MAX'])):
            weight += increment*2
    return weight

