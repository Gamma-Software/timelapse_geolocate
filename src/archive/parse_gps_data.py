import io
import os
import yaml
import sys
import pynmea2
import serial
import time
import logging
import datetime as dt
import paho.mqtt.client as mqtt


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
connected = False
logging.basicConfig(
    filename="/var/log/timelapse_generator/parse_gps_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S") + ".log",
    filemode="a",
    level=logging.DEBUG if conf.debug else logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt='%m/%d/%Y %I:%M:%S %p')

# ----------------------------------------------------------------------------------------------------------------------
# Initiate MQTT variables
# ----------------------------------------------------------------------------------------------------------------------
client = mqtt.Client()
logging.info("Connect to localhost broker")
client.connect("localhost", 1883, 60)

while not client.is_connected():
    logging.info("Waiting for the broker connection")
    time.sleep(1)

# ----------------------------------------------------------------------------------------------------------------------
# Main loop
# ----------------------------------------------------------------------------------------------------------------------
client.publish("gps/process/alive", True)
while True:
    try:
        with serial.Serial(conf["gps_serial_port"], conf["gps_serial_baudrate"], timeout=1) as ser:
            logging.info("Opening port: " + conf["gps_serial_port"] + " at speed: " + conf["gps_serial_baudrate"])
            # 'warm up' with reading some input
            for i in range(5):
                logging.info("Dry run:"+str(ser.readline()))
            sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser), encoding='ascii', errors='ignore')
            last_valid_nmea = pynmea2.parse("$GPGGA,184353.07,1929.045,S,02410.506,E,1,04,2.6,100.00,M,-33.9,M,,0000*6D")
            while True:
                try:
                    nmeaobj = pynmea2.parse(sio.readline())
                    logging.debug(repr(nmeaobj))
                    if isinstance(nmeaobj, pynmea2.types.RMC) or isinstance(nmeaobj, pynmea2.types.GGA):
                        data = nmeaobj
                        if not data.is_valid:
                            logging.warning("GPS is not fixed")
                            client.publish("gps/fixed", False)
                        else:
                            client.publish("gps/fixed", True)
                            try:
                                if isinstance(last_valid_nmea, pynmea2.types.GGA):
                                    client.publish("gps/timestamp", dt.datetime.now().timestamp())
                                    client.publish("gps/latitude", round(data.latitude, 4))
                                    client.publish("gps/longitude", round(data.longitude, 4))
                                    client.publish("gps/speed", round(float(data.data[6]) * 1.852, 2))
                                    client.publish("gps/route", data.data[7])
                                if isinstance(last_valid_nmea, pynmea2.types.RMC):
                                    client.publish("gps/altitude", data.altitude)
                                last_valid_nmea = nmeaobj
                            except AttributeError as e:
                                logging.warning("Error on attribute {}".format(e))
                                pass
                except pynmea2.ParseError as e:
                    logging.warning('Parse error: {}'.format(e))
                    logging.warning("Retry getting a correct NMEA data")
                    pass
                except KeyboardInterrupt:
                    logging.info("Stop script")
                    client.publish("gps/process/alive", False)
                    client.disconnect()
                    sys.exit(0)
                client.publish("gps/process/alive", True)
                time.sleep(1 / 50)
    except serial.SerialException as e:
        logging.error('Device error: {}'.format(e))
        client.publish("gps/process/alive", False)
        sys.exit('Device error: {}'.format(e))
