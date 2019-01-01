import VL53L1X
from flask import abort
#import time
import sys

rangemodes = {"none":0, "short":1, "medium":2, "long":3}
rngmode = "medium"

tof = VL53L1X.VL53L1X(i2c_bus=1, i2c_address=0x29)
tof.open() # Initialise the i2c bus and configure the sensor
tof.start_ranging(rangemodes[rngmode]) # Start ranging, 1 = Short Range, 2 = Medium Range, 3 = Long Range

def range():
    global rngmode
    distance = tof.get_distance()
    return {"distance":distance, "mode": rngmode}

def rangemode(put):
    mode = put['mode']
    global rngmode
    if mode not in rangemodes:
        abort(404, "Invalid range mode")

    rngmode = mode
    tof.stop_ranging()
    if rangemodes[mode] > 0:
        tof.start_ranging(rangemodes[mode])

