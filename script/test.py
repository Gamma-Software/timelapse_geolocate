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

# Get the coords of the image
print(gps_coords.loc[datetime.strptime(images_sorted[0].strip(".jpg"), '%Y-%m-%d_%H-%M-%S')])
