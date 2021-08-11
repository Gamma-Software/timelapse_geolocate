#!/bin/sh

# Create the folder
PICS_FOLDER="/tmp/timelapse_trip/"
FOLDER=$(date +"%Y-%m-%d_%H-%M-%S")
mkdir -p $PICS_FOLDER/$FOLDER
cd $PICS_FOLDER/$FOLDER

# TODO refactor to avoid using shell script
# Launch the timelapse and store the images in the pic folder horodated
ffmpeg -rtsp_transport tcp -y -i "rtsp://admin:pam1249CS1110ragot&@camera:554//h264Preview_01_main" -q:v 4 -vf fps=$1 -strftime 1 "%Y-%m-%d_%H-%M-%S.jpg"

# https://ffmpeg.org/ffmpeg.html#Synopsis
#ffmpeg -y -i "rtsp://admin:pam1249CS1110ragot&@192.168.1.23:554//h264Preview_01_main" -rtsp_transport tcp image%03d.jpg
#ffmpeg -rtsp_transport tcp -y -i "rtsp://admin:pam1249CS1110ragot&@192.168.1.23:554//h264Preview_01_main" -frames:v image%03d.jpg
#ffmpeg -rtsp_transport tcp -y -i "rtsp://admin:pam1249CS1110ragot&@192.168.1.23:554//h264Preview_01_main" image%03d.jpg
#ffmpeg -rtsp_transport tcp -y -i "rtsp://admin:pam1249CS1110ragot&@192.168.1.23:554//h264Preview_01_main" -vf fps=1  image%03d.jpg
#ffmpeg -rtsp_transport tcp -y -i "rtsp://admin:pam1249CS1110ragot&@192.168.1.23:554//h264Preview_01_main" -vf fps=1 -strftime 1 "%Y-%m-%d_%H-%M-%S.jpg"
#ffmpeg -rtsp_transport tcp -y -i "rtsp://admin:pam1249CS1110ragot&@192.168.1.23:554//h264Preview_01_main" -q:v 4 -vf fps=1 -strftime 1 "%Y-%m-%d_%H-%M-%S.jpg"
#ffmpeg -rtsp_transport tcp -y -i "rtsp://admin:pam1249CS1110ragot&@192.168.1.23:554//h264Preview_01_main" -q:v 4 -vf fps=1 -strftime 1 -strftime_mkdir 1 "%Y%m%d_%H%M%S/%Y-%m-%d_%H-%M-%S.jpg"