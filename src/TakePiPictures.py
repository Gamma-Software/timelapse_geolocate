import sys
from enum import Enum
from picamera import PiCamera
import picamera
from time import sleep
import datetime as dt
import logging
import time
import os
import yaml
from paho.mqtt import client as mqtt


# MQTT methods
def on_connect(client, userdata, flags, rc):  # The callback for when the client connects to the broker
    logging.info("Connected with result code {0}".format(str(rc)))  # Print result of connection attempt
    client.subscribe("gps/latitude")  # Subscribe to the topic “digitest/test1”, receive any messages published on it
    client.subscribe("gps/longitude")  # Subscribe to the topic “digitest/test1”, receive any messages published on it
    client.subscribe("gps/timestamp")  # Subscribe to the topic “digitest/test1”, receive any messages published on it
    client.subscribe("tripcam/app/alive")


class TimelapseGeneratorCommand(Enum):
    PAUSE = 0
    RESUME = 1
    STOP = 2


def on_message(client, userdata, msg):  # The callback for when a PUBLISH message is received from the server.
    global latitude, longitude, timestamp, alive, state
    data = msg.payload.decode("utf-8")
    if msg.topic == "gps/timestamp":
        timestamp = float(data)
    if msg.topic == "gps/latitude":
        latitude = float(data)
    if msg.topic == "gps/longitude":
        longitude = float(data)
    if msg.topic == "tripcam/app/alive":
        alive = bool(data)
    if msg.topic == "timelaspe_generator/app/command":
        command = TimelapseGeneratorCommand(data)
        # Accept instance of only TimelapseGeneratorCommand
        if isinstance(command, TimelapseGeneratorCommand):
            logging.info("Change app state from " + repr(state) + " to " + repr(command) + " succeeded")
            state = command
        else:
            logging.warning("Change app state from " + repr(state) + " to " + repr(command) + " failed")


# ----------------------------------------------------------------------------------------------------------------------
# Read script parameters
# ----------------------------------------------------------------------------------------------------------------------
path_to_conf = os.path.join("/etc/timelapse_generator/config.yaml")
# If the default configuration is not install, then configure w/ the default one
if not os.path.exists(path_to_conf):
    sys.exit("Configuration file %s does not exists. Please reinstall the app" % path_to_conf)
# load configuration
with open(path_to_conf, "r") as file:
    conf = yaml.load(file, Loader=yaml.FullLoader)

# ----------------------------------------------------------------------------------------------------------------------
# Initiate variables
# ----------------------------------------------------------------------------------------------------------------------
logging.basicConfig(
    filename="/var/log/timelapse_generator/take_picture.log",
    filemode="a", level=logging.DEBUG if conf.debug else logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt='%m/%d/%Y %I:%M:%S %p')

alive = False
state = TimelapseGeneratorCommand.START
timestamp = 0.0
latitude = 0.0
longitude = 0.0

# ----------------------------------------------------------------------------------------------------------------------
# Initiate MQTT client and try to connect
# ----------------------------------------------------------------------------------------------------------------------
logging.info("Create mqtt client with timelapse_generator_take_picture id")
client = mqtt.Client("timelapse_generator_take_picture")  # Create instance of client with client ID “digi_mqtt_test”
logging.info("trying to connect to localhost")
client.on_connect = on_connect  # Define callback function for successful connection
client.on_message = on_message  # Define callback function for receipt of a message
client.connect("localhost")
client.loop_start()
client.publish("timelapse_generator/app/status", "started")

while not alive:
    logging.info("Wait 1s for connection to publisher")
    sleep(1.0)

# ----------------------------------------------------------------------------------------------------------------------
# Initiate PiCamera
# ----------------------------------------------------------------------------------------------------------------------
camera = PiCamera()
camera.resolution = (conf.camera_width, conf.camera_height)
camera.annotate_background = picamera.Color('black')

# ----------------------------------------------------------------------------------------------------------------------
# Create subfolders in /home/camera/
# ----------------------------------------------------------------------------------------------------------------------
datetime = dt.datetime.now().strftime('%Y%m%d_%H%M%S')
path = conf.root_temp_image_loc + datetime
images_path = path + "/images"
log_path = path + "/log"
access_rights = 0o755
try:
    os.mkdir(path, access_rights)
except OSError:
    sys.exit("Creation of the directory %s failed" % path)
try:
    os.mkdir(images_path, access_rights)
except OSError:
    sys.exit("Creation of the directory %s failed" % images_path)
try:
    os.mkdir(log_path, access_rights)
except OSError:
    sys.exit("Creation of the directory %s failed" % log_path)

# Warm up the raspberry camera
logging.info("Warming up")
camera.start_preview()
sleep(2.0)

# ----------------------------------------------------------------------------------------------------------------------
# Main loop
# ----------------------------------------------------------------------------------------------------------------------
while state is not TimelapseGeneratorCommand.STOP:
    if state is TimelapseGeneratorCommand.PAUSE:
        logging.info("Script pause by user")
        time.sleep(0.5)
    try:
        start_time = time.time()
        datetime = dt.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        client.publish("timelapse_generator/app/status", "take picture")
        # Take the picture
        camera.annotate_text = datetime + "_lat:" + str(latitude) + "_lon:" + str(longitude)
        camera.capture(images_path + "/" + datetime + "_" + str(latitude) + "_" + str(longitude) + ".jpg")
        logging.info("Capture " + images_path + "/" + datetime + "_" + str(latitude) + "_" + str(longitude) + ".jpg")

        elapsed_time = 60/conf.fpm - (time.time() - start_time)
        client.publish("timelapse_generator/app/status", "sleeps")
        if elapsed_time > 0.0:
            logging.info("Sleeps "+str(elapsed_time))
            time.sleep(elapsed_time)
        else:
            logging.info("Sleeps by default with 0.1s")
            time.sleep(0.1)
    except KeyboardInterrupt:
        logging.warning("timelapse_generator app is ended by user")
        break

logging.info("Script stopped by user")
client.publish("timelapse_generator/app/status", "stop")
camera.stop_preview()
client.loop_stop()
sys.exit(0)
