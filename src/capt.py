from picamera import PiCamera
import picamera
from time import sleep
import datetime as dt
import logging
import time

from paho.mqtt import client as mqtt


def on_connect(client, userdata, flags, rc):  # The callback for when the client connects to the broker
    logging.info("Connected with result code {0}".format(str(rc)))  # Print result of connection attempt
    client.subscribe("gps/latitude")  # Subscribe to the topic “digitest/test1”, receive any messages published on it
    client.subscribe("gps/longitude")  # Subscribe to the topic “digitest/test1”, receive any messages published on it
    client.subscribe("gps/timestamp")  # Subscribe to the topic “digitest/test1”, receive any messages published on it
    client.subscribe("tripcam/app/alive")



def on_message(client, userdata, msg):  # The callback for when a PUBLISH message is received from the server.
    global latitude, longitude, timestamp, alive
    data = msg.payload.decode("utf-8")
    if msg.topic == "gps/timestamp":
        timestamp = float(data)
    if msg.topic == "gps/latitude":
        latitude = float(data)
    if msg.topic == "gps/longitude":
        longitude = float(data)
    if msg.topic == "tripcam/app/alive":
        alive = bool(data)

alive=False
timestamp = 0.0
latitude = 0.0
longitude = 0.0
picture_cache_location = "/home/camera/images/"

logging.basicConfig(
    filename="/home/pi/log/capture" + dt.datetime.now().strftime("%Y%m%d-%H%M%S") + ".log",
    filemode="a", level=logging.DEBUG, format="%(asctime)s %(levelname)s:%(message)s", datefmt='%m/%d/%Y %I:%M:%S %p')

logging.info("Create mqtt client")
client = mqtt.Client("my_id")  # Create instance of client with client ID “digi_mqtt_test”
logging.info("trying to connect to localhost")
client.on_connect = on_connect  # Define callback function for successful connection
client.on_message = on_message  # Define callback function for receipt of a message
client.connect("localhost")
client.loop_start()

while not alive:
    logging.info("Wait 1s for connection to publisher")
    sleep(1.0)

camera = PiCamera()
camera.resolution = (1920, 1080)
camera.annotate_background = picamera.Color('black')

# Warm up the raspberry camera
print("Warm up")
logging.info("Warming up")
camera.start_preview()
sleep(2.0)

while alive:
    start_time = time.time()
    try:
        # Take the picture
        camera.annotate_background = picamera.Color('black')
        camera.annotate_text = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "-lat:" + str(latitude) + "-lon:" + str(longitude)
        camera.capture(picture_cache_location + dt.datetime.fromtimestamp(timestamp).strftime('%Y%m%d-%H:%M:%S') + "-" +
                       str(latitude) + "-" + str(longitude) + ".png")
        print("Capture " + picture_cache_location + dt.datetime.fromtimestamp(timestamp).strftime('%Y%m%d-%H:%M:%S') + "-" +
              str(latitude) + "-" + str(longitude) + ".png")
        logging.info("Capture " + picture_cache_location + dt.datetime.fromtimestamp(timestamp).strftime('%Y%m%d-%H:%M:%S') + "-" +
                     str(latitude) + "-" + str(longitude) + ".png")

        elapsed_time = 5 - (time.time() - start_time)
        if elapsed_time > 0.0:
            logging.info("Sleeps "+str(elapsed_time))
            time.sleep(elapsed_time)
        else:
            logging.info("Sleeps by default with 0.1s")
            time.sleep(0.1)
    except KeyboardInterrupt:
        break
        # Close camera instance
camera.stop_preview()
#take_picture_annotate(client, "/home/camera/images/", 1920, 1080, 0.0, 0.0)
client.loop_stop()