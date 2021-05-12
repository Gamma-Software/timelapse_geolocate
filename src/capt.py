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
    #client.subscribe("tripcam/app/state") # play/stop/pause


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
    #if msg.topic == "tripcam/app/state":
        #state = data

#state = "pause"
state = "run"
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
client.publish("tripcam/app/status", "startd")
while not alive:
    logging.info("Wait 1s for connection to publisher")
    sleep(1.0)

camera = PiCamera()
camera.resolution = (1920/2, 1080/2)
camera.annotate_background = picamera.Color('black')

# Warm up the raspberry camera
logging.info("Warming up")
camera.start_preview()
sleep(2.0)
camera.annotate_background = picamera.Color('black')

start_time = time.time()
try:
    datetime = dt.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
    for i, filename in enumerate(camera.capture_continuous(picture_cache_location + datetime + "-" + str(latitude) +
                                                           "-" + str(longitude) + ".jpg")):
        client.publish("tripcam/app/status", "take picture")
        camera.annotate_text = datetime + "-lat:" + str(latitude) + "-lon:" + str(
            longitude)
        logging.info("Capture " + filename)

        elapsed_time = 5 - (time.time() - start_time)
        client.publish("tripcam/app/status", "sleeps")
        if elapsed_time > 0.0:
            logging.info("Sleeps " + str(elapsed_time))
            time.sleep(elapsed_time)
        else:
            logging.info("Sleeps by default with 0.1s")
            time.sleep(0.1)
        start_time = time.time()
        datetime = dt.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')

        while alive:
            while state != "run":
                logging.info("Wait for user to resume capture")
                time.sleep(0.5)
                client.publish("tripcam/app/status", "pause")
except KeyboardInterrupt:
    logging.info("stopped by user")

client.publish("tripcam/app/status", "stop")
# Close camera instance
camera.stop_preview()
#take_picture_annotate(client, "/home/camera/images/", 1920, 1080, 0.0, 0.0)
client.loop_stop()
logging.info("End of script")
