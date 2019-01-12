#!/usr/bin/python

import smbus

i2cbus = smbus.SMBus(1)
try:
  print("Battery Charge is {}%".format(i2cbus.read_byte_data(0x36,0x04)))
except:
  print("Cannot connect to Fuel Gauge, hardware not available")
