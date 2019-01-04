import VL53L1X
from flask import abort
import sys
import threading
import serial

serialport = '/dev/serial0'

rangemodes = {"none":0, "short":1, "medium":2, "long":3}
rngmode = "medium"

# Need a mutex lock to protect the single hardware instance on i2c
lock = threading.Lock()
# Lock required for the serial resource
seriallock = threading.Lock()

lock.acquire()
tof = VL53L1X.VL53L1X(i2c_bus=1, i2c_address=0x29)
tof.open() # Initialise the i2c bus and configure the sensor
tof.start_ranging(rangemodes[rngmode]) # Start ranging, 1 = Short Range, 2 = Medium Range, 3 = Long Range
lock.release()

seriallock.acquire()
ser = serial.Serial(port=serialport, timeout=2.0, write_timeout=2.0)
seriallock.release()

def range():
    global rngmode
    lock.acquire()
    distance = tof.get_distance()
    lock.release()
    return {"distance":distance, "mode": rngmode}

def rangemode(put):
    mode = put['mode']
    global rngmode
    if mode not in rangemodes:
        abort(404, "Invalid range mode")

    rngmode = mode
    lock.acquire()

    tof.stop_ranging()
    if rangemodes[mode] > 0:
        tof.start_ranging(rangemodes[mode])

    lock.release()

def move(put):
    global ser
    if not ser.is_open:
        # Try to open the port again
        seriallock.acquire()
        ser = serial.Serial(port=serialport, timeout=2.0, write_timeout=2.0)
        seriallock.release()
        if not ser.is_open:
          abort(500, "Serial comms port unavailable")

    serial_command = put['command'] + " " + str(put['speed']) + "\r\n"
    bytestr = serial_command.encode('ascii')
    seriallock.acquire()
    ser.write(bytestr)
    response = ser.readline()
    seriallock.release()

def getmove():
    global ser
    if not ser.is_open:
        # Try to open the port again
        seriallock.acquire()
        ser = serial.Serial(port=serialport, timeout=2.0, write_timeout=2.0)
        seriallock.release()
        if not ser.is_open:
          abort(500, "Serial comms port unavailable")

    seriallock.acquire()
    ser.write(b'cmd\r\n')
    response = ser.readline().strip()
    seriallock.release()

    # TO DO: implement cmd with last set speed
    return {"command": response, "speed": 255}
