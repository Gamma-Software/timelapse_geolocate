import io
import sys

import pynmea2
import serial
import time
import logging
import datetime as dt
import paho.mqtt.client as mqtt

logging.basicConfig(
    filename="/home/pi/log/parse" + dt.datetime.now().strftime("%Y%m%d-%H%M%S") + ".log",
    filemode="a", level=logging.DEBUG, format="%(asctime)s %(levelname)s:%(message)s", datefmt='%m/%d/%Y %I:%M:%S %p')

client = mqtt.Client()
logging.info("Connect to localhost broker")
connected = False
client.connect("localhost", 1883, 60)

port = "/dev/serial0"
while True:
    client.publish("tripcam/app/alive", False)
    try:
        with serial.Serial(port, 115200, timeout=1) as ser:
            logging.info("Opening port: "+port)
            # 'warm up' with reading some input
            for i in range(5):
                logging.info("Dry run:"+str(ser.readline()))
            sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser), encoding='ascii', errors='ignore')
            last_valid_nmea = pynmea2.parse("$GPGGA,184353.07,1929.045,S,02410.506,E,1,04,2.6,100.00,M,-33.9,M,,0000*6D")
            log = ""
            while True:
                try:
                    nmeaobj = pynmea2.parse(sio.readline())
                    if isinstance(nmeaobj, pynmea2.types.RMC) or isinstance(nmeaobj, pynmea2.types.GGA):
                        data = nmeaobj
                        if not data.is_valid:
                            logging.info("GPS is not fixed")
                            client.publish("gps/fixed", False)
                        else:
                            client.publish("gps/fixed", True)
                            try
                            if isinstance(last_valid_nmea, pynmea2.types.GGA):
                                client.publish("gps/timestamp", dt.datetime.now().timestamp())
                                client.publish("gps/latitude", round(data.latitude, 4))
                                client.publish("gps/longitude", round(data.longitude, 4))
                                client.publish("gps/speed", round(float(data.data[6]) * 1.852, 2))
                                client.publish("gps/route", data.data[7])
                            if isinstance(last_valid_nmea, pynmea2.types.RMC):
                                client.publish("gps/altitude", data.altitude)
                            last_valid_nmea = nmeaobj
                    logging.debug(repr(nmeaobj))
                except pynmea2.ParseError as e:
                    logging.warning('Parse error: {}'.format(e))
                    logging.warning("Retry getting a correct NMEA data")
                    pass
                except AttributeError as e:
                    logging.warning("Erreur sur attribut {}".format(e))
                    pass
                except KeyboardInterrupt:
                    logging.info("Stop script")
                    client.publish("tripcam/app/alive", False)
                    client.disconnect()
                    sys.exit(0)
                client.publish("tripcam/app/alive", True)
                time.sleep(1 / 100)
            except serial.SerialException as e:
            print('Device error: {}'.format(e))
            logging.error('Device error: {}'.format(e))
            continue
        logging.info("Sleeps for 1s to open serial")
        time.sleep(1)
