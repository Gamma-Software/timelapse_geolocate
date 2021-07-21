from influxdb import InfluxDBClient, DataFrameClient
import influxdb
import pandas as pd
from datetime import datetime, timezone, timedelta


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

def retrieve_lat_lon(timestamps, margin, influxdb_client):
    """
    retrieve_lat_lon(timestamps, margin, influxdb_client)->DataFrame
    timestamps: This is a list of the timestamps to retrieve the latlon positions
    margin: time margin before start and after end of the timestamp bound 
    influxdb_client: influxbd client to connect to
    return a Pandas DataFrame; warn: it can be empty if no latlon is found
    """
    start = (timestamps[0] + timedelta(seconds=-margin)).isoformat()
    end = (timestamps[-1] + timedelta(seconds=margin)).isoformat()
    
    # Query the lat and lon values inside of the first and last + margin timestamps
    latitude = influxdb_client.query("SELECT * FROM \"autogen\".\"mqtt_consumer\" WHERE (\"topic\"\
         = '/gps_measure/latitude') AND time >= '"+start+"Z' AND time <= '"+end+"Z'")
    longitude = influxdb_client.query("SELECT * FROM \"autogen\".\"mqtt_consumer\" WHERE (\"topic\"\
         = '/gps_measure/longitude') AND time >= '"+start+"Z' AND time <= '"+end+"Z'")
    # Check the values
    if latitude.empty or longitude.empty:
        return pd.DataFrame()
    # Clean, resample 1s just to be sure, add the values to one specific DataFrame
    latitude["mqtt_consumer"].drop(["host", "topic"], axis=1)
    longitude["mqtt_consumer"].drop(["host", "topic"], axis=1)
    latitude["mqtt_consumer"] = latitude["mqtt_consumer"].resample('1S').first()
    longitude["mqtt_consumer"] = longitude["mqtt_consumer"].resample('1S').first()
    gps_coords = latitude["mqtt_consumer"].copy()
    gps_coords["longitude"] = longitude["mqtt_consumer"]["value"]
    gps_coords.columns = ["latitude"]
    # Fill NaN cells
    gps_coords = gps_coords.fillna(method="ffill")

timestamps = [datetime.strptime(timestamp_dirty.strip(".jpg"), '%Y-%m-%d_%H-%M-%S').isoformat() for timestamp_dirty in images_sorted]
client = DataFrameClient("localhost", "8086", "rudloff", "y4uv3jpc", "telegraf")
#client =  DataFrameClient(conf["influxdb"]["url"], conf["influxdb"]["port"], conf["influxdb"]["name"], conf["influxdb"]["pass"], conf["influxdb"]["database"])
margin = 5
#margin = conf["timestamp_margin"]
retrieve_lat_lon(timestamps, margin, client)

# Create the list of timestamp to generate the map
timestamps_to_maps = [datetime.strptime(images_name.strip(".jpg"), '%Y-%m-%d_%H-%M-%S').isoformat() for images_name in images_sorted]

# Filter out only on timestamps from the images
mask = (gps_coords.index >= timestamps_to_maps[0]) & (gps_coords.index <= timestamps_to_maps[-1])
gps_coords = gps_coords.loc[mask]


import matplotlib.pyplot as plt
import tilemapbase

#t = tilemapbase.tiles.build_OSM()
t = tilemapbase.tiles.Tiles("http://localhost:8000/osm/{zoom}/{x}/{y}.png", "OSM", headers={"User-Agent":"TileMapBase"})

def show_map(lat, lon, id):
    degree_range = 0.003
    extent = tilemapbase.Extent.from_lonlat(lon[-1] - degree_range, lon[-1] + degree_range,
                    lat[-1] - degree_range, lat[-1] + degree_range)
    extent = extent.to_aspect(1.0)
    fig, ax = plt.subplots(figsize=(8, 8), dpi=100) 
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)
    plotter = tilemapbase.Plotter(extent, t, width=600)
    plotter.plot(ax, t)

    x, y = tilemapbase.project(*[lon[-1], lat[-1]])
    ax.scatter(x,y, marker=".", color="black", linewidth=20)
    plt.savefig("map/"+str(id)+".png",bbox_inches='tight', dpi=200, pad_inches=0)
    print("saved map ", id)
    #plt.show()
    plt.close()


show_map([0], [0], "2021-07-20_17-40-40")
exit(0)

lat_list = []
lon_list = []
for lat, lon, timestamp in zip(gps_coords["latitude"].tolist(), gps_coords["longitude"].tolist(), gps_coords.index) :
    lat_list.append(lat)
    lon_list.append(lon)
    show_map(lat_list, lon_list, datetime.strftime(timestamp, '%Y-%m-%d_%H-%M-%S'))

import cv2
import numpy as np
#from matplotlib import pyplot as plt
from datetime import datetime
from os import walk


def combine(map_path, frame_path, id, video_out):
    x_offset = y_offset = 20
    map_image = cv2.imread(map_path)
    scale_percent = 80
    width = int(map_image.shape[1] * scale_percent / 100)
    height = int(map_image.shape[0] * scale_percent / 100)
    dsize = (width, height)
    map_image = cv2.resize(map_image, dsize)

    frame = cv2.imread(frame_path)
    mask = np.zeros(frame.shape[:2], dtype="uint8")
    cv2.circle(mask, (frame.shape[1] - int(map_image.shape[0]/2) - x_offset,
                      frame.shape[0] - int(map_image.shape[1]/2) - y_offset),
               int(map_image.shape[0]/2), 255, -1)
    mask_inv = cv2.bitwise_not(mask)
    frame_masked = cv2.bitwise_and(frame, frame, mask=mask_inv)

    frame[frame.shape[0] - map_image.shape[0] - y_offset*2 : frame.shape[0] - y_offset*2,
          frame.shape[1] - map_image.shape[1] - x_offset : frame.shape[1] - x_offset] = map_image
    map_masked = cv2.bitwise_and(frame, frame, mask=mask)
    dst = cv2.add(frame_masked, map_masked)
    frame[0:frame.shape[0], 0:frame.shape[1]] = dst

    date = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    lat = 10
    lon = 15
    localisation = " lat: " + str(lat) + ", " + "lon :" + str(lon)
    text = date + ", " + localisation
    cv2.putText(frame,text,(10,30), cv2.FONT_HERSHEY_DUPLEX, 1,(0,0,0),2,cv2.LINE_AA)
    cv2.imwrite("result/"+str(id)+".png", frame)

    video_out.write(frame)

frameSize = (2304, 1296)
video_out = cv2.VideoWriter('result/output.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 10, frameSize)

for timestamp in images_sorted:
    combine("map/"+timestamp.strip(".jpg")+".png", os.path.join(initdir, timelapse_to_process, timestamp), timestamp.strip(".jpg"), video_out)

video_out.release()