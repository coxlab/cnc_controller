#
#  CNCController.py
#  main object that interfaces background python code with the cocoa UI
#
#  Created by Brett Graham on 12/7/09
#  Copyright (c) 2009 __MyCompanyName__. All rights reserved
#

import time

from Foundation import *
from AppKit import *
import objc
from objc import IBAction, IBOutlet

import CNCAxes
import cfg

class CNCController (NSObject):
    
    # These are class variables because of vagaries in how PyObjC interacts 
    # with python object instantiated from Nibs
    # Consequently, there can only be one of these
    
    xStep = objc.ivar(u"xStep")
    yStep = objc.ivar(u"yStep")
    zStep = objc.ivar(u"zStep")
    bStep = objc.ivar(u"bStep")
    wStep = objc.ivar(u"wStep")
    
    xPos = objc.ivar(u"xPos")
    yPos = objc.ivar(u"yPos")
    zPos = objc.ivar(u"zPos")
    bPos = objc.ivar(u"bPos")
    wPos = objc.ivar(u"wPos")
    
    xPosLimit = objc.ivar(u"xPosLimit")
    xNegLimit = objc.ivar(u"xNegLimit")
    yPosLimit = objc.ivar(u"yPosLimit")
    yNegLimit = objc.ivar(u"yNegLimit")
    zPosLimit = objc.ivar(u"zPosLimit")
    zNegLimit = objc.ivar(u"zNegLimit")
    
    def awakeFromNib(self):
        print "in awakeFromNib"
        
        # == setting defaults ==
        self._.xStep = cfg.xStep if 'xStep' in dir(cfg) else 1.27 # mm
        self._.yStep = cfg.yStep if 'yStep' in dir(cfg) else 1.27 # mm
        self._.zStep = cfg.zStep if 'zStep' in dir(cfg) else 1.27 # mm
        
        self._.bStep = cfg.bStep if 'bStep' in dir(cfg) else 1.0 # degrees
        self._.wStep = cfg.wStep if 'wStep' in dir(cfg) else 1.0 # mm
        
        self._.xPosLimit = cfg.xPosLimit if 'xPosLimit' in dir(cfg) else 12.70
        self._.xNegLimit = cfg.xNegLimit if 'xNegLimit' in dir(cfg) else -12.70
        self._.yPosLimit = cfg.yPosLimit if 'yPosLimit' in dir(cfg) else 12.70
        self._.yNegLimit = cfg.yNegLimit if 'yNegLimit' in dir(cfg) else -12.70
        self._.zPosLimit = cfg.zPosLimit if 'zPosLimit' in dir(cfg) else 12.70
        self._.zNegLimit = cfg.zNegLimit if 'zNegLimit' in dir(cfg) else -12.70
        
        # set timeout to None to wait until error (infinite timeout)
        # set timeout to 0.0 to not wait for the socket to connect (this is a BAD idea) 
        serialConnectionTimeout = 1.0 # seconds
        if 'serialConnectionTimeout' in dir(cfg):
            serialConnectionTimeout = cfg.serialConnectionTimeout
        
        print "Trying to connect to CNC Linear(XYZ) Axes"
        try:
            linearIP = "169.254.0.9"
            if 'cncLinearAxesIP' in dir(cfg):
                linearIP = cfg.cncLinearAxesIP
            
            linearPort = 8003
            if 'cncLinearAxesPort' in dir(cfg):
                linearPort = cfg.cncLinearAxesPort
            
            self.linearAxes = CNCAxes.CNCLinearAxes(linearIP, linearPort, timeout=serialConnectionTimeout)
        except:
            print "Connection with CNC Linear(XYZ) Axes timed out, making fake axes instead"
            self.linearAxes = CNCAxes.CNCFakeLinearAxes()
            #print "quitting application"
            #NSApp().terminate_(self) # is this the right way to quit?
        
        print "Trying to connect to CNC Head(BW) Axes"
        try:
            headIP = "169.254.0.9"
            if 'cncHeadAxesIP' in dir(cfg):
                headIP = cfg.cncHeadAxesIP
            
            headPort = 8004
            if 'cncHeadAxesPort' in dir(cfg):
                headPort = cfg.cncHeadAxesPort
            
            self.headAxes = CNCAxes.CNCHeadAxes(headIP, headPort, timeout=serialConnectionTimeout)
        except:
            print "Connection with CNC Head(BW) Axes timed out, making fake axes instead"
            self.headAxes = CNCAxes.CNCFakeHeadAxes()
        
        self.update_bindings()
    
    def update_bindings(self):
        # TODO, add checks to see if any of the axes are moving. If they are, wait and then update later
        if not all((self.linearAxes.is_motion_done(),
                    self.headAxes.is_motion_done())):
            self._.xPos, self._.yPos, self._.zPos = (0., 0., 0.)
            self._.bPos, self._.wPos = (0., 0.)
            time.sleep(1)
            return self.update_bindings()
        self._.xPos, self._.yPos, self._.zPos = self.linearAxes.get_position()
        self._.bPos, self._.wPos = self.headAxes.get_position()
    
    # --------------- Actions ------------------
    
    @IBAction
    def xLeft_(self, sender):
        try:
            print "trying to move left"
            xStep = float(self.xStep)
        except:
            return
        self.linearAxes.move_relative(1,-xStep)
        self.update_bindings()
    
    @IBAction
    def xRight_(self, sender):
        try:
            print "trying to move right"
            xStep = float(self.xStep)
        except:
            return
        self.linearAxes.move_relative(1,xStep)
        self.update_bindings()
    
    @IBAction
    def yForward_(self, sender):
        try:
            print "trying to move forward"
            yStep = float(self.yStep)
        except:
            return
        self.linearAxes.move_relative(2,yStep)
        self.update_bindings()
    
    @IBAction
    def yBack_(self, sender):
        try:
            print "trying to move back"
            yStep = float(self.yStep)
        except:
            return
        self.linearAxes.move_relative(2,-yStep)
        self.update_bindings()
    
    @IBAction
    def zUp_(self, sender):
        try:
            print "trying to move z up"
            zStep = float(self.zStep)
        except:
            return
        self.linearAxes.move_relative(3,-zStep)
        self.update_bindings()
    
    @IBAction
    def zDown_(self, sender):
        try:
            print "trying to move z down"
            zStep = float(self.zStep)
        except:
            return
        self.linearAxes.move_relative(3,zStep)
        self.update_bindings()
    
    @IBAction
    def bClockwise_(self, sender):
        try:
            print "trying to move b clockwise"
            bStep = float(self.bStep)
        except:
            return
        self.headAxes.move_relative(1,-bStep)
        self.update_bindings()
    
    @IBAction
    def bCounterClockwise_(self, sender):
        try:
            print "trying to move b counter clockwise"
            bStep = float(self.bStep)
        except:
            return
        self.headAxes.move_relative(1,bStep)
        self.update_bindings()
 
    @IBAction
    def wUp_(self, sender):
        try:
            print "trying to move w up"
            wStep = float(self.wStep)
        except:
            return
        self.headAxes.move_relative(2,-wStep)
        self.update_bindings()
    
    @IBAction
    def wDown_(self, sender):
        try:
            print "trying to move w down"
            wStep = float(self.wStep)
        except:
            return
        self.headAxes.move_relative(2,wStep)
        self.update_bindings()
    
    @IBAction
    def setHome_(self, sender):
        # read limit values, set limits
        print "setting x limits:", self.xPosLimit, self.xNegLimit
        self.linearAxes.set_software_limits(1, self.xPosLimit, self.xNegLimit)
        self.linearAxes.set_software_home(1)
        print "setting y limits:", self.yPosLimit, self.yNegLimit
        self.linearAxes.set_software_limits(2, self.xPosLimit, self.xNegLimit)
        self.linearAxes.set_software_home(1)
        print "setting z limits:", self.zPosLimit, self.zNegLimit
        self.linearAxes.set_software_limits(3, self.xPosLimit, self.xNegLimit)
        self.linearAxes.set_software_home(1)
        self.update_bindings()