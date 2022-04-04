import requests
from requests.sessions import session
from math import radians, cos, sin, asin, sqrt, pi
import random
import pandas as pd
import os
from HERErequest import  getTiles, getTileRequest

API_KEY = "d-aIdnx2a7WmFl5t2nDznTNmOfB3O3p1fGIxGfjaboM"

getIdxList_count = 0
def getIdxListCount():
    global getIdxList_count
    print(f"[INFO] total {getIdxList_count} api is called")

#This function transforms degrees to radians
def degtorad(deg: float):
    return deg * (pi/180)

#This function return the distance between two gps locations
def Haversine(loc1, loc2):
    earth_rad = 6378 #km
    dlat1 = degtorad(loc1[0])
    dlat2 = degtorad(loc2[0])
    dlon1 = degtorad(loc1[1])
    dlon2 = degtorad(loc2[1])
    dlat = dlat2 - dlat1
    dlon = dlon2 - dlon1
    dist = 2 * earth_rad * asin(((sin(dlat/2)**2) + cos(dlat1)*cos(dlat2)*(sin(dlon/2)**2) )**(1/2))
    return dist

#This function returns a list of tiles
def getIdxList(tilex, tiley, level, depth_target):
    global getIdxList_count
    l = []
    if level != depth_target:
        for i in range(2 * tilex, 2 * tilex + 2):
            for j in range(2 * tiley, 2 * tiley + 2):
                l.extend(getIdxList(i, j, level + 1, depth_target))
    l.append((tilex, tiley, level))
    getIdxList_count += len(l)
    return l

#This function returns the euclidean distance between two gps locations
def distance(loc1, loc2):
    dist = sqrt((loc1[0]-loc2[0])**2 + (loc1[1]-loc2[1])**2)
    return dist

#This function returns a charge stations list
def ChargingStations(tiles: tuple, session): 
    stations_dict = {}
    for tile in tiles:
        stations = getTileRequest(tile, f'EVCHARGING_POI', session)['Rows']
        for s in stations:
            if(str(s['CONNECTORTYPE']) != str(None)):
                stations_dict[s['POI_ID']] = {'LINK_ID' : s['LINK_ID'],
                                              'CONNECTOR_TYPE' : s['CONNECTORTYPE'],
                                              'PAYMENT_METHOD' : s['PAYMENTMETHOD'],
                                              'LOC': (int(s['LAT'])/100000,int(s['LON'])/100000)}
    return stations_dict

#This function deletes the tiles files stored in cache
def deleteCache():
    dir = os.path.join(os.getcwd(), 'tiles_cache')
    for f in os.listdir(dir):
        os.remove(os.path.join(dir, f))
    dir = os.path.join(os.getcwd(), 'graph_cache')
    for f in os.listdir(dir):
        os.remove(os.path.join(dir, f))

#This function returns a set of gps locations between two points
def lineOfSamplePoints(startLoc: tuple, endLoc: tuple, sample_separation = 0.01):
    diffx = abs(startLoc[1] - endLoc[1])
    diffy = abs(startLoc[0] - endLoc[0])
    diffmax = max(diffx,diffy)
    n = floor(diffmax/sample_separation)
    points = [startLoc]
    if((startLoc[1] - endLoc[1]) != 0):
        m = (startLoc[0] - endLoc[0]) / (startLoc[1] - endLoc[1])
        b = startLoc[0] - (m*startLoc[1])
        step = (startLoc[1] - endLoc[1])/n
        for i in range(n + 1):
            x = startLoc[1] - i*step
            p =  x*m + b
            points.append((p,x))
            points.append((p,x))
    else:
        step = (startLoc[0] - endLoc[0])/n
        for i in range(n + 1):
            x = startLoc[1]
            p =  startLoc[0] - i*step
            points.append((p,x))
            points.append((p,x))
    points.append(endLoc)
    return points

#This function deletes the routes files before a new route request
def removeGPXFiles(path: str):
    output_files = os.listdir(path)
    for name in output_files:
        os.remove(path+name)

#This function return a random gps location inside a fixed distance
def getRandomLocation(start_location: tuple, dist: float):
    dist = dist/90
    theta = 2*pi*random.random()
    lat = start_location[0] + dist*sin(theta)
    lon = start_location[1] + dist*cos(theta)
    loc = (lat,lon)
    return loc
    