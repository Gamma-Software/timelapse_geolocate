import time
import sys
from picamera import PiCamera
import picamera
from ReadGPSdata import read_gps_data_log
from time import sleep
import datetime as dt
import itertools


def take_picture_annotate(picture_cache_location, width, height, latitude, longitude):
    camera = PiCamera()
    camera.resolution = (width, height)
    #camera.awb_mode = "greyworld"
    camera.annotate_background = picamera.Color('black')
    text = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "-lat:" + str(latitude) + "-lon:" + str(longitude)
    # Display long text
    # camera.annotate_text = ' ' * 31
    camera.annotate_text = text
    #for c in itertools.cycle(text):
    #    camera.annotate_text = camera.annotate_text[1:31] + c
    #    sleep(0.1)

    # Warm up the raspberry camera
    print("Warm up")
    camera.start_preview()
    sleep(2)
    # Take the picture
    camera.capture(picture_cache_location + dt.datetime.now().strftime('%Y%m%d-%H:%M:%S') + "-" + str(latitude) + "-" + str(longitude) + ".png")
    print("Capture " + picture_cache_location + dt.datetime.now().strftime('%Y%m%d-%H:%M:%S') + "-" + str(latitude) + "-" + str(longitude) + ".png")
    # Close camera instance
    camera.stop_preview()

try:
    gps_data = read_gps_data_log()
    take_picture_annotate("/home/camera/images/", 1920, 1080, gps_data["lat"], gps_data["lon"])
except KeyboardInterrupt:
    sys.exit()
