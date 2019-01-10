import pygame
import cv2
import threading
from gamestate import GameState
from pgcontrol import ControlWnd, PgClock

class Offline(ControlWnd):
  def __init__(self, bgcol=(0,0,0), **args):
    ControlWnd.__init__(self, **args)
    self._startupsequence = True
    self._bgcolour = bgcol
    self._clock = PgClock()
    self._cursorblink = PgClock()
    self._sequencetext = []
    self._sequencetext.append("Frickin' Lasers: Online")
    self._sequencetext.append("Camera         : Offline")
    self._sequencetext.append("Motors         : Online")
    self._sequencetext.append("")
    self._sequencetext.append("Welcome to Video Droid!")
    self._cursorpos = 0
    self._linepos = 0
    #self._font = pygame.font.Font(None, 30)
    self._font = pygame.font.SysFont('droidsansmono', 15)
    self._cursorblink.set_timer(250)
    self._showcursor = True ;
    
  def connectingvideo(self, state):
    if state:
      self._sequencetext = []
      self._sequencetext.append("Connecting to camera...")
    else: 
      self._sequencetext = []
      self._sequencetext.append("Disconnected...")
    self._linepos = 0
    self._cursorpos = 0
    self._clock.set_timer(40)
    
  def draw(self):
    self.screen.fill(self._bgcolour)
    newlineat = 0
    screenpos = pos = self.screen.get_rect()
    
    if self._cursorblink.tick():
      self._showcursor = not self._showcursor
    
    if self._clock.tick():
      if self._linepos < len(self._sequencetext):
        if self._cursorpos == 0:
          self._clock.set_timer(40)
        self._cursorpos += 1 
        if self._cursorpos >= len(self._sequencetext[self._linepos]):
          self._clock.set_timer(1500)
          if self._linepos < len(self._sequencetext)-1:
            self._linepos += 1
            self._cursorpos = 0
          
    for l in range(self._linepos): 
      txt = self._font.render(self._sequencetext[l], 1, (255,255,255))
      pos = txt.get_rect(left=screenpos.left, top = screenpos.top+newlineat)
      self.screen.blit(txt, pos)
      newlineat += self._font.get_height()
      
    if self._cursorpos > 0:   
      txt = self._font.render(self._sequencetext[self._linepos][0:self._cursorpos], 1, (255,255,255))      
      pos = txt.get_rect(left=screenpos.left, top = screenpos.top+newlineat)
      self.screen.blit(txt, pos)
    else:
      newlineat -= self._font.get_height()

    if self._showcursor:
      pygame.draw.rect(self.screen, (255,255,225), pygame.Rect(pos.right, pos.top, 10, self._font.get_ascent()), 0)
  
class VideoStream(object):
  def __init__(self, address=None, port=5001):
    self._cam = cv2.VideoCapture()
    self._isopen = False
    if address is not None:
      self.open(address, port)
      
  def open(self, address, port):
    'Open the video stream'
    if self._isopen:
      self.close()
      
    self._cam.open("tcp://" + address + ":" + str(port))
    if not self._cam.isOpened():
      print ("DEBUG - Cannot open video stream")
      return False
    
    self._isopen = True
    return True
  
  def close(self):
    'Close the video stream'
    if self._isopen:
      self._cam.release()
      self._isopen = False
      
  def getimage(self):
    'Gets an image from the video stream and returns a pygame surface image'
    # TO DO: Check read return. Handle disconnects
    ret, image= self._cam.read()
    if not ret: 
      return None
    return pygame.image.frombuffer(image.tostring()[::-1], image.shape[1::-1], "RGB")
    
class ExternalView(GameState, ControlWnd):
  def __init__(self, wndpos=pygame.Rect(0,0,640,480), scaletofit=True, **args):
    ControlWnd.__init__(self, wndpos=wndpos, **args)
    GameState.__init__(self)
    self._background = (0,0,0)
    self._scaletofit = scaletofit
    self._video = VideoStream()
    self._offline = Offline(bgcol=self._background, wndpos=pygame.Rect(wndpos.width/4, wndpos.height/4, wndpos.width/2, wndpos.height/2))
    self._isonline = False # Video stream online and streaming
    self._camport = None
    self._address = None
    self._vidthread = None

    addressinfo = self.get_state("app_camconnection")
    if addressinfo is not None:
      self._camport = addressinfo[1]
      self._address = addressinfo[0]
    
  def state_change(self, param, value):
    # Callback for any state changes
    if param == "app_camconnection":
      print ("setting cam at {}:{}".format(self._address, self._camport))
      self._address = value[0]
      self._camport = value[1]
    elif param == "cam_online":
      # TO DO: open camera in thread to prevent IO blocking. Show a connecting message in Offline screen
      if value:
          if not (self._isonline and self._vidthread.is_alive()):
            self._vidthread = threading.Thread(target=self._open_stream_t)
            self._vidthread.start()
          else:
            print ("DEBUG - Cannot start video, already running")
      else:
        self._video.close()
        self._isonline = False
        
  def _open_stream_t(self):
    self._offline.connectingvideo(True)
    if self._video.open(self._address, self._camport):
      self._isonline = True
    else:
      self._video.close()
      self._isonline = False
      self.set_state("cam_online", False)
    self._offline.connectingvideo(False)
        
  def draw(self):
    self.screen.fill(self._background)
    if self._isonline: # Stream open, show the video
      vidimg = self._video.getimage()
      if vidimg is None:
        self._isonline = False
      else:
        vidimg = vidimg.convert()
        if self._scaletofit:
          pygame.transform.scale(vidimg, self._wndpos.size, self.screen)
        else:
          self.screen.blit(vidimg, vidimg.get_rect(centerx = self._wndpos.centerx, centery = self._wndpos.centery))
    else: # Show the offline screen
      self._offline.draw()
      # Blit centrally
      self.screen.blit(self._offline.screen, 
                       self._offline.screen.get_rect(centerx = self._wndpos.centerx, centery = self._wndpos.centery))