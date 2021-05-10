import pynmea2
import serial
import time
import sys
import io
import logging

def read_gps_data_log():
    return_values = {"lat": 0.00, "lon": 0.00}

    port = "/dev/serial0"
    over = 0
    while True:
        over = over + 1
        if over >= 5:
            print("After " + str(over) + " tries, can’t open /dev/serial0")
            logging.error("After " + str(over) + " tries, can’t open /dev/serial0")
            return return_values
        try:
            # try to read a line of data from the serial port and parse
            with serial.Serial(port, 115200, timeout=1) as ser:
                print("Opening port: "+port)
                logging.info("Opening port: "+port)
                # 'warm up' with reading some input
                for i in range(5):
                    print("Dry run:", ser.readline())
                    logging.info("Dry run:" + repr(ser.readline()))

                sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser), encoding='ascii', errors='ignore')

                while 1:
                    print("Getting NMEA data")
                    logging.info("Getting NMEA data")
                    try:
                        nmeaobj = pynmea2.parse(sio.readline())
                        print(nmeaobj)
                        logging.info(nmeaobj)
                        if isinstance(nmeaobj, pynmea2.types.RMC) and nmeaobj.latitude != 0.0 and nmeaobj.longitude != 0.0:
                            logging.debug(str(type(nmeaobj.latitude)) + str(nmeaobj.latitude))
                            logging.debug(str(type(nmeaobj.longitude)) + str(nmeaobj.longitude))
                            return_values["lat"] = round(nmeaobj.latitude, 4)
                            return_values["lon"] = round(nmeaobj.longitude, 4)
                            print(return_values)
                            logging.info(return_values)
                            break
                        else:
                            continue
                    except pynmea2.ParseError as e:
                        print('Parse error: {}'.format(e))
                        print("Retry getting a correct NMEA data")
                        logging.warning('Parse error: {}'.format(e))
                        time.sleep(0.1)
                        continue
                return return_values
        except serial.SerialException as e:
            print('Device error: {}'.format(e))
            logging.error('Device error: {}'.format(e))
            continue
    return return_values
