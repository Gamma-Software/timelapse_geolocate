import pynmea2
import serial
import time
import sys
import io


def read_gps_data_log():
    return_values = {"lat": 0.0, "lon": 0.0}

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
                    return_values["lat"] = nmeaobj.latitude
                    return_values["lon"] = nmeaobj.longitude
                    print(return_values)
                    break
                except pynmea2.ParseError as e:
                    print('Parse error: {}'.format(e))
                    print("Retry getting a correct NMEA data")
                    time.sleep(0.1)
                    continue
    except serial.SerialException as e:
        sys.stderr.write('Device error: {}'.format(e))
    return return_values
