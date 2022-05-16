from HERErequest import  getTiles, fillCache
import requests 

session = requests.Session()

sample_separation = 0.001

start_gps = [42.794493, -83.422365]
end_gps = [42.693361, -82.480642]



lat_max = max(start_gps[0],end_gps[0])
lon_max = max(start_gps[1],end_gps[1])
lat_min = min(start_gps[0],end_gps[0])
lon_min = min(start_gps[1],end_gps[1])

lat_interval = lat_max - lat_min
lon_interval = lon_max - lon_min

resolution = [abs(int(lat_interval/sample_separation)),abs(int(lon_interval/sample_separation))]
lat_step = lat_interval / (resolution[0] - 1)
lon_step = lon_interval / (resolution[1] - 1)

gps_locations = []
for i in range(resolution[0]):
    for j in range(resolution[1]):
        gps_locations.append((lat_min + lat_step * i, lon_min + lon_step * j))

tiles = getTiles(gps_locations,9, 13)

fillCache(tiles,session)