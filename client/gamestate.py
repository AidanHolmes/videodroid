import threading

class GameState(object):
  observers = []
  gamestate = {}
  lock = threading.Lock()
  
  def __init__(self):
    GameState._add(self)
    
  def __del__(self):
    GameState._del(self)
    
  @staticmethod
  def _add(obj):
    if obj not in GameState.observers:
      GameState.observers.append(obj)
      
  @staticmethod
  def _del(obj):
    try: 
      GameState.observers.remove(obj)
    except ValueError:
      pass
  
  def get_state(self, param):
    val = None 
    try:
      GameState.lock.acquire()
      val = GameState.gamestate[param]
    except KeyError:
      pass
    finally:
      GameState.lock.release()
      
    return val
    
  def set_state(self, param, value):
    try:
      GameState.lock.acquire()
      GameState.gamestate[param] = value
    finally:
      GameState.lock.release()
      
    for o in GameState.observers:
      o.state_change(param, value)
 
  def state_change(self, param, value):
    pass