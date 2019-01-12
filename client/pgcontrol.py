import pygame
import time

class Clock(object):
  def __init__(self, timeout = None, fn=None, immediate=True):
    self._t = 0
    self._fn = None
    self._sectimer = 0
    if timeout is not None:
      self.set_timer(timeout, fn, immediate)

  def set_timer(self, timeout, fn=None, immediate=True):
    if not immediate:
      self._t = time.time()
    self._sectimer = timeout
    self._fn = fn

  def tick(self):
    t = time.time()
    if self._t + self._sectimer <= t:
      self._t = t
      if self._fn is not None:
        self._fn()
      return True
    return False
    
class PgClock(object):
  def __init__(self):
    self._clock = pygame.time.Clock()
    self._frame_t = 0
    self._mtimer = 0
    self._ontick = None

  def set_timer(self, millis, fn=None):
    self._mtimer = millis
    self._ontick = fn
    self._frame_t = 0

  def tick(self):
    ret = False
    self._frame_t += self._clock.get_rawtime()
    if self._frame_t > self._mtimer:
      ret = True
      self._frame_t = 0
      if self._ontick :
        self._ontick()
    self._clock.tick()

    return ret
        
class ControlWnd(object):
  def __init__(self, wndpos=pygame.Rect(0,0,1,1)):
    self._wndpos = wndpos.copy() # Absolute Rect position to the parent controlwnd
    self.screen = pygame.Surface(wndpos.size).convert()
    self._controls = []
    self._ctlfocus = False
  
  def add_control(self, ctrl):
    self._controls.append(ctrl)
    
  def event(self, evt):
    'Passes an event from the pygame event queue'
    localevt = self._localise_event(evt)
    if evt.type == pygame.MOUSEBUTTONDOWN or evt.type == pygame.MOUSEBUTTONUP or evt.type == pygame.MOUSEMOTION:
      if self._wndpos.collidepoint(evt.pos):
        # Set focus if not already set
        if not self._ctlfocus:
          self._ctlfocus = True
          self.focused()
        # Trigger the local event
        if not self.local_event(localevt):
          for ctl in self._controls:
            ctl.event(localevt)
      else:
        # Press isn't in control. Change focus
        if self._ctlfocus:
          self._ctlfocus = False
          self.unfocused()
    else: # Key presses or other events
      if not self.local_evnt(localevt):
        for ctl in self._controls:
          ctl.event(localevt)
    
  @property
  def focus(self):
    return self_ctlfocus
    
  @focus.setter
  def focus(self, focused):
    self._ctlfocus = focused
    if focused:
      self.focused()
    else:
      self.unfocused()
    
  def unfocused(self):
    'Triggered when control loses focus'
    pass
    
  def focused(self):
    'Triggered when control gains focus'
    pass
    
  def local_event(self,evt):
    'event adjusted for the control. Evt is a copy and can be updated. Return True if handled, or False to pass to child control'
    return False

  def _draw_controls(self):
    for ctl in self._controls:
      ctl.draw()
    
  def draw(self):
    'All controls draw in this function'
    pass
    
  def _localise_event(self,evt):
    evtnew = pygame.event.Event(evt.type, evt.__dict__.copy())
    if evt.type == pygame.MOUSEBUTTONDOWN or evt.type == pygame.MOUSEBUTTONUP or evt.type == pygame.MOUSEMOTION:
      # normalise the press to this screen
      evtnew.pos = (evt.pos[0] - self._wndpos.x, evt.pos[1] - self._wndpos.y)
    return evtnew
    
  def get_rect(self):
    return self._wndpos.copy()