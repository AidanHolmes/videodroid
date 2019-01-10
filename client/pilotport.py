import pygame
from gamestate import GameState
from videoport import ExternalView
from sensors import RangeSensor, Lights, Drive
from pgcontrol import ControlWnd

class TextDisplay(ControlWnd):
  def __init__(self, text="", **args):
    ControlWnd.__init__(self, **args)
    self._colourbackground = (40,40,40)
    self._colour1 = (128,128,128)
    self._colourshadow = (0,0,0)

    self._colourtext = (50,255,0)
    self._font = pygame.font.Font(None, 20)
    self.text = text
    self._linewidth = 2
    
  def draw(self):
    self.screen.fill(self._colourbackground)
    drawpos = self.screen.get_rect()

    txt = self._font.render(self.text, 1, self._colourtext)
    drawpos = txt.get_rect(centerx=drawpos.centerx, centery=drawpos.centery)
    self.screen.blit(txt, drawpos)
    
    drawpos = self.screen.get_rect()
    pygame.draw.rect(self.screen, self._colour1, drawpos, self._linewidth)    
    pygame.draw.line(self.screen, self._colourshadow, (drawpos.x+self._linewidth,drawpos.bottom-self._linewidth), (drawpos.x+self._linewidth, drawpos.y+self._linewidth), self._linewidth)
    pygame.draw.line(self.screen, self._colourshadow, (drawpos.right-self._linewidth,drawpos.y+self._linewidth), (drawpos.x+self._linewidth, drawpos.y+self._linewidth), self._linewidth)
    
  
class DroidButton(GameState, ControlWnd):
  def __init__(self, statename="", text="", **args):
    ControlWnd.__init__(self, **args)
    GameState.__init__(self)
    self._colouron = (50,255,0)
    self._colouroff = (128,128,128)
    self._colourbutton = (255,145,0)
    self._colourbackground = (0,0,0)
    self._linewidth = 3
    self.text = text
    self._active = False
    self._font = pygame.font.Font(None, 20)
    self._statename = statename
    self._toggletype = True

  def set_toggle(self, toggle):
    self._toggletype = toggle
    
  def state_change(self, param, value):
    if param == self._statename:
      if value:
        self._active = True
      else:
        self._active = False

  def local_event(self, evt):
    if evt.type == pygame.MOUSEBUTTONDOWN:
      if self._toggletype:
        self.set_state(self._statename, not self._active)
      else:
        self.set_state(self._statename, True)

  def focused(self):
    if not self._toggletype:
      self._active = True
    
  def unfocused(self):
    if not self._toggletype:
      self._active = False
      
  def draw(self):
    self.screen.fill(self._colourbackground)
    drawpos = self.screen.get_rect()
    pygame.draw.rect(self.screen, self._colourbutton, drawpos, self._linewidth)
    txt = None
    if self._active:
      drawpos.width = drawpos.width - (self._linewidth*2)
      drawpos.height = drawpos.height - (self._linewidth*2)
      drawpos.x = drawpos.x + self._linewidth
      drawpos.y = drawpos.y + self._linewidth
      pygame.draw.rect(self.screen, self._colouron, drawpos, self._linewidth)
      txt = self._font.render(self.text, 1, self._colouron)
    else:
      txt = self._font.render(self.text, 1, self._colouroff)
    
    drawpos = self.screen.get_rect()
    drawpos = txt.get_rect(centerx=drawpos.centerx, centery=drawpos.centery)
    self.screen.blit(txt, drawpos)
    
class DroidImgButton(DroidButton):
  def __init__(self, image="default.png", imageactive="default.png", *args, **kwargs):
    DroidButton.__init__(self, *args,**kwargs)
    self._imagefilename = image
    self._imageactivefilename = imageactive
    self._image = pygame.image.load(self._imagefilename).convert_alpha()
    self._image = pygame.transform.smoothscale(self._image, self._wndpos.size)
    self._imageactive = pygame.image.load(self._imageactivefilename).convert_alpha()
    self._imageactive = pygame.transform.smoothscale(self._imageactive, self._wndpos.size)
    
  def draw(self):
    if self._active:
      self.screen.blit(self._imageactive, (0,0))
    else:
      self.screen.blit(self._image, (0,0))
    

class Cockpit(GameState, ControlWnd):
  def __init__(self, **args):
    ControlWnd.__init__(self, **args)
    GameState.__init__(self)
    self._view = ExternalView(self._wndpos, True)
    self._rangesensor = RangeSensor()
    self._lights = Lights()
    self._drive = Drive()
    # use state change to update the address and port
    self._apiport = None 
    self._address = None
    self._image = pygame.image.load("cockpit.png").convert_alpha()
    self._scaling = (self._wndpos.width / self._image.get_width(), self._wndpos.height / self._image.get_height())
    self._image = pygame.transform.smoothscale(self._image, self._wndpos.size)
    self._movecontrols = []
    self._rangemode = 0
    
    self._hudfont = pygame.font.Font(None, 15)
    self._hudcolour = (50,255,0)
    self._hudcolourwarning = (255,0,0)
    self._hudscale = 100 # in mm
    self._hudmarkat = 40 * self._scaling[1] # pixels
    
    screenpos = self.screen.get_rect()
    
    pos = pygame.Rect(150*self._scaling[0], screenpos.bottom - (120 * self._scaling[1]), 50*self._scaling[0], 25*self._scaling[1])
    self._videobtn = DroidButton("cam_online", "Video", wndpos=pos)
    self.add_control(self._videobtn)
    
    pos = pygame.Rect(pos.left, pos.bottom + (10 * self._scaling[1]), 50*self._scaling[0], 25*self._scaling[1])
    self._lightbtn = DroidButton("light_ctrl", "Lights", wndpos=pos)
    self.add_control(self._lightbtn)
    
    pos = pygame.Rect(500*self._scaling[0], screenpos.bottom - (100 * self._scaling[1]), 20*self._scaling[0], 20*self._scaling[1])
    self._rngupbtn = DroidImgButton(wndpos=pos, statename="range_up", image="btnupnorm.png", imageactive="btnupactive.png")
    self._rngupbtn.set_toggle(False)
    self.add_control(self._rngupbtn)
    
    pos = pygame.Rect(pos.left, pos.bottom + (10 * self._scaling[1]), 20*self._scaling[0], 20*self._scaling[1])
    self._rngdnbtn = DroidImgButton(wndpos=pos, statename="range_down", image="btndnnorm.png", imageactive="btndnactive.png")
    self._rngdnbtn.set_toggle(False)
    self.add_control(self._rngdnbtn)
    
    pos = pygame.Rect(pos.left-(65*self._scaling[0]), pos.bottom - (34 * self._scaling[1]), 60*self._scaling[0], 20*self._scaling[1])
    self._rangetxt = TextDisplay(wndpos=pos, text=RangeSensor.MODES[self._rangemode])
    self.add_control(self._rangetxt)
    
    pos = pygame.Rect(pos.left, self._videobtn.get_rect().top, 50*self._scaling[0], 25*self._scaling[1])
    self._rangebtn = DroidButton("ranging_ctrl", "Range", wndpos=pos)
    self.add_control(self._rangebtn)
    
    pos = pygame.Rect(312 * self._scaling[0], screenpos.bottom - (125 * self._scaling[1]), 25*self._scaling[0], 25*self._scaling[1])
    self._moveupbtn = DroidImgButton(wndpos=pos, statename="move_forward", image="btnupnorm.png", imageactive="btnupactive.png")
    self._moveupbtn.set_toggle(False)
    self.add_control(self._moveupbtn)
    self._movecontrols.append(self._moveupbtn)
    
    pos = pygame.Rect(pos.left, pos.bottom + (5 * self._scaling[1]), 25*self._scaling[0], 25*self._scaling[1])
    self._movestopbtn = DroidImgButton(wndpos=pos, statename="move_stop", image="btnstopnorm.png", imageactive="btnstopactive.png")
    self._movestopbtn.set_toggle(False)
    self.add_control(self._movestopbtn)
    self._movecontrols.append(self._movestopbtn)
    
    pos = pygame.Rect(pos.left - (30 *self._scaling[0]), pos.top, 25*self._scaling[0], 25*self._scaling[1])
    self._moveleftbtn = DroidImgButton(wndpos=pos, statename="move_left", image="btnleftnorm.png", imageactive="btnleftactive.png")
    self._moveleftbtn.set_toggle(False)
    self.add_control(self._moveleftbtn)
    self._movecontrols.append(self._moveleftbtn)

    pos = self._movestopbtn.get_rect()
    
    pos = pygame.Rect(pos.left + (30 *self._scaling[0]), pos.top, 25*self._scaling[0], 25*self._scaling[1])
    self._moverightbtn = DroidImgButton(wndpos=pos, statename="move_right", image="btnrightnorm.png", imageactive="btnrightactive.png")
    self._moverightbtn.set_toggle(False)
    self.add_control(self._moverightbtn)
    self._movecontrols.append(self._moverightbtn)
    
    pos = self._movestopbtn.get_rect()
    
    pos = pygame.Rect(pos.left, pos.bottom +(5 * self._scaling[1]), 25*self._scaling[0], 25*self._scaling[1])
    self._movebackbtn = DroidImgButton(wndpos=pos, statename="move_back", image="btndnnorm.png", imageactive="btndnactive.png")
    self._movebackbtn.set_toggle(False)
    self.add_control(self._movebackbtn)
    self._movecontrols.append(self._movebackbtn)

    self._lastmove = "stop"
    
    addressinfo = self.get_state("app_apiconnection")
    if addressinfo is not None:
      self._address = addressinfo[0]
      self._apiport = addressinfo[1]
      self._rangesensor.open(addressinfo[0], addressinfo[1])  
      self._rangesensor.mode=RangeSensor.MODES[self._rangemode]
      self._lights.open(addressinfo[0], addressinfo[1]) 
      self._drive.open(addressinfo[0], addressinfo[1])
    
  def state_change(self, param, value):
    # Callback for any state changes
    if param == "app_apiconnection":
      self._address = value[0]
      self._apiport = value[1]
      self._rangesensor.open(value[0], value[1])  
      self._lights.open(value[0], value[1])      
    elif param == "light_ctrl":
      self._lights.switch(value)
    elif param == "range_up":
      if self._rangemode < len(RangeSensor.MODES)-1:
        self._rangemode = self._rangemode + 1
        self._rangetxt.text = RangeSensor.MODES[self._rangemode]
        self._rangesensor.mode=self._rangetxt.text
    elif param == "range_down":
      if self._rangemode > 0:
        self._rangemode = self._rangemode - 1
        self._rangetxt.text = RangeSensor.MODES[self._rangemode]
        self._rangesensor.mode=self._rangetxt.text
    elif param == "ranging_ctrl":
      if value:
        self._rangesensor.start_ranging()
      else:
        self._rangesensor.stop_ranging()
    elif param == "move_forward":
      for ctl in self._movecontrols:
        ctl.focus = False
      self._moveupbtn.focus = True
      
      self._lastmove = 'fwd'
      self._drive.move = (self._lastmove, 150)
    elif param == "move_stop":
      for ctl in self._movecontrols:
        ctl.focus = False
      self._movestopbtn.focus = True
      
      self._lastmove = 'stop'
      self._drive.move = (self._lastmove, 0)
    elif param == "move_back":
      for ctl in self._movecontrols:
        ctl.focus = False
      self._movebackbtn.focus = True
      
      self._lastmove = 'back'
      self._drive.move = (self._lastmove, 150)
    elif param == "move_left":
      for ctl in self._movecontrols:
        ctl.focus = False
      self._moveleftbtn.focus = True

      if self._lastmove == 'fwd':
        self._drive.move = ('rfwd', 150)
        self._drive.move = ('lfwd', 80)
      elif self._lastmove == 'stop':
        self._drive.move = ('rfwd', 100)
        self._drive.move = ('lback', 100)
      elif self._lastmove == 'back':
        self._drive.move =('rback', 150)
        self._drive.move = ('lback', 80)
    elif param == "move_right":
      for ctl in self._movecontrols:
        ctl.focus = False
      self._moverightbtn.focus = True
      
      if self._lastmove == 'fwd':
        self._drive.move = ('lfwd', 150)
        self._drive.move = ('rfwd', 80)
      elif self._lastmove == 'stop':
        self._drive.move = ('lfwd', 100)
        self._drive.move = ('rback', 100)
      elif self._lastmove == 'back':
        self._drive.move =('lback', 150)
        self._drive.move = ('rback', 80)      
        
  def close(self):
    self._rangesensor.stop_ranging()
    self._drive.move = ("stop", 0)
    
  def draw_hud(self):
    distance = self._rangesensor.distance_mm
    hudline_x = 500 * self._scaling[0] # pixels
    hudline_start_y = 50 * self._scaling[1] # pixels
    hudline_end_y = 250 * self._scaling[1] # pixels
    marklength = 3 * self._scaling[0] # pixels
    warningdistance = 100 # mm
    hudrangepx = hudline_end_y - hudline_start_y

    # start of hud range line
    startmm = distance + ((hudrangepx*self._hudscale)/(2*self._hudmarkat))
    endmm = distance - ((hudrangepx*self._hudscale)/(2*self._hudmarkat))
    modulo = (int(startmm/self._hudscale), startmm%self._hudscale)
    markat = modulo[1] * (self._hudmarkat/self._hudscale)
    markval = modulo[0] * self._hudscale
    # HUD line drawing routine    
    pygame.draw.line(self.screen, self._hudcolour, (hudline_x, hudline_start_y), (hudline_x, hudline_end_y),1)
    if endmm < warningdistance:
      warnstartpx = (self._hudmarkat/self._hudscale) * (startmm - warningdistance)
      pygame.draw.line(self.screen, self._hudcolourwarning, (hudline_x, warnstartpx+hudline_start_y), (hudline_x, hudline_end_y),1)

    while markat < hudrangepx: # draw marks until exceeding range
      col = self._hudcolour
      if markval < warningdistance:
        col = self._hudcolourwarning
      pygame.draw.line(self.screen, col, (hudline_x, markat+hudline_start_y), (hudline_x+marklength, markat+hudline_start_y), 1)
      txt = self._hudfont.render(str(markval)+"mm", 1, col)
      drawpos = txt.get_rect(left=hudline_x+marklength, centery=markat+hudline_start_y)
      self.screen.blit(txt, drawpos)
      # Advance markings and values
      markat = markat + self._hudmarkat
      markval = markval - self._hudscale
      
    col = self._hudcolour
    if distance < warningdistance:
      col = self._hudcolourwarning
    txt = self._hudfont.render(str(distance)+"mm", 1, col)
    drawpos = txt.get_rect(right=hudline_x-6, centery=int((hudline_start_y+hudline_end_y)/2))
    self.screen.blit(txt, drawpos)
    drawpos.width += 4
    drawpos.height += 4
    drawpos.x -= 2
    drawpos.y -= 2
    pygame.draw.rect(self.screen, col, drawpos, 1)
      
  def draw(self):
    # Draw external view
    self._view.draw()
    # Blit external view to cockpit screen
    self.screen.blit(self._view.screen, (0,0))
    # Draw the cockpit control dashboard
    self.screen.blit(self._image, (0,0))
    
    for ctl in self._controls:
      ctl.draw()
      self.screen.blit(ctl.screen, ctl.get_rect())
      
    if self.get_state("ranging_ctrl"):
      self.draw_hud()
    
    