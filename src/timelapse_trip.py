#!/usr/bin/env python3
import os
import yaml
import sys
import time
import logging
import datetime as dt
import paho.mqtt.client as mqtt
from subprocess import Popen, PIPE, TimeoutExpired
from influxdb import InfluxDBClient, DataFrameClient
from enums import *
from common import *
from path_files import *


# ----------------------------------------------------------------------------------------------------------------------
# Read script parameters
# ----------------------------------------------------------------------------------------------------------------------
path_to_conf = os.path.join("/etc/capsule/timelapse_trip/config.yaml")
# If the default configuration is not install, then configure w/ the default one
if not os.path.exists(path_to_conf):
    sys.exit("Configuration file %s does not exists. Please reinstall the app" % path_to_conf)
# load configuration
with open(path_to_conf, "r") as file:
    conf = yaml.load(file, Loader=yaml.FullLoader)

# ----------------------------------------------------------------------------------------------------------------------
# Initiate variables
# ----------------------------------------------------------------------------------------------------------------------
connected = False
logging.basicConfig(
    filename="/var/log/capsule/timelapse_trip/" + dt.datetime.now().strftime("%Y%m%d-%H%M%S") + ".log",
    filemode="a",
    level=logging.DEBUG if conf["debug"] else logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt='%m/%d/%Y %I:%M:%S %p')

# ----------------------------------------------------------------------------------------------------------------------
# Initiate MQTT variables
# ----------------------------------------------------------------------------------------------------------------------
motion_state = Motion.IDLE # By default
stop_command = False
latitude = 0.0,
longitude = 0.0
# MQTT methods
def on_connect(client, userdata, flags, rc):  # The callback for when the client connects to the broker
    logging.info("Connected with result code {0}".format(str(rc)))  # Print result of connection attempt
    
    for topic in ["capsule/motion_state", "timelapse_trip/stop_command", "/gps_measure/latitude", "/gps_measure/longitude"]:
        r=client.subscribe(topic)
        tries = 10
        while r[0]!=0:
            logging.info("Waiting to subscribe to " + topic + " / Will exit the process after " + tries + " tries")
            time.sleep(0.5)
            if tries <= 0:
                logging.info("Stop script")
                client.publish("process/timelapse_trip/alive", False)
                client.loop_stop()
                client.disconnect()
                sys.exit(1)

def on_message(client, userdata, msg):  # The callback for when a PUBLISH message is received from the server.
    global motion_state, stop_command, latitude, longitude
    data = msg.payload.decode("utf-8")
    if msg.topic == "timelapse_trip/stop_command":
        stop_command = True if data == "True" else False
    if msg.topic == "capsule/motion_state":
        command = Motion[data]
        # Accept instance of only TimelapseGeneratorCommand
        if isinstance(command, Motion):
            logging.info("Change app state from " + repr(motion_state) + " to " + repr(command) + " succeeded")
            motion_state = command
        else:
            logging.warning("Change app state from " + repr(motion_state) + " to " + repr(command) + " failed")
    if msg.topic == "/gps_measure/latitude":
        latitude = data
    if msg.topic == "/gps_measure/longitude":
        longitude = data

def wait_for(client,msgType,period=0.25):
 if msgType=="SUBACK":
  if client.on_subscribe:
    while not client.suback_flag:
      logging.info("waiting suback")
      client.loop()  #check for messages
      time.sleep(period)

client = mqtt.Client()
logging.info("Connect to localhost broker")
client.username_pw_set(conf["mqtt"]["user"], conf["mqtt"]["pass"])
client.on_connect = on_connect  # Define callback function for successful connection
client.on_message = on_message
client.connect(conf["mqtt"]["host"], conf["mqtt"]["port"])
client.loop_start()

while not client.is_connected():
    logging.info("Waiting for the broker connection")
    time.sleep(1)

# ----------------------------------------------------------------------------------------------------------------------
# Main loop
# ----------------------------------------------------------------------------------------------------------------------
def stop_script(process, why):
    logging.info("Process killed: " + why)
    process.stdin.write("q")
    process.communicate()[0]
    process.stdin.close()
    logging.info("Wait 5 seconds for the subprocess to be correctly killed")
    time.sleep(5)
    
try:
    while True:
        client.publish("process/timelapse_trip/alive", True)
        if motion_state != Motion.STOP and not stop_command:
            args = ["/home/rudloff/sources/CapsuleScripts/timelapse_geolocate/script/ffmpeg_timelapse_thread.sh", str(conf["rtsp"]["framerate"])]
            process = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True, encoding='utf8')
            try:
                logging.info("Start timelapse")
                while True:
                    client.publish("process/timelapse_trip/alive", True)
                    client.publish("process/timelapse_trip/last_status", "Take picture")
                    if motion_state == Motion.STOP or stop_command:
                        stop_script(process, "Motion Stop" if motion_state == Motion.STOP else "stop command by user")
                        break
                    time.sleep(1/conf["rtsp"]["framerate"])
            except TimeoutExpired as e:
                stop_script(process, 'Timelapse process as been killed outside of the script: {}'.format(e))
            except KeyboardInterrupt:
                stop_script(process, "Timelapse process as been killed by the user")
                pass
        # Get the non empty timelapses that need to be processed
        timelapses_to_process = get_timelapse_to_process(path_to_timelapse_tmp)
        if timelapses_to_process: # If the list is not empty
            client.publish("process/timelapse_trip/last_status", "Generate timelapse")
            for timelapse_to_process in timelapses_to_process:
                client.publish("process/timelapse_trip/timelapse_process_progress", 0)
                # Retrieve the timestamps
                images_sorted = sorted(os.listdir(timelapse_to_process))
                timestamps = [datetime.strptime(timestamp_dirty.strip(".jpg"), '%Y-%m-%d_%H-%M-%S').isoformat()\
                     for timestamp_dirty in images_sorted]
                client.publish("process/timelapse_trip/timelapse_process_progress", 10)
                
                # Connect to influxdb client
                #client = DataFrameClient("localhost", "8086", "rudloff", "y4uv3jpc", "telegraf")
                client =  DataFrameClient(conf["influxdb"]["url"], conf["influxdb"]["port"], conf["influxdb"]["name"], conf["influxdb"]["pass"], conf["influxdb"]["database"])
                # Get the list of gps coordinates from the influxdb database
                gps_coords = retrieve_lat_lon(timestamps, client)
                
                # Construct the map
                if conf["map_generation_mean"] == "local":
                    t = tilemapbase.tiles.Tiles(conf["map_generation"]["url"], conf["map_generation"]["tile_name"], headers={"User-Agent":"TileMapBase"})
                else:
                    t = tilemapbase.tiles.build_OSM()
               
                # Create the map folder
                path_to_maps = os.path.join(timelapse_to_process, "maps")
                os.makedirs(path_to_maps, 0o600)
                os.chown(path_to_maps, 1000, 0) # Rudloff id and group Root
                os.chmod(path_to_maps, 0o775) # Give all read access but Rudloff write access 
                lat_list = []
                lon_list = []
                for lat, lon, timestamp in zip(gps_coords["latitude"].tolist(), gps_coords["longitude"].tolist(), gps_coords.index) :
                    lat_list.append(lat)
                    lon_list.append(lon)
                    # Retrieve the maps and save it
                    retrieve_save_map(lat_list, lon_list, t, datetime.strftime(timestamp, '%Y-%m-%d_%H-%M-%S'), path_to_maps)
                    time.sleep(0.1)
                
                # Combine the map and the frame and generate the mp4 timelapse
                frameSize = (2304, 1296)
                result_folder = path_to_current_results + os.path.basename(timelapse_to_process)
                os.makedirs(result_folder, 0o600)
                video_out = cv2.VideoWriter(result_folder + "/video.mp4",
                 cv2.VideoWriter_fourcc(*'mp4v'), 10, frameSize)
                for timestamp in images_sorted:
                    video_out.write(combine(os.path.join(path_to_maps,timestamp.strip(".jpg"))+".png", os.path.join(path_to_timelapse_tmp,
                     timelapse_to_process, timestamp)))
                    time.sleep(0.05)
                video_out.release()
               
                # Combine the map and the frame and generate the gif timelapse
                video_out = cv2.VideoWriter(result_folder + "/video.gif",
                 cv2.VideoWriter_fourcc(*'gif'), 10, frameSize)
                for timestamp in images_sorted:
                    video_out.write(combine(os.path.join(path_to_maps,timestamp.strip(".jpg"))+".png", os.path.join(path_to_timelapse_tmp,
                     timelapse_to_process, timestamp)))
                    time.sleep(0.05)
                video_out.release()
                time.sleep(0.5)
        # Clear empty tmp folder or already generated timelapses
        clear_timelapse_to_process(path_to_timelapse_tmp, path_to_current_results)
        time.sleep(1)
except KeyboardInterrupt:
    stop_script(process, "Timelapse process as been killed by the user")
    pass

logging.info("Stop script")
client.publish("process/timelapse_trip/alive", False)
client.loop_stop()
client.disconnect()
sys.exit(0)