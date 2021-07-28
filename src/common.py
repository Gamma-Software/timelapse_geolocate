import os
import shutil
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from influxdb import DataFrameClient
from typing import List
import cv2
import tilemapbase
import matplotlib.pyplot as plt


def get_timelapse_to_process(timelapse_tmp_path, timelapse_generated_path)->List:
    """
    Get the list of timelapse folders to process if they are not empty
    timelapse_tmp_path: initial temporary folder
    timelapse_generated_path: path to result folder
    """
    return_list = []
    for timelapse_to_process in os.listdir(timelapse_tmp_path):
        path = os.path.join(timelapse_tmp_path, timelapse_to_process)
        if len(os.listdir(path)) != 0 and timelapse_to_process not in os.listdir(timelapse_generated_path):
            return_list.append(path)
    return return_list

def clear_timelapse_to_process(timelapse_tmp_path, timelapse_generated_path):
    """
    Clean the timelapse temporary folders if the timelapse is generated or if the temporary folder is empty
    timelapse_tmp_path: initial temporary folder
    """
    for timelapse_to_process in os.listdir(timelapse_tmp_path):
        path = os.path.join(timelapse_tmp_path, timelapse_to_process)
        if len(os.listdir(path)) == 0 or timelapse_to_process in os.listdir(timelapse_generated_path):
            shutil.rmtree(path)

def retrieve_lat_lon(timestamps: List[datetime],  influxdb_client: DataFrameClient) -> pd.DataFrame():
    """
    timestamps: This is a list of the timestamps to retrieve the latlon positions in the iso format
    influxdb_client: influxbd client to connect to
    return a Pandas DataFrame; warn: it can be empty if no latlon is found
    """
    
    start = (datetime.fromisoformat(timestamps[0]) + timedelta(seconds=-5)).isoformat()
    end = (datetime.fromisoformat(timestamps[-1]) + timedelta(seconds=5)).isoformat()
    
    # Query the lat and lon values inside of the first and last + margin timestamps
    result = influxdb_client.query("SELECT * FROM \"autogen\".\"mqtt_consumer\" WHERE (\"topic\"\
         = '/gps_measure/latitude') AND time >= '"+start+"Z' AND time <= '"+end+"Z'")
    latitude = pd.DataFrame()
    if result:
        latitude = result["mqtt_consumer"]
    result = influxdb_client.query("SELECT * FROM \"autogen\".\"mqtt_consumer\" WHERE (\"topic\"\
         = '/gps_measure/longitude') AND time >= '"+start+"Z' AND time <= '"+end+"Z'")
    longitude = pd.DataFrame()
    if result:
        longitude = result["mqtt_consumer"]
    # Check the values
    if latitude.empty or longitude.empty:
        return pd.DataFrame()
    # Clean, resample 1s just to be sure, add the values to one specific DataFrame
    latitude.drop(["host", "topic"], axis=1, inplace=True)
    longitude.drop(["host", "topic"], axis=1, inplace=True)
    latitude = latitude.resample('1S').first()
    longitude = longitude.resample('1S').first()
    gps_coords = pd.DataFrame()
    gps_coords = latitude.copy()
    gps_coords = latitude.copy()
    gps_coords["longitude"] = longitude["value"]
    gps_coords.columns = ["longitude", "latitude"]
    # Fill NaN cells
    gps_coords = gps_coords.fillna(method="ffill")
    # Filter out only on timestamps from the images
    mask = (gps_coords.index >= timestamps[0]) & (gps_coords.index <= timestamps[-1])
    gps_coords = gps_coords.loc[mask]
    return gps_coords

def retrieve_save_map(lat, lon, tiles, output_title, output_path):
    """
    Retrieve and save the map corresponding on the lat lon coordinates
    gps_coords: gps coordinates
    tiles: tilemapbase instance
    output_title: output title
    output_path: folder name to save the map to
    """
    degree_range = 0.003
    extent = tilemapbase.Extent.from_lonlat(
        lon[-1] - degree_range, lon[-1] + degree_range, lat[-1] - degree_range, lat[-1] + degree_range)
    extent = extent.to_aspect(1.0)
    fig, ax = plt.subplots(figsize=(8, 8), dpi=100) 
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)
    plotter = tilemapbase.Plotter(extent, tiles, width=600)
    plotter.plot(ax, tiles)
    # TODO simplify database usage
    x, y = tilemapbase.project(*[lon[-1], lat[-1]])
    ax.scatter(x,y, marker=".", color="black", linewidth=20)
    plt.savefig(output_path+"/"+output_title+".png",bbox_inches='tight', dpi=200, pad_inches=0)
    plt.close()

def combine(map_path, frame_path, timestamp, latitude, longitude):
    """
    Combine the timelapse frame and the map to display
    map_path: folder path to the map
    timestamp: timestamp
    latitude: latitude
    longitude: longitude
    frame_path: folder path to the timelapse frame
    """
    # Read images
    map_image = cv2.imread(map_path)
    frame = cv2.imread(frame_path)

    # Resize the map images
    x_offset = y_offset = 20
    scale_percent = 80
    width = int(map_image.shape[1] * scale_percent / 100)
    height = int(map_image.shape[0] * scale_percent / 100)
    dsize = (width, height)
    map_image = cv2.resize(map_image, dsize)

    # Create a circle mask
    mask = np.zeros(frame.shape[:2], dtype="uint8")
    cv2.circle(mask, (frame.shape[1] - int(map_image.shape[0]/2) - x_offset,
                      frame.shape[0] - int(map_image.shape[1]/2) - y_offset),
               int(map_image.shape[0]/2), 255, -1)
    mask_inv = cv2.bitwise_not(mask)
    frame_masked = cv2.bitwise_and(frame, frame, mask=mask_inv)

    # Incrust the map mask onto the frame
    frame[frame.shape[0] - map_image.shape[0] - y_offset*2 : frame.shape[0] - y_offset*2,
          frame.shape[1] - map_image.shape[1] - x_offset : frame.shape[1] - x_offset] = map_image
    map_masked = cv2.bitwise_and(frame, frame, mask=mask)
    dst = cv2.add(frame_masked, map_masked)
    frame[0:frame.shape[0], 0:frame.shape[1]] = dst
    
    # Diplay metadata
    date = timestamp
    localisation = " lat: " + str(round(latitude, 1)) + ", " + "lon :" + str(round(longitude, 1))
    cv2.putText(frame,date + ", " + localisation,(10,30), cv2.FONT_HERSHEY_DUPLEX, 1,(0,0,0),2,cv2.LINE_AA)
    
    # Save frame
    return frame