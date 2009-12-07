#
#  CNCController.py
#  main object that interfaces background python code with the cocoa UI
#
#  Created by Brett Graham on 12/7/09
#  Copyright (c) 2009 __MyCompanyName__. All rights reserved
#

from Foundation import *
from AppKit import *
import objc
from objc import IBAction, IBOutlet

import CNCAxes

class CNCController (NSObject):
    
    # These are class variables because of vagaries in how PyObjC interacts 
    # with python object instantiated from Nibs
    # Consequently, there can only be one of these
    
    xStep = objc.ivar(u"xStep")
    yStep = objc.ivar(u"yStep")
    zStep = objc.ivar(u"zStep")
    bStep = objc.ivar(u"bStep")
    wStep = objc.ivar(u"wStep")
    
    def awakeFromNib(self):
        print "in awakeFromNib"
        
        # == setting defaults ==
        self._.xStep = 1.27 # mm
        self._.yStep = 1.27 # mm
        self._.zStep = 1.27 # mm
        
        self._.bStep = 1.0 # degrees
        self._.wStep = 1.0 # mm
        
        # set timeout to None to wait until error (infinite timeout)
        # set timeout to 0.0 to not wait for the socket to connect (this is a BAD idea) 
        serialConnectionTimeout = 4.0 # seconds
        
        print "Trying to connect to CNC Linear(XYZ) Axes"
        try:
            self.linearAxes = CNCAxes.CNCLinearAxes("169.254.0.9", 8003, timeout=serialConnectionTimeout)
        except:
            print "Connection with CNC Linear(XYZ) Axes timed out, making fake axes instead"
            self.linearAxes = CNCAxes.CNCFakeLinearAxes()
            #print "quitting application"
            #NSApp().terminate_(self) # is this the right way to quit?
        
        print "Trying to connect to CNC Head(BW) Axes"
        try:
            self.headAxes = CNCAxes.CNCHeadAxes("169.254.0.9", 8004, timeout=serialConnectionTimeout)
        except:
            print "Connection with CNC Head(BW) Axes timed out, making fake axes instead"
            self.headAxes = CNCAxes.CNCFakeHeadAxes()
            
    
    # --------------- Actions ------------------
    
    @IBAction
    def xLeft_(self, sender):
        try:
            print "trying to move left"
            xStep = float(self.xStep)
        except:
            return
        self.linearAxes.move_relative(1,-xStep)
    
    @IBAction
    def xRight_(self, sender):
        try:
            print "trying to move right"
            xStep = float(self.xStep)
        except:
            return
        self.linearAxes.move_relative(1,xStep)
    
    @IBAction
    def yForward_(self, sender):
        try:
            print "trying to move forward"
            yStep = float(self.yStep)
        except:
            return
        self.linearAxes.move_relative(2,yStep)
    
    @IBAction
    def yBack_(self, sender):
        try:
            print "trying to move back"
            yStep = float(self.yStep)
        except:
            return
        self.linearAxes.move_relative(2,-yStep)
    
    @IBAction
    def zUp_(self, sender):
        try:
            print "trying to move z up"
            zStep = float(self.zStep)
        except:
            return
        self.linearAxes.move_relative(3,-zStep)
    
    @IBAction
    def zDown_(self, sender):
        try:
            print "trying to move z down"
            zStep = float(self.zStep)
        except:
            return
        self.linearAxes.move_relative(3,zStep)
    
    @IBAction
    def bClockwise_(self, sender):
        try:
            print "trying to move b clockwise"
            bStep = float(self.bStep)
        except:
            return
        self.headAxes.move_relative(1,-bStep)
    
    @IBAction
    def bCounterClockwise_(self, sender):
        try:
            print "trying to move b counter clockwise"
            bStep = float(self.bStep)
        except:
            return
        self.headAxes.move_relative(1,bStep)
 
    @IBAction
    def wUp_(self, sender):
        try:
            print "trying to move w up"
            wStep = float(self.wStep)
        except:
            return
        self.headAxes.move_relative(2,-wStep)
    
    @IBAction
    def wDown_(self, sender):
        try:
            print "trying to move w down"
            wStep = float(self.wStep)
        except:
            return
        self.headAxes.move_relative(2,wStep)
