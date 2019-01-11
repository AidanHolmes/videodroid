import VL53L1X
from flask import abort
import sys
import threading
import serial
import RPi.GPIO as gpio
import smbus2

led_pin = 18
serialport = '/dev/serial0'

rangemodes = {"none":0, "short":1, "medium":2, "long":3}
rngmode = "medium"

# Need a mutex lock to protect the single hardware instance on i2c
lock = threading.Lock()
# Lock required for the serial resource
seriallock = threading.Lock()

lock.acquire()
i2cbus = smbus2.SMBus(1)

tof = VL53L1X.VL53L1X(i2c_bus=1, i2c_address=0x29)
tof.open() # Initialise the i2c bus and configure the sensor
tof.start_ranging(rangemodes[rngmode]) # Start ranging, 1 = Short Range, 2 = Medium Range, 3 = Long Range
lock.release()

seriallock.acquire()
ser = serial.Serial(port=serialport, timeout=2.0, write_timeout=2.0)
seriallock.release()

gpio.setwarnings(False)
gpio.setmode(gpio.BCM)
gpio.setup(led_pin, gpio.OUT)

def battery():
    global i2cbus
    with lock:
        try:
            return {"charge": i2cbus.read_byte_data(0x36,0x04)}
        except IOError:
            abort(503, "Cannot query battery level")
def leds(put):
    global led_pin
    on = True
    if put['turnon'] <= 0:
        on = False
    gpio.output(led_pin, on)
    
def range():
    global rngmode
    with lock:
        distance = tof.get_distance()
    return {"distance":distance, "mode": rngmode}

def rangemode(put):
    mode = put['mode']
    global rngmode
    global tof
    if mode not in rangemodes:
        abort(404, "Invalid range mode")

    rngmode = mode

    with lock:
        tof.stop_ranging()
        if rangemodes[mode] > 0:
            tof.start_ranging(rangemodes[mode])

def move(put):
    global ser
    if not ser.is_open:
        # Try to open the port again
        with seriallock:
            ser = serial.Serial(port=serialport, timeout=2.0, write_timeout=2.0)
        if not ser.is_open:
            abort(500, "Serial comms port unavailable")

    serial_command = put['command'] + " " + str(put['speed']) + "\r\n"
    bytestr = serial_command.encode('ascii')
    with seriallock:
        ser.write(bytestr)
        response = ser.readline()

def getmove():
    global ser
    if not ser.is_open:
        # Try to open the port again
        with seriallock:
            ser = serial.Serial(port=serialport, timeout=2.0, write_timeout=2.0)
        if not ser.is_open:
          abort(500, "Serial comms port unavailable")

    with seriallock:
        ser.write(b'cmd\r\n')
        response = ser.readline().strip()

    # TO DO: implement cmd with last set speed
    return {"command": response, "speed": 255}
