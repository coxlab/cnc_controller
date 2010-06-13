#!/usr/bin/env python

import logging

from Foundation import *
from AppKit import *
import objc
from objc import IBAction, IBOutlet

class OCCenteringSliderCell(NSSliderCell):
    controller = objc.IBOutlet()
    velocityField = objc.IBOutlet()
    
    # need to set maxValue = 1.0 and minValue to -1.0
    def setValue_forKeyPath_(self, value, keypath):
        if keypath == 'axis':
            self.axis = value
    
    def continueTracking_at_inView_(self, lastPoint, currentPoint, controlView):
        # move axis by amount Value
        #print self.floatValue()
        self.cncAxes.move_relative(self.floatValue(), self.axis)
        
        return NSSliderCell.continueTracking_at_inView_(self, lastPoint, currentPoint, controlView)
    
    def startTrackingAt_inView_(self, startPoint, controlView):
        # find which cnc axes control this axis
        if self.axis in self.controller.cnc.linearAxes.axes.keys():
            self.cncAxes = self.controller.cnc.linearAxes
        elif self.axis in self.controller.cnc.headAxes.axes.keys():
            self.cncAxes = self.controller.cnc.headAxes
        else:
            raise ValueError("invalid axis(%s) for OCCenteringSliderCell" % self.axis)
        
        # set axis velocity from text field
        #print self.velocityField.floatValue()
        self.controller.update_velocities()
        
        #print "start tracking"
        logging.debug("start tracking")
        return NSSliderCell.startTrackingAt_inView_(self, startPoint, controlView)
    
    def stopTracking_at_inView_mouseIsUp_(self, lastPoint, stopPoint, controlView, flag):
        self.setFloatValue_(0.0)
        # stop axis
        #print "stopping axis"
        NSSliderCell.stopTracking_at_inView_mouseIsUp_(self, lastPoint, stopPoint, controlView, flag)