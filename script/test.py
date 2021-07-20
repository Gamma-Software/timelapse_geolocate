from influxdb import InfluxDBClient, DataFrameClient
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



start = (datetime.strptime(images_sorted[0].strip(".jpg"), '%Y-%m-%d_%H-%M-%S') + timedelta(seconds=-5)).isoformat()
end = (datetime.strptime(images_sorted[-1].strip(".jpg"), '%Y-%m-%d_%H-%M-%S') + timedelta(seconds=5)).isoformat()
client = DataFrameClient("localhost", "8086", "rudloff", "y4uv3jpc", "telegraf")
result = client.query("SELECT * FROM \"autogen\".\"mqtt_consumer\" WHERE (\"topic\" = '/gps_measure/latitude') AND time >= '"+start+"Z' AND time <= '"+end+"Z'")
# TODO handle if the result is empty (result.empty) i.e. the vehicle was not localized
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
import tilemapbase

t = tilemapbase.tiles.build_OSM()

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


lat_list = []
lon_list = []
for lat, lon in zip(gps_coords["latitude"].tolist(), gps_coords["longitude"].tolist()) :
    lat_list.append(lat)
    lon_list.append(lon)
    show_map(lat_list, lon_list, len(lat_list)-1)