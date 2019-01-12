import pygame
from gamestate import GameState
from pilotport import Cockpit
import argparse

class DroidControl(GameState):
  def __init__(self, wndpos=pygame.Rect(0,0,640,480), fullscreen=False, scaletofit=False, address=None, camport=5001, apiport=5000):
    GameState.__init__(self)
    self._wndpos = wndpos.copy()
    self._fullscreen = fullscreen
    self._scaletofit = scaletofit
    self._init_pygame()
    self._screen = None
    self._clock = pygame.time.Clock()
    self._isopen = False
    self._droidaddress = None
    self._camport = camport
    self._apiport = apiport
    if address is not None:
      self.open(address, camport, apiport)
    self._running = False
    
  def _init_pygame(self):
    pygame.init()
    pygame.mixer.quit()
    pygame.event.set_allowed(None)
    pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP, pygame.MOUSEBUTTONDOWN])
    
  def open(self, address, camport=5001, apiport=5000):
    'open connections to videodroid'
    self._droidaddress = address
    self._camport = camport
    self._apiport = apiport
    self.set_state("app_camconnection", (address,camport))
    self.set_state("app_apiconnection", (address,apiport))
    
  def close(self):
    'Close all connections to videodroid'
    pass
    
  def run(self):
    try:
      if self._fullscreen:
        modes = pygame.display.list_modes(0,pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE)
        if len(modes) == 0:
          print("DEBUG - no hardware fullscreen modes supported")
          quit()
        self._screen = pygame.display.set_mode(modes[0],pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE)
        if self._scaletofit:
          # Update window size if fullscreen and scale flag set. 
          self._wndpos.width = self._screen.get_width()
          self._wndpos.height = self._screen.get_height()
        else:
          self._wndpos.centerx = self._screen.get_rect().centerx
          self._wndpos.centery = self._screen.get_rect().centery
      else:
        self._screen = pygame.display.set_mode(self._wndpos.size)
              
      cockpitview = Cockpit(wndpos=self._wndpos)
      
      self._running = True
      while self._running:
        for evt in pygame.event.get():
          if evt.type == pygame.KEYDOWN and evt.key == pygame.K_ESCAPE:
            self._running = False
          elif evt.type == pygame.MOUSEBUTTONDOWN: # Pass on all mouse presses to the cockpit view
            cockpitview.event(evt)
          elif evt.type == pygame.QUIT: 
            self._running = False
          elif evt.type == pygame.KEYUP:
            if evt.key == pygame.K_l: # Light toggle
              light_state = self.get_state("light_ctrl")
              if light_state is None or not light_state:
                self.set_state("light_ctrl", True)
              else:
                self.set_state("light_ctrl", False)
            elif evt.key == pygame.K_r:
              range_state = self.get_state("ranging_ctrl")
              if range_state is None or not range_state:
                self.set_state("ranging_ctrl", True)
              else:
                self.set_state("ranging_ctrl", False)
            elif evt.key == pygame.K_v:
              if evt.mod & pygame.KMOD_SHIFT:
                self.set_state("cam_online", True)
              else:
                self.set_state("cam_online", False)
            elif evt.key == pygame.K_w:
              self.set_state("move_forward", True)
              
            elif evt.key == pygame.K_s:
              self.set_state("move_stop", True)
    
            elif evt.key == pygame.K_x:
              self.set_state("move_back", True)
              
           # Left and right directions are modifiers to fwd, back or stop
            if evt.key == pygame.K_a:
              self.set_state("move_left", True)
              
            elif evt.key == pygame.K_d:
              self.set_state("move_right", True)
              
                
        cockpitview.draw()
        self._screen.blit(cockpitview.screen, cockpitview.get_rect(), special_flags = 0)
        pygame.display.flip()
        self._clock.tick(30)
        
    finally:
      self._running = False
      self.close()
      pygame.quit()
      cockpitview.close()
      
      
if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('address', type=str, help='IP or hostname', metavar='IP')
  args = parser.parse_args()
  print ("Connecting to " + args.address + "...")
  app = DroidControl(fullscreen=True, scaletofit=True)
  app.open(args.address)
  app.run()
      