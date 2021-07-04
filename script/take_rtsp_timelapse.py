#!/usr/bin/env python3
import io
import os
import subprocess
from timelapse_geolocate.src.enums import Motion
import yaml
import sys
import pynmea2
import serial
import time
import logging
import datetime as dt
import paho.mqtt.client as mqtt
from subprocess import Popen, PIPE
from timelapse_geolocate.script.enums import Motion


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
# MQTT methods
def on_connect(client, userdata, flags, rc):  # The callback for when the client connects to the broker
    logging.info("Connected with result code {0}".format(str(rc)))  # Print result of connection attempt
    client.subscribe("capsule/motion_state")
    client.subscribe("timelapse_trip/stop_command")

motion_state = Motion.STOP # By default
stop_command = False
def on_message(client, userdata, msg):  # The callback for when a PUBLISH message is received from the server.
    global motion_state, stop_command
    data = msg.payload.decode("utf-8")
    if msg.topic == "timelapse_trip/stop_command":
        stop_command = bool(data)
    if msg.topic == "capsule/motion_state":
        command = Motion(data)
        # Accept instance of only TimelapseGeneratorCommand
        if isinstance(command, Motion):
            logging.info("Change app state from " + repr(state) + " to " + repr(command) + " succeeded")
            motion_state = command
        else:
            logging.warning("Change app state from " + repr(state) + " to " + repr(command) + " failed")

client = mqtt.Client()
logging.info("Connect to localhost broker")
client.username_pw_set(conf["mqtt"]["user"], conf["mqtt"]["pass"])
client.on_connect = on_connect  # Define callback function for successful connection
client.connect(conf["mqtt"]["host"], conf["mqtt"]["port"])
client.loop_start()

while not client.is_connected():
    logging.info("Waiting for the broker connection")
    time.sleep(1)


# ----------------------------------------------------------------------------------------------------------------------
# Main loop
# ----------------------------------------------------------------------------------------------------------------------
args = ["ffmpeg", "-rtsp_transport tcp", "-y", "-i", 
conf["rtsp"]["stream_name"], "-q:v 4",
"-vf", "fps="+conf["rtsp"]["framerate"], "-strftime 1", "-strftime_mkdir 1", '"%Y%m%d/%Y-%m-%d_%H-%M-%S.jpg"']
try:
    while True:
        if motion_state == Motion.STOP or stop_command:
            logging.warning("The Timelapse will not start because of the vehicle is Stopped or the user asks to stop the timelapse")
            break
        process = Popen(args, stdin=PIPE, stderr=PIPE, shell=True, encoding='utf8')
        try:
            logging.info("Start timelapse")
            while motion_state != Motion.STOP and not stop_command:
                client.publish("process/timelapse_trip/alive", True)
                stdout, stderr = process.communicate()
                if stdout:
                    logging.info(stdout)
                if stderr:
                    logging.error(stderr)
                time.sleep(0.5)
        except subprocess.TimeoutExpired as e:
            logging.warning('Timelapse process as been killed outside of the script: {}'.format(e))
            process.communicate(input='q')
            logging.info("Wait 5 seconds for the subprocess to be correctly killed")
            time.sleep(5)
            break
except KeyboardInterrupt:
    process.communicate(input='q')
    logging.info("Wait 5 seconds for the subprocess to be correctly killed")
    time.sleep(0.5)
    pass
logging.info("Stop script")
client.publish("process/timelapse_trip/alive", False)
client.loop_stop()
client.disconnect()
sys.exit(0)
