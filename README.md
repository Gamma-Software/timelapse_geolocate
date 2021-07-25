*Date of creation: 29/03/2021*

# Timelapse Trip
Retrive the rtsp stream from a IP cam (for now) and create a timelapse that displays a map to indicate the trip progression

## Requirements
TODO

# Installation
Create a python virtual environnement: 'virtualenv .venv"
Install requirements 'pip install -r requirements.txt'
Install the configurations and service 'python3 (from the virtualenv) install.py'
Change default user and pass config in /etc/capsule/timelapse_trip/config.yaml

## Details
### Programming Language
This project is written in python and is meant to be run on a device that supports.

### Integration
We assume that the script will only be run on Linux OS
TODO

# Mosquitto publish topics
process/timelapse_trip/alive
process/timelapse_trip/last_status
