from influxdb import InfluxDBClient, DataFrameClient
import pandas as pd
from datetime import datetime, timezone, timedelta


client = DataFrameClient("localhost", "8086", "rudloff", "y4uv3jpc", "telegraf")

def generate_timelapse():
    print("test")

import os
initdir = "/tmp/timelapse_trip/"
for timelapse_to_process in os.listdir(initdir):
    print(timelapse_to_process)
    if len(os.listdir(os.path.join(initdir, timelapse_to_process))) == 0:
        print("remove empty timelapse_trip folder"+ os.path.join(initdir, timelapse_to_process))
        os.rmdir(os.path.join(initdir, timelapse_to_process))
    else:
        images_sorted = sorted(os.listdir(os.path.join(initdir, timelapse_to_process)))
        print(images_sorted)
        break

start = (datetime.strptime(images_sorted[0].strip(".jpg"), '%Y-%m-%d_%H-%M-%S') + timedelta(seconds=-5)).isoformat()
end = (datetime.strptime(images_sorted[-1].strip(".jpg"), '%Y-%m-%d_%H-%M-%S') + timedelta(seconds=5)).isoformat()
client = DataFrameClient("localhost", "8086", "rudloff", "y4uv3jpc", "telegraf")
result = client.query("SELECT * FROM \"autogen\".\"mqtt_consumer\" WHERE (\"topic\" = '/gps_measure/latitude') AND time >= '"+start+"Z' AND time <= '"+end+"Z'")
result["mqtt_consumer"].drop(["host", "topic"], axis=1, inplace=True)
result["mqtt_consumer"] = result["mqtt_consumer"].resample('1S').first()
gps_coords = result["mqtt_consumer"].copy()
gps_coords.columns = ["latitude"]
result = client.query("SELECT * FROM \"autogen\".\"mqtt_consumer\" WHERE (\"topic\" = '/gps_measure/longitude') AND time >= '"+start+"Z' AND time <= '"+end+"Z'")
result["mqtt_consumer"].drop(["host", "topic"], axis=1, inplace=True)
result["mqtt_consumer"] = result["mqtt_consumer"].resample('1S').first()
gps_coords["longitude"] = result["mqtt_consumer"]["value"]
gps_coords = gps_coords.fillna(method="ffill")

# Create the list of timestamp to generate the map
timestamps_to_maps = [datetime.strptime(images_name.strip(".jpg"), '%Y-%m-%d_%H-%M-%S').isoformat() for images_name in images_sorted]

# Filter out only on timestamps from the images
mask = (gps_coords.index >= timestamps_to_maps[0]) & (gps_coords.index <= timestamps_to_maps[-1])
gps_coords = gps_coords.loc[mask]


import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
import io
from urllib.request import urlopen, Request
from PIL import Image

def show_map(lat, lon, id):
    def image_spoof(self, tile):  # this function pretends not to be a Python script
        url = self._image_url(tile)  # get the url of the street map API
        req = Request(url)  # start request
        req.add_header('User-agent', 'Anaconda 3')  # add user agent to request
        fh = urlopen(req)
        im_data = io.BytesIO(fh.read())  # get image
        fh.close()  # close url
        img = Image.open(im_data)  # open image with PIL
        img = img.convert(self.desired_tile_form)  # set image format
        return img, self.tileextent(tile), 'lower'  # reformat for cartopy

    import cartopy.io.img_tiles as cimgt


    cimgt.OSM.get_image = image_spoof  # reformat web request for street map spoofing
    osm_img = cimgt.GoogleTiles()  # spoofed, downloaded street map
    #osm_img = cimgt.QuadtreeTiles()  # spoofed, downloaded street map

    fig = plt.figure(figsize=(5,5), frameon=False)
    ax1 = plt.axes(projection=osm_img.crs)
    center_pt = [lat[-1], lon[-1]]  # lat/lon of One World Trade Center in NYC
    zoom = 100  # for zooming out of center point
    print(center_pt)
    extent = [center_pt[1] - (zoom * 1.5), center_pt[1] + (zoom * 1.5), center_pt[0] - zoom,
              center_pt[0] + zoom]  # adjust to zoom
    print(extent)
    #ax1.set_extent(extent, crs=osm_img.crs)  # set extents

    scale = np.ceil(-np.sqrt(2) * np.log(np.divide(zoom, 350.0)))  # empirical solve for scale based on zoom
    scale = (scale < 20) and scale or 19  # scale cannot be larger than 19
    ax1.add_image(osm_img, int(scale))  # add OSM with zoom specification
    ax1.set_axis_off()
    fig.add_axes(ax1)
    # NOTE: zoom specifications should be selected based on extent:
    # -- 2     = coarse image, select for worldwide or continental scales
    # -- 4-6   = medium coarseness, select for countries and larger states
    # -- 6-10  = medium fineness, select for smaller states, regions, and cities
    # -- 10-12 = fine image, select for city boundaries and zip codes
    # -- 14+   = extremely fine image, select for roads, blocks, buildings
    plt.plot(lon, lat, color='red', linewidth=2, alpha=0.5,
             transform=ccrs.Geodetic(),
             )
    plt.plot(lon[-1], lat[-1],
             color='blue', markersize=10, marker='o',
             transform=ccrs.Geodetic(),
             )
    plt.savefig("map/"+str(id)+".png",bbox_inches='tight', pad_inches=0)
    #plt.show()
    plt.close()


lat_list = []
lon_list = []
for lat, lon in zip(gps_coords["latitude"].tolist(), gps_coords["longitude"].tolist()) :
    lat_list.append(lat)
    lon_list.append(lon)
    show_map(lat_list, lon_list, len(lat_list)-1)