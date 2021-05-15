from picamera import PiCamera
import picamera
from time import sleep
import datetime as dt
import logging
import time
import os

from paho.mqtt import client as mqtt


def on_connect(client, userdata, flags, rc):  # The callback for when the client connects to the broker
    logging.info("Connected with result code {0}".format(str(rc)))  # Print result of connection attempt
    client.subscribe("gps/latitude")  # Subscribe to the topic “digitest/test1”, receive any messages published on it
    client.subscribe("gps/longitude")  # Subscribe to the topic “digitest/test1”, receive any messages published on it
    client.subscribe("gps/timestamp")  # Subscribe to the topic “digitest/test1”, receive any messages published on it
    client.subscribe("tripcam/app/fpm")
    client.subscribe("tripcam/app/alive")



def on_message(client, userdata, msg):  # The callback for when a PUBLISH message is received from the server.
    global latitude, longitude, timestamp, alive, fpm
    data = msg.payload.decode("utf-8")
    if msg.topic == "gps/timestamp":
        timestamp = float(data)
    if msg.topic == "gps/latitude":
        latitude = float(data)
    if msg.topic == "gps/longitude":
        longitude = float(data)
    if msg.topic == "tripcam/app/alive":
        alive = bool(data)
    if msg.topic == "tripcam/app/fpm":
        fpm = int(data)


def main():
    alive=False
    timestamp = 0.0
    latitude = 0.0
    longitude = 0.0
    fpm = 12 # 5s

    picture_cache_location = "/home/camera/images/"

    # Create a folders in /home/camera/
    # define the name of the directory to be created
    datetime = dt.datetime.now().strftime('%Y%m%d_%H%M%S')
    root_path = "/home/camera/"+datetime
    images_path = "/home/camera/"+datetime+"/images"
    log_path = "/home/camera/"+datetime+"/log"
    access_rights = 0o755
    try:
        os.mkdir(root_path, access_rights)
    except OSError:
        print ("Creation of the directory %s failed" % root_path)
    else:
        print ("Successfully created the directory %s" % root_path)
    try:
        os.mkdir(images_path, access_rights)
    except OSError:
        print("Creation of the directory %s failed" % images_path)
    else:
        print("Successfully created the directory %s" % images_path)
    try:
        os.mkdir(log_path, access_rights)
    except OSError:
        print("Creation of the directory %s failed" % log_path)
    else:
        print("Successfully created the directory %s" % log_path)

    logging.basicConfig(
        filename=log_path+"/capture.log",
        filemode="a", level=logging.DEBUG, format="%(asctime)s %(levelname)s:%(message)s", datefmt='%m/%d/%Y %I:%M:%S %p')

    logging.info("Create mqtt client")
    client = mqtt.Client("my_id")  # Create instance of client with client ID “digi_mqtt_test”
    logging.info("trying to connect to localhost")
    client.on_connect = on_connect  # Define callback function for successful connection
    client.on_message = on_message  # Define callback function for receipt of a message
    client.connect("localhost")
    client.loop_start()
    client.publish("tripcam/app/status", "started")

    while not alive:
        logging.info("Wait 1s for connection to publisher")
        sleep(1.0)

    camera = PiCamera()
    camera.resolution = (1280, 720)
    camera.annotate_background = picamera.Color('black')

    # Warm up the raspberry camera
    print("Warm up")
    logging.info("Warming up")
    camera.start_preview()
    sleep(2.0)
    while alive:
        start_time = time.time()
        try:
            datetime = dt.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            client.publish("tripcam/app/status", "take picture")
            # Take the picture
            camera.annotate_text = datetime + "_lat:" + str(latitude) + "_lon:" + str(longitude)
            camera.capture(images_path + "/" + datetime + "_" + str(latitude) + "_" + str(longitude) + ".jpg")
            logging.info("Capture " + images_path + "/" + datetime + "_" + str(latitude) + "_" + str(longitude) + ".jpg")

            elapsed_time = 60/fpm - (time.time() - start_time)
            if elapsed_time > 0.0:
                logging.info("Sleeps "+str(elapsed_time))
                time.sleep(elapsed_time)
            else:
                logging.info("Sleeps by default with 0.1s")
                time.sleep(0.1)
        except KeyboardInterrupt:
            break
            # Close camera instance
    client.publish("tripcam/app/status", "stop")
    camera.stop_preview()
    #take_picture_annotate(client, "/home/camera/images/", 1920, 1080, 0.0, 0.0)
    client.loop_stop()