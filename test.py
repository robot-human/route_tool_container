import datetime
import time

print(datetime.datetime(2022, 1, 1))
"""
from Config import cfg
import requests
from HERErequest import  getTiles
from HEREgraph2 import getLinksFromTile
from HEREgraph2 import graphFromDict

session = requests.Session() 

def printDict(dict):
    for k in dict:
        length1 = len(str(k))
        length2 = len(str(dict[k]))
        spaces = 30 - length1 + length2
        right_justified_string = str(dict[k]).rjust(spaces)
        print(k,right_justified_string)

tiles = getTiles(cfg.get('gps_locations'),9, 13)


links_dict = getLinksFromTile(tiles[0], cfg['query_features'], session)

for k in links_dict.keys():
    #print(links_dict[k]['SPEED_BUMPS'])
    #if(links_dict[k]['SPEED_BUMPS'] != None):
    printDict(links_dict[k])

"""



