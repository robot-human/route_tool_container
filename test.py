from Config import cfg
import requests
from HERErequest import  getTiles
from HEREgraph2 import getLinksFromTile

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
k = links_dict.keys()

printDict(links_dict['1237622720'])




