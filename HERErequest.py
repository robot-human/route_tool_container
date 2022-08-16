from math import floor
import requests
import json
from time import sleep
import gpxpy
import os
from multiprocessing import Pool
from functools import partial

tiles_cache_path = "./tiles_cache/"

base_url = 'https://fleet.ls.hereapi.com'
resource_url = {'get_specific_layer_tile':'/1/tile.json',
                'list_layer_attributes':'/1/doc/layer.json',
                'list_available_layers':'/1/doc/layers.json'}

#APP_CODE = 'jKvhe5N2sdc8kPOU0Bqw_CBEgtX2LSjds5CCTCE67q4'
APP_CODE ='vGeMc2D8lMqb5OY39enKrjNjrEMWlOabRS2olRxc2a0'

level_layerID_map = {9:1, 10:2, 11:3, 12:4, 13:5}
api_usage_count = 0
PERCENTAGE_ = 0.3
kms_to_miles=1
mts_to_fts = 1
road_roughn_cat = {1:"Good",2:"Fair",3:"Poor"}

def fillCache(tiles: list, session):
    print("start filling cache")
    for tile in tiles:
        checkTileFromCache(tile, f'LINK_FC{level_layerID_map[tile[2]]}', session)
        checkTileFromCache(tile, f'LINK_ATTRIBUTE_FC{level_layerID_map[tile[2]]}', session)
        checkTileFromCache(tile, f'LANE_FC{level_layerID_map[tile[2]]}', session)
        checkTileFromCache(tile, f'TRAFFIC_SIGN_FC{level_layerID_map[tile[2]]}', session)
        checkTileFromCache(tile, f'ROAD_GEOM_FC{level_layerID_map[tile[2]]}', session)
        checkTileFromCache(tile, f'EVCHARGING_POI', session)
        checkTileFromCache(tile, f'ROAD_ROUGHNESS_FC{level_layerID_map[tile[2]]}', session)
        checkTileFromCache(tile, f'SPEED_LIMITS_FC{level_layerID_map[tile[2]]}', session)
        checkTileFromCache(tile, f'SPEED_LIMITS_COND_FC{level_layerID_map[tile[2]]}', session)
        checkTileFromCache(tile, f'TOLL_BOOTH_FC{level_layerID_map[tile[2]]}', session)
        checkTileFromCache(tile, f'TRAFFIC_PATTERN_FC{level_layerID_map[tile[2]]}', session)
    return None

def tileToCache(tile:tuple, layer:str, path: str, session:requests.Session=None):
    try:
        cache_file_path = f'{tiles_cache_path}/{layer}-{tile[2]}-{tile[0]}-{tile[1]}.json'           
        if(os.stat(cache_file_path).st_size > 0):
            with open(cache_file_path) as json_file:
                tile_data = json.load(json_file)
        else:
            print("empty layer file")
            os.remove(cache_file_path)
            print(f"request data from {layer}")
            tile_data = getTileRequest(tile, layer, session)['Rows']
            tileToFile(tile_data, tile, layer, path)
    except:
        print(f"request data from {layer}")
        tile_data = getTileRequest(tile, layer, session)['Rows']
        tileToFile(tile_data, tile, layer, path)
    return tile_data

def coordsToTile(loc: tuple, level: int):
    tileSize = 180.0 / (2**level)
    tiley = floor((loc[0] +  90.0) / tileSize)
    tilex = floor((loc[1] + 180.0) / tileSize)
    tile = (tilex,tiley,level)
    return tile

def getTiles(locations: list, start_level: int, end_level: int):
    tiles = list()
    for level in range(start_level,end_level+1):
        for loc in locations:
            tile = coordsToTile(loc,level)
            if tile not in tiles:
                tiles.append(tile)
    return tiles

def incrementApiCount():
    global api_usage_count
    api_usage_count += 1
    return None

def getAPIResponse(url:str, params:dict, session: requests.Session=None):
    if not session: session = requests.Session()
    res = session.get(url , params=params)
    sleep(0.05)
    incrementApiCount()
    return json.loads(res.content)
    
def getTileRequest(tile:tuple, layer:str, session:requests.Session=None):
    params = {'layer': layer,
              'level': tile[2],
              'tilex': tile[0],
              'tiley': tile[1],
              'apiKey': APP_CODE}
    return getAPIResponse(base_url + resource_url['get_specific_layer_tile'], params=params)

def tileToFile(tileDict:dict, tile:tuple, layer:str, path = tiles_cache_path):
    with open(f'{path}{layer}-{tile[2]}-{tile[0]}-{tile[1]}.json', 'w+') as out_file:
        json.dump(tileDict, out_file)
    out_file.close()
    return None

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

def getLinksFromTile(tile: tuple, cfg: dict, session: requests.Session=None): 
    not_navigable = []
    if not session: session = requests.Session() 
    links = checkTileFromCache(tile, f'LINK_FC{level_layerID_map[tile[2]]}', session)
    links_basic_attributes = checkTileFromCache(tile, f'LINK_ATTRIBUTE_FC{level_layerID_map[tile[2]]}', session)
    links_dict = {}
    wMax=0
    wMin=500
    if(str(links) != "None"):
        for link in links:
            links_dict[link['LINK_ID']] = {'REF_NODE_ID' : link['REF_NODE_ID'],
                                           'NONREF_NODE_ID' : link['NONREF_NODE_ID'],
                                           'LINK_LENGTH' : float(link['LINK_LENGTH']),
                                           'LAT': link['LAT'],
                                           'LON': link['LON'],
                                           'WEIGHT': 100*float(link['LINK_LENGTH']),
                                           'N_ATTRIBUTES': 0}
    if(str(links_basic_attributes) != "None"):   
        for attr in links_basic_attributes:
            links_dict,not_navigable = fillDictionary(links_dict, attr, cfg, not_navigable)
            
    links_dict,not_navigable = requestAttributesTile(links_dict, tile, cfg['query_features'], not_navigable, session)
    links_dict = requestTrafficPatternTile(links_dict, tile, session)
    links_dict = requestSpeedLimitTile(links_dict, tile, session)
    links_dict = requestSignsTile(links_dict, tile, cfg['query_features']['sign_features'], session)
    links_dict = requestRoadRoughnessTile(links_dict, tile, cfg['query_features'], session)
    links_dict = requestSpeedBumpsTile(links_dict, tile, cfg['query_features'], session)
    links_dict = requestTollBoothTile(links_dict, tile, cfg['query_features'], session)
    links_dict = requestLaneTile(links_dict, tile, cfg['query_features'], session)
    links_dict = requestAdasTile(links_dict, tile, session)
    links_dict = requestRoadAdminTile(links_dict, tile, session)
    links_dict = requestRoadGeomTile(links_dict, tile, cfg, session)
    setRoadTypes(links_dict, cfg)
     
    for link in not_navigable:
        try:
            del links_dict[link]
        except:
            continue
    return links_dict

def fillDictionary(links_dict, attr, query, not_navigable):
    link_id = attr['LINK_ID']
    if(link_id in links_dict):
        links_dict[link_id]['ATTR_COUNT'] = 0
        links_dict[link_id]['TRAVEL_DIRECTION'] = attr['TRAVEL_DIRECTION']
        links_dict[link_id]['VEHICLE_TYPES'] = attr['VEHICLE_TYPES']
        if((int(links_dict[link_id]['VEHICLE_TYPES'])%2 != 1) or (attr['PUBLIC_ACCESS'] == 'N') or (attr['PRIVATE'] == 'Y')):
            not_navigable.append(link_id)
        links_dict[link_id]['FUNCTIONAL_CLASS'] = int(attr['FUNCTIONAL_CLASS'])

        links_dict[link_id]['URBAN'] = attr['URBAN']
        links_dict[link_id]['LOW_MOBILITY'] = int(attr['LOW_MOBILITY'])
        links_dict[link_id]['LIMITED_ACCESS_ROAD'] = attr['LIMITED_ACCESS_ROAD']
        links_dict[link_id]['PAVED'] = attr['PAVED']
        links_dict[link_id]['RAMP'] = attr['RAMP']
        links_dict[link_id]['INTERSECTION'] = None
        if(attr['INTERSECTION_CATEGORY'] != None): 
            if(int(attr['INTERSECTION_CATEGORY']) == 2): 
                links_dict[link_id]['INTERSECTION'] = int(attr['INTERSECTION_CATEGORY'])
            if(int(attr['INTERSECTION_CATEGORY']) == 4): 
                links_dict[link_id]['INTERSECTION'] = int(attr['INTERSECTION_CATEGORY'])
        links_dict[link_id]['LANE_CATEGORY'] = int(attr['LANE_CATEGORY'])
        links_dict[link_id]['SPEED_CATEGORY'] = int(attr['SPEED_CATEGORY'])
        if((int(attr['FUNCTIONAL_CLASS']) == 5) or ((str(query['query_features']['boolean_features']['ramp']) == '0') and (attr['RAMP'] == 'Y')) or ((str(query['query_features']['boolean_features']['urban']) == '0') and (attr['URBAN'] == 'Y'))):
            links_dict[link_id]['WEIGHT'] *= 1.1
        if((str(query['query_features']['boolean_features']['not_paved']) == '0') and (attr['PAVED'] == 'N')):
            links_dict[link_id]['WEIGHT'] *= 10
        links_dict[link_id]['PARKING_LOT_ROAD'] = None
        links_dict[link_id]['SURFACE_TYPE'] = None

        links_dict[link_id]['AVG_SPEED'] = 80
        links_dict[link_id]['SPEED_LIMIT'] = None
        setAttrWeight(links_dict[link_id], attr, query['query_features'])

        links_dict[link_id]['STREET_NAME'] = None
        
        links_dict[link_id]['COUNTRY'] = None
        links_dict[link_id]['BUILTUP'] = None

        links_dict[link_id]['HIGHWAY'] = None
        links_dict[link_id]['CITY'] = None
        links_dict[link_id]['RURAL'] = None

        links_dict[link_id]['TRAFFIC_CONDITION_F'] = []
        links_dict[link_id]['TRAFFIC_CONDITION_T'] = []
        links_dict[link_id]['TRAFFIC_SIGNS_F'] = []
        links_dict[link_id]['TRAFFIC_SIGNS_T'] = []

        links_dict[link_id]['TUNNEL'] = None
        links_dict[link_id]['BRIDGE'] = None

        links_dict[link_id]['ROAD_ROUGHNESS_F'] = "Unkown"
        links_dict[link_id]['ROAD_ROUGHNESS_T'] = "Unkown"

        links_dict[link_id]['SPEED_BUMPS'] = 0

        links_dict[link_id]['TOLL_BOOTH'] = None
        links_dict[link_id]['TOLL_LOC'] = None

        links_dict[link_id]['LANE_TYPE'] = None
        links_dict[link_id]['LANE_DIVIDER_MARKER'] = 14
        links_dict[link_id]['WIDTH'] = None
        links_dict[link_id]['HPX'] = []
        links_dict[link_id]['HPY'] = []
    return links_dict, not_navigable

def setAttrWeight(links_dict, attributes: dict, features_query: dict, percentage = PERCENTAGE_):
    if(features_query['boolean_features']['oneway']):
        if((str(attributes['TRAVEL_DIRECTION']) == 'F') or (str(attributes['TRAVEL_DIRECTION']) == 'T')):
            links_dict['WEIGHT'] *= percentage
            links_dict['N_ATTRIBUTES'] += 1
    if(features_query['boolean_features']['both_ways']):
        if(str(attributes['TRAVEL_DIRECTION']) == 'B'):
            links_dict['WEIGHT'] *= percentage
            links_dict['N_ATTRIBUTES'] += 1
    if(features_query['boolean_features']['limited_access']):
        if(attributes['LIMITED_ACCESS_ROAD'] == 'Y'):
            links_dict['WEIGHT'] *= percentage
            links_dict['N_ATTRIBUTES'] += 1
    if(features_query['boolean_features']['not_paved']):
        if(attributes['PAVED'] == 'N'):
            links_dict['WEIGHT'] *= percentage
            links_dict['N_ATTRIBUTES'] += 1
    if(features_query['boolean_features']['ramp']):
        if(attributes['RAMP']=='Y'):
            links_dict['WEIGHT'] *= percentage
            links_dict['N_ATTRIBUTES'] += 1
    if(features_query['boolean_features']['manoeuvre']):
        if(str(attributes['INTERSECTION_CATEGORY']) == '2'):
            links_dict['WEIGHT'] *= percentage
            links_dict['N_ATTRIBUTES'] += 1
    if(features_query['boolean_features']['roundabout']):
        if(str(attributes['INTERSECTION_CATEGORY']) == '4'):
            links_dict['WEIGHT'] *= percentage
            links_dict['N_ATTRIBUTES'] += 1
    if(features_query['boolean_features']['one_lane']):
        if(int(attributes['LANE_CATEGORY']) == 1):
            links_dict['WEIGHT'] *= percentage
            links_dict['N_ATTRIBUTES'] += 1
    if(features_query['boolean_features']['multiple_lanes']):
        if(int(attributes['LANE_CATEGORY']) > 1):
            links_dict['WEIGHT'] *= percentage
            links_dict['N_ATTRIBUTES'] += 1
    if(features_query['boolean_features']['speed_category']):
        if(int(attributes['SPEED_CATEGORY']) in features_query['attr_features']['SPEED_CAT']):
            links_dict['WEIGHT'] *= percentage
            links_dict['N_ATTRIBUTES'] += 1
    return None

def requestAttributesTile(links_dict: dict,  tile: tuple, features_query, not_navigable, session: requests.Session=None):
    attributes = checkTileFromCache(tile, f'LINK_ATTRIBUTE2_FC{level_layerID_map[tile[2]]}', session)
    if(str(attributes) != "None"):
        for attr in attributes:
            try:
                link_id = attr['LINK_ID']   
                links_dict[link_id]['PARKING_LOT_ROAD'] = attr['PARKING_LOT_ROAD']
                links_dict[link_id]['SURFACE_TYPE'] = attr['SURFACE_TYPE']
                if(str(features_query['boolean_features']['parking_lot']) == '0'):
                    if(attr['PARKING_LOT_ROAD'] == 'Y'):
                        not_navigable.append(link_id)
                setAttr2Weight(links_dict[link_id], attr, features_query)
            except:
                continue
    return links_dict, not_navigable

def setAttr2Weight(links_dict, attributes: dict, features_query: dict, percentage = PERCENTAGE_):
    if(features_query['boolean_features']['parking_lot']):
        if(attributes['PARKING_LOT_ROAD'] == 'Y'):
            links_dict['WEIGHT'] *= percentage
            links_dict['N_ATTRIBUTES'] += 1
    return None

def requestTrafficPatternTile(links_dict: dict,  tile: tuple, session: requests.Session=None):
    traffic_pattern = checkTileFromCache(tile, f'TRAFFIC_PATTERN_FC{level_layerID_map[tile[2]]}', session)
    if(str(traffic_pattern) != "None"):
        for pattern in traffic_pattern:
            try:
                link_id = pattern['LINK_ID']   
                links_dict[link_id]['AVG_SPEED'] = float(pattern['FREE_FLOW_SPEED'])
            except:
                continue
    return links_dict

def requestSpeedLimitTile(links_dict: dict,  tile: tuple, session: requests.Session=None):
    links_speed_limit = checkTileFromCache(tile, f'SPEED_LIMITS_FC{level_layerID_map[tile[2]]}', session)
    if(str(links_speed_limit) != "None"):
        for limit in links_speed_limit:
            try:
                link_id = limit['LINK_ID']
                if(links_dict[link_id]['TRAVEL_DIRECTION'] == 'T'):   
                    links_dict[link_id]['SPEED_LIMIT'] = int(limit['TO_REF_SPEED_LIMIT'])
                else:
                    links_dict[link_id]['SPEED_LIMIT'] = int(limit['FROM_REF_SPEED_LIMIT'])
            except:
                continue
    return links_dict

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
                setSignsWeight(links_dict[link_id], attr, features_query)
            except:
                continue
    return links_dict

def setSignsWeight(links_dict, attributes: dict, features_query: dict, percentage = PERCENTAGE_):
    if(attributes['CONDITION_TYPE'] != None):
        if(int(attributes['CONDITION_TYPE']) in features_query['CONDITION_TYPE']):
            links_dict['WEIGHT'] *= percentage
            links_dict['N_ATTRIBUTES'] += 1
    if(attributes['TRAFFIC_SIGN_TYPE'] != None):
        if(int(attributes['TRAFFIC_SIGN_TYPE']) in features_query['SIGN_TYPE']):
            links_dict['WEIGHT'] *= percentage
            links_dict['N_ATTRIBUTES'] += 1
    return None

def requestRoadAdminTile(links_dict: dict,  tile: tuple, session: requests.Session=None):
    road_geom = checkTileFromCache(tile, f'ROAD_ADMIN_NAMES_FC{level_layerID_map[tile[2]]}', session)
    if(str(road_geom) != "None"):
        for layer in road_geom:
            try:
                link_id = layer['LINK_ID']
                if((layer['COUNTRY_NAMES'].find('Deutschland') < 0) and (layer['COUNTRY_NAMES'].find('Nederland') < 0) and (layer['COUNTRY_NAMES'].find('Belgique') < 0)):
                    print(layer['COUNTRY_NAMES'], layer['COUNTRY_NAMES'].find('Deutschland'))
                links_dict[link_id]['COUNTRY'] = layer['COUNTRY_NAMES']
                if(layer['BUILTUP_NAMES'] != None):
                    builtup = layer['BUILTUP_NAMES'][5:]
                    if(builtup.find("BN") > 0):
                        builtup = builtup[:builtup.find("BN")-3]
                else:
                    builtup = None
                links_dict[link_id]['BUILTUP'] = builtup
            except:
                continue
    return links_dict

def requestRoadRoughnessTile(links_dict: dict,  tile: tuple, features_query: dict, session: requests.Session=None):
    road_layer = checkTileFromCache(tile, f'ROAD_ROUGHNESS_FC{level_layerID_map[tile[2]]}', session)
    if(str(road_layer) != "None"):
        for layer in road_layer:
            try:
                link_id = layer['LINK_ID']
                if(layer['FROM_AVG_ROUGHN_CAT'] != None):
                    links_dict[link_id]['ROAD_ROUGHNESS_F'] = road_roughn_cat[int(layer['FROM_AVG_ROUGHN_CAT'])]
                if(layer['TO_AVG_ROUGHN_CAT'] != None):
                    links_dict[link_id]['ROAD_ROUGHNESS_T'] = road_roughn_cat[int(layer['TO_AVG_ROUGHN_CAT'])]
                setRoadRoughnessWeight(links_dict[link_id], layer, features_query)
            except:
                continue
    return links_dict

def setRoadRoughnessWeight(links_dict, attributes: dict, features_query: dict, percentage = PERCENTAGE_):
    if(features_query['boolean_features']['road_roughness_good']): 
        if((1 in attributes['ROAD_ROUGHNESS_T']) or (1 in attributes['ROAD_ROUGHNESS_F'])):
            links_dict['WEIGHT'] *= percentage
            links_dict['N_ATTRIBUTES'] += 1
    if(features_query['boolean_features']['road_roughness_fair']): 
        if((2 in attributes['ROAD_ROUGHNESS_T']) or (2 in attributes['ROAD_ROUGHNESS_F'])):
            links_dict['WEIGHT'] *= percentage
            links_dict['N_ATTRIBUTES'] += 1
    if(features_query['boolean_features']['road_roughness_poor']): 
        if((3 in attributes['ROAD_ROUGHNESS_T']) or (3 in attributes['ROAD_ROUGHNESS_F'])):
            links_dict['WEIGHT'] *= percentage
            links_dict['N_ATTRIBUTES'] += 1
    return None

def requestSpeedBumpsTile(links_dict: dict,  tile: tuple, features_query: dict, session: requests.Session=None):
    links_speed_limit = checkTileFromCache(tile, f'SPEED_LIMITS_COND_FC{level_layerID_map[tile[2]]}', session)
    if(str(links_speed_limit) != "None"):
        for limit in links_speed_limit:
            try:
                link_id = limit['LINK_ID']
                links_dict[link_id]['SPEED_BUMPS'] = int(limit['SPEED_LIMIT_TYPE'])
                setSpeedBumpsWeight(links_dict[link_id], limit, features_query)
            except:
                continue
    return links_dict

def setSpeedBumpsWeight(links_dict, attributes: dict, features_query: dict, percentage = PERCENTAGE_):
    if(features_query['boolean_features']['speed_bumps']): 
        if(int(attributes['SPEED_LIMIT_TYPE']) == 3):
            links_dict['WEIGHT'] *= percentage
            links_dict['N_ATTRIBUTES'] += 1
    return None

def requestTollBoothTile(links_dict: dict,  tile: tuple, features_query: dict, session: requests.Session=None):
    toll_layer = checkTileFromCache(tile, f'TOLL_BOOTH_FC{level_layerID_map[tile[2]]}', session)
    if(toll_layer != None):
        for layer in toll_layer:
            try:
                link_ids = layer['LINK_IDS'].split(",")
                if(len(link_ids) == 2):
                    link_1 = link_ids[0]
                    link_2 = link_ids[1]
                    if(link_1.find('-') == 0):
                        link_id_1 = link_1[1:]
                    else:
                        link_id_1 = link_1
                    if(link_2.find('-') == 0):
                        link_id_2 = link_2[1:]
                    else:
                        link_id_2 = link_2
                    links_dict[link_id_1]['TOLL_LOC'] = str(int(layer['LAT'])/100000)+","+str(int(layer['LON'])/100000)
                    links_dict[link_id_2]['TOLL_LOC'] = str(int(layer['LAT'])/100000)+","+str(int(layer['LON'])/100000)
                    links_dict[link_id_1]['TOLL_BOOTH'] = layer['NAME']
                    links_dict[link_id_2]['TOLL_BOOTH'] = layer['NAME']
                    setTollBoothWeight(links_dict[link_id_1], layer, features_query)
                    setTollBoothWeight(links_dict[link_id_2], layer, features_query)
                elif(len(link_ids) == 1):
                    link_1 = link_ids[0]
                    if(link_1.find('-') == 0):
                        link_id_1 = link_1[1:]
                    else:
                        link_id_1 = link_1
                    links_dict[link_id_1]['TOLL_LOC'] = str(int(layer['LAT'])/100000)+","+str(int(layer['LON'])/100000)
                    links_dict[link_id_1]['TOLL_BOOTH'] = layer['NAME']
                    setTollBoothWeight(links_dict[link_id_1], layer, features_query)
            except:
                continue
    return links_dict

def setTollBoothWeight(links_dict, attributes: dict, features_query: dict, percentage = PERCENTAGE_):
    if(features_query['boolean_features']['toll_booth']): 
        if(attributes['NAME'] != None):
            links_dict['WEIGHT'] *= percentage
            links_dict['N_ATTRIBUTES'] += 1
    return None

def requestLaneTile(links_dict: dict, tile: tuple, features_query: dict, session: requests.Session=None):
    lane_attributes = checkTileFromCache(tile, f'LANE_FC{level_layerID_map[tile[2]]}', session)
    if(str(lane_attributes) != "None"):
        for attr in lane_attributes:
            try:
                link_id = attr['LINK_ID']
                links_dict[link_id]['LANE_TRAVEL_DIRECTION'] = attr['LANE_TRAVEL_DIRECTION']
                if(str(attr['LANE_TYPE']) != 'None'):
                    links_dict[link_id]['LANE_TYPE'] = int(attr['LANE_TYPE'])
                if(str(attr['LANE_DIVIDER_MARKER']) != 'None'):
                    links_dict[link_id]['LANE_DIVIDER_MARKER'] = int(attr['LANE_DIVIDER_MARKER'])
                if(str(attr['WIDTH']) != 'None'): 
                    links_dict[link_id]['WIDTH'] = float(attr['WIDTH'])
                setLanesWeight(links_dict[link_id], attr, features_query)
            except:
                continue
    return links_dict

def setLanesWeight(links_dict, attributes: dict, features_query: dict, percentage = PERCENTAGE_):
    if(features_query['boolean_features']['lane_markers_bool']): 
        if(int(attributes['LANE_DIVIDER_MARKER']) in features_query['lane_features']['lane_markers']):
            links_dict['WEIGHT'] *= percentage
            links_dict['N_ATTRIBUTES'] += 1
    if(features_query['boolean_features']['lane_type_bool']): 
        if(int(attributes['LANE_TYPE']) in features_query['lane_features']['lane_markers']):
            links_dict['WEIGHT'] *= percentage
            links_dict['N_ATTRIBUTES'] += 1
    return None

def getChargingStationsList(tiles: tuple, session): 
    stations_dict ={}
    filt=False
    for tile in tiles:
        stations = checkTileFromCache(tile, f'EVCHARGING_POI', session)
        try:
            for s in stations:
                if(str(s['CONNECTORTYPE']) != str(None)):
                    if(filt==False):
                        stations_dict[s['LINK_ID']] = {'CONNECTORTYPE':s['CONNECTORTYPE'],'SIDE_OF_STREET':s['SIDE_OF_STREET'],'LAT':s['LAT'],'LON':s['LON']}
                    else:
                        string = s['CONNECTORTYPE'].split("                   ")
                        if('combo' in string[0]):
                            if(len(string) == 1):
                                alt_string = string[0].split(";")
                                cs_type = alt_string[len(alt_string) - 1]
                            else:
                                cs_type = string[7]
                            if((cs_type == "ChargePoint") or (cs_type == "Electrify America")):
                                stations_dict[s['LINK_ID']] = {'CONNECTORTYPE':s['CONNECTORTYPE'],'SIDE_OF_STREET':s['SIDE_OF_STREET'],'LAT':s['LAT'],'LON':s['LON']}
        except:
            continue
    return stations_dict

def requestAdasTile(links_dict: dict, tile: tuple, session: requests.Session=None):
    adas_attributes = checkTileFromCache(tile, f'ADAS_ATTRIB_FC{level_layerID_map[tile[2]]}', session)#
    if(str(adas_attributes) != "None"):
        for attr in adas_attributes:
            try:
                link_id = attr['LINK_ID']
                links_dict[link_id]['HPX'] = attr['HPX'].split(",")
                links_dict[link_id]['HPY'] = attr['HPY'].split(",")   
            except:
                continue
    return links_dict

def requestRoadGeomTile(links_dict: dict,  tile: tuple, cfg: dict, session: requests.Session=None):
    road_geom = checkTileFromCache(tile, f'ROAD_GEOM_FC{level_layerID_map[tile[2]]}', session)
    if(str(road_geom) != "None"):
        for geom in road_geom:
            try:
                link_id = geom['LINK_ID']   
                links_dict[link_id]['STREET_NAME'] = geom['NAME']
                links_dict[link_id]['TUNNEL'] = geom['TUNNEL']
                links_dict[link_id]['BRIDGE'] = geom['BRIDGE']
                if(geom['NAME'] != None):
                    if(links_dict[link_id]['COUNTRY'].find('Deutschland') >= 0):
                        if((geom['NAME'].find("A") == 0) and (int(geom['NAME'][1]) in [0,1,2,3,4,5,6,7,8,9])):
                            links_dict[link_id]['HIGHWAY'] = 'Y'
                            links_dict[link_id]['CITY'] = 'N'
                            links_dict[link_id]['RURAL'] = 'N'
                        elif((geom['NAME'].find("B") == 0) and (int(geom['NAME'][1]) in [0,1,2,3,4,5,6,7,8,9])):
                            links_dict[link_id]['HIGHWAY'] = 'N'
                            links_dict[link_id]['CITY'] = 'Y'
                            links_dict[link_id]['RURAL'] = 'N'
                        elif((geom['NAME'].find("L") == 0) and (int(geom['NAME'][1]) in [0,1,2,3,4,5,6,7,8,9])):
                            links_dict[link_id]['HIGHWAY'] = 'N'
                            links_dict[link_id]['CITY'] = 'N'
                            links_dict[link_id]['RURAL'] = 'Y'
                        else:
                            links_dict[link_id]['HIGHWAY'] = 'N'
                            links_dict[link_id]['CITY'] = 'Y'
                            links_dict[link_id]['RURAL'] = 'N'

                    elif((links_dict[link_id]['COUNTRY'].find('Nederland') >= 0) or (links_dict[link_id]['COUNTRY'].find('Belgique') >= 0)):
                        if((geom['NAME'][0] in ['A','E']) and (int(geom['NAME'][1]) in [0,1,2,3,4,5,6,7,8,9])):
                            links_dict[link_id]['HIGHWAY'] = 'Y'
                            links_dict[link_id]['CITY'] = 'N'
                            links_dict[link_id]['RURAL'] = 'N'
                        elif((geom['NAME'][0] in ['N']) and (int(geom['NAME'][1]) in [0,1,2,3,4,5,6,7,8,9])):
                            links_dict[link_id]['HIGHWAY'] = 'N'
                            links_dict[link_id]['CITY'] = 'Y'
                            links_dict[link_id]['RURAL'] = 'N'
                        else:
                            links_dict[link_id]['HIGHWAY'] = 'N'
                            links_dict[link_id]['CITY'] = 'Y'
                            links_dict[link_id]['RURAL'] = 'N'
                    
                    elif(links_dict[link_id]['COUNTRY'].find('Luxemburg') >= 0):
                        if((geom['NAME'][0] in ['A','E']) and (int(geom['NAME'][1]) in [0,1,2,3,4,5,6,7,8,9])):
                            links_dict[link_id]['HIGHWAY'] = 'Y'
                            links_dict[link_id]['CITY'] = 'N'
                            links_dict[link_id]['RURAL'] = 'N'
                        else:
                            links_dict[link_id]['HIGHWAY'] = 'N'
                            links_dict[link_id]['CITY'] = 'Y'
                            links_dict[link_id]['RURAL'] = 'N'
                    
                    elif(links_dict[link_id]['COUNTRY'].find('France') >= 0):
                        if((geom['NAME'][0] in ['A','E']) and (int(geom['NAME'][1]) in [0,1,2,3,4,5,6,7,8,9])):
                            links_dict[link_id]['HIGHWAY'] = 'Y'
                            links_dict[link_id]['CITY'] = 'N'
                            links_dict[link_id]['RURAL'] = 'N'
                        else:
                            links_dict[link_id]['HIGHWAY'] = 'N'
                            links_dict[link_id]['CITY'] = 'Y'
                            links_dict[link_id]['RURAL'] = 'N'
                    

                setRoadGeomWeight(links_dict[link_id], geom, cfg['query_features'])
            except:
                continue
    return links_dict

def setRoadGeomWeight(links_dict, attributes: dict, features_query: dict, percentage = PERCENTAGE_):
    if(features_query['boolean_features']['highway']):
        if(links_dict['HIGHWAY'] == 'Y'):
            links_dict['WEIGHT'] *= percentage
            links_dict['N_ATTRIBUTES'] += 1
    if(features_query['boolean_features']['avoid_highway']):
        if(links_dict['HIGHWAY'] == 'N'):
            links_dict['WEIGHT'] *= percentage
            links_dict['N_ATTRIBUTES'] += 1
    if(features_query['boolean_features']['urban']):  
        if(str(attributes['CITY']) == 'Y'):
            links_dict['WEIGHT'] *= percentage
            links_dict['N_ATTRIBUTES'] += 1
    if(features_query['boolean_features']['tunnel']):  
        if(str(attributes['TUNNEL']) == 'Y'):
            links_dict['WEIGHT'] *= percentage
            links_dict['N_ATTRIBUTES'] += 1
    if(features_query['boolean_features']['bridge']): 
        if(str(attributes['BRIDGE']) == 'Y'):
            links_dict['WEIGHT'] *= percentage
            links_dict['N_ATTRIBUTES'] += 1
    return None

def setRoadTypes(links_dict,cfg):
    if(cfg['region'] == 'us'):
        for link_id in links_dict:
            if(links_dict[link_id]['FUNCTIONAL_CLASS'] in [1,2]):
                links_dict[link_id]['HIGHWAY'] = 'Y'
                links_dict[link_id]['CITY'] = 'N'
                links_dict[link_id]['RURAL'] = 'N'
            elif(links_dict[link_id]['FUNCTIONAL_CLASS'] == 3):
                links_dict[link_id]['HIGHWAY'] = 'N'
                if((links_dict[link_id]['TRAVEL_DIRECTION'] == 'B') and (links_dict[link_id]['LANE_CATEGORY'] == 1) and ((links_dict[link_id]['SPEED_LIMIT'] == None) or (links_dict[link_id]['SPEED_LIMIT'] >= 70))):
                    links_dict[link_id]['CITY'] = 'N'
                    links_dict[link_id]['RURAL'] = 'Y'
                else:
                    links_dict[link_id]['CITY'] = 'Y'
                    links_dict[link_id]['RURAL'] = 'N'
            elif(links_dict[link_id]['FUNCTIONAL_CLASS'] == 4):
                links_dict[link_id]['HIGHWAY'] = 'N'
                if((links_dict[link_id]['TRAVEL_DIRECTION'] == 'B') and (links_dict[link_id]['LANE_CATEGORY'] == 1) and ((links_dict[link_id]['SPEED_LIMIT'] == None) or (links_dict[link_id]['SPEED_LIMIT'] >= 64))):
                    links_dict[link_id]['CITY'] = 'N'
                    links_dict[link_id]['RURAL'] = 'Y'
                else:
                    links_dict[link_id]['CITY'] = 'Y'
                    links_dict[link_id]['RURAL'] = 'N'
            else:
                links_dict[link_id]['HIGHWAY'] = 'N'
                links_dict[link_id]['CITY'] = 'Y'
                links_dict[link_id]['RURAL'] = 'N'
