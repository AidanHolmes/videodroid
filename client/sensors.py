import threading
import requests
import time

class Lights(object):
  def __init__(self, address=None, port=5000):
    self._address = address
    self._port = port
    self._apiurl = ""
    if address is not None:
      self.open(address, port)
      
  def open(self, address, port=5000):
    if len(self._apiurl) > 0:
      # Already open. Close and update URL
      self.close()
    self._apiurl = "http://" + address + ":" + str(port) + "/droid/lights"
    
  def switch(self, onoff):
    val = 1
    if not onoff:
      val = 0
    try:
      r = requests.put(self._apiurl, json={'turnon':val})
      if not r.status_code == requests.codes.ok:
        print ("DEBUG - light control failed: {}".format(r.status_code))
    except requests.exceptions.ConnectionError:
      # Failed to connect. 
      print("DEBUG - move API error, cannot connect")
      
class Battery(object):
  def __init__(self, address=None, port=5000):
    self._address = address
    self._port = port
    self._apiurl = ""
    if address is not None:
      self.open(address, port)
      
  def open(self, address, port=5000):
    if len(self._apiurl) > 0:
      # Already open. Close and update URL
      self.close()
    self._apiurl = "http://" + address + ":" + str(port) + "/droid/battery"
    
  def is_available(self):
    # Query the droid and check response code
    # 503 returned if charge hardware unavailable
    try:
      r = requests.get(self._apiurl)
      if r.status_code == requests.codes.ok:
        return True
      else:
        print ("DEBUG - battery query failed: {}".format(r.status_code))
    except requests.exceptions.ConnectionError:
      # Failed to connect.
      print("DEBUG - battery API error, cannot connect")
      
    return False
    
  def charge(self):
    # Query the droid for battery charge information
    charge = 0
    try:
      r = requests.get(self._apiurl)
      if r.status_code == requests.codes.ok:
        vals = r.json() 
        charge = vals['charge']
      else:
        print ("DEBUG - battery query failed: {}".format(r.status_code))
    except requests.exceptions.ConnectionError:
      # Failed to connect.
      print("DEBUG - battery API error, cannot connect")

    return charge
    
class Drive(object):
  def __init__(self, address=None, port=5000):
    self._address = address
    self._port = port
    self._apiurl = ""
    self._lastmove = ('',0)
    if address is not None:
      self.open(address, port)
      
  def open(self, address, port=5000):
    if len(self._apiurl) > 0:
      # Already open. Close and update URL
      self.close()
    self._apiurl = "http://" + address + ":" + str(port) + "/droid/move"

  def close(self):
    self._apiurl = ""

  @property
  def move(self):
    # Query the droid for last move instruction
    try:
      r = requests.get(self._apiurl)
      if r.status_code == requests.codes.ok:
        vals = r.json() 
        self._lastmove = (vals['command'], vals['speed'])
      else:
        print ("DEBUG - move query failed: {}".format(r.status_code))
    except requests.exceptions.ConnectionError:
      # Failed to connect. Do not update last move, just use cached info from last move
      print("DEBUG - move API error, cannot connect")

    return self._lastmove
    
  @move.setter
  def move(self, val):
    try:
      r = requests.put(self._apiurl, json={'command':val[0], 'speed':val[1]})
      if r.status_code == requests.codes.ok:
        self._lastmove = val
      else:
        print ("DEBUG - move instruction failed: {}".format(r.status_code))
    except requests.exceptions.ConnectionError:
      # Failed to connect. Do not update last move, just use cached info from last move
      print("DEBUG - move API error, cannot connect")

  def standby(self):
    try:
      r = requests.put(self._apiurl, json={'command':'standby', 'speed':0})
      if not r.status_code == requests.codes.ok:
        print ("DEBUG - move instruction failed: {}".format(r.status_code))
    except requests.exceptions.ConnectionError:
      # Failed to connect. Do not update last move, just use cached info from last move
      print("DEBUG - move API error, cannot connect")
      
class RangeSensor(object):
  MODES=["none", "short", "medium", "long"]
  def __init__(self, address=None, port=5000):
    self._address = address
    self._port = port
    self._mode = 'none'
    self._distancemm = 0
    self._thread = None
    self._ranging = False
    self._apiurl = ""
    if address is not None:
      self.open(address, port)

  def open(self, address, port=5000):
    'Setup the connection URL based on address and port'
    if len(self._apiurl) > 0:
      # Already open. Stop activity and change URL
      self.close()
    self._apiurl = "http://" + address + ":" + str(port) + "/droid/range"

  def close(self):
    self.stop_ranging()
    self._apiurl = ""
    
  @property
  def distance_mm(self):
    return self._distancemm
    
  @property
  def mode(self):
    # Returns the last known mode set for the sensor
    return self._mode
    
  @mode.setter
  def mode(self, val):
    # Range mode may not change and soft fail. Function cannot guarantee a change
    if len(self._apiurl) > 0:
      try:
        r = requests.put(self._apiurl, json={'mode':val})
        if r.status_code == requests.codes.ok:
          # Update the mode successfully set by the API call
          self._mode = val
        else:
          print("DEBUG - Cannot change mode to {}".format(val))
      except requests.exceptions.ConnectionError:
        print("DEBUG - Cannot connect to the API server to change ranging mode")
  
  def start_ranging(self):
    'Start continuous query of range in a separate thread'
    if len(self._apiurl) == 0 or self._ranging:
      # Not open or already running a ranging thread
      return False
    self._ranging = True
    self._thread = threading.Thread(target=self._do_ranging)
    self._thread.start()
    return True
    
  def stop_ranging(self):
    'Stop the continuous query of range and close the thread'
    self._ranging = False
    if self._thread is None: 
      return True # No thread running
    self._thread.join(10.0)
    if self._thread.is_alive():
      print("DEBUG - ranging still running in thread. Trying again...")
      self._thread.join(10.0)
      if self._thread.is_alive():
        print("DEBUG - ranging thread not terminating, something has gone wrong with the API call")
        return False
    return True
    
  def _do_ranging(self):
    while self._ranging:
      try:
        r = requests.get(self._apiurl)
        if r.status_code == requests.codes.ok:
          vals = r.json() 
          self._distancemm = vals['distance']
          self._mode = vals['mode']
        else:
          print ("DEBUG - ranging query failed: {}".format(r.status_code))
        time.sleep(0.5)
      except requests.exceptions.ConnectionError:
        # Failed to connect. Try again in 10 sec
        print("DEBUG - cannot connect to API for range information")
        time.sleep(10)