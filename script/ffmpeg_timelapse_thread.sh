#!/bin/sh

# Create the folder
PICS_FOLDER="/tmp/timelapse_trip/"
FOLDER=$(date +"%Y-%m-%d_%H-%M-%S")
mkdir -p $PICS_FOLDER/$FOLDER
cd $PICS_FOLDER/$FOLDER

# Launch the timelapse and store the images in the pic folder horodated
ffmpeg -rtsp_transport tcp -y -i "rtsp://admin:pam1249CS1110ragot&@192.168.1.23:554//h264Preview_01_main" -q:v 4 -vf fps=$2 -strftime 1 "%Y-%m-%d_%H-%M-%S.jpg"