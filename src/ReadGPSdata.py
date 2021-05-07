import pynmea2
import serial
import time
import sys
import io


def read_gps_data_log():
    return_values = {"lat": 0.00, "lon": 0.00}

    port = "/dev/serial0"
    try:
        # try to read a line of data from the serial port and parse
        with serial.Serial(port, 115200, timeout=1) as ser:
            print("Opening port: "+port)
            # 'warm up' with reading some input
            for i in range(5):
                print("Dry run:", ser.readline())

            sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))

            while 1:
                print("Getting NMEA data")
                try:
                    nmeaobj = pynmea2.parse(sio.readline())
                    print(nmeaobj)
                    return_values["lat"] = round(nmeaobj.latitude, 2)
                    return_values["lon"] = round(nmeaobj.longitude, 2)
                    print(return_values)
                    if return_values["lat"] != 0.00 or return_values["lon"] != 0.00:
                        break
                except pynmea2.ParseError as e:
                    print('Parse error: {}'.format(e))
                    print("Retry getting a correct NMEA data")
                    time.sleep(0.1)
                    continue
    except serial.SerialException as e:
        sys.stderr.write('Device error: {}'.format(e))
    return return_values