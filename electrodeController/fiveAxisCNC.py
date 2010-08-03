#!/usr/bin/env python

import cfg
if cfg.fakeCNC:
    from cncAxes import FakeAxes as Axes
else:
    from cncAxes import Axes
#import cncAxes
from numpy import *

from rayfit import measure_rotation_plane

class FiveAxisCNC:
    """
    linearAxes = {'x':1, 'y':2, 'z':3}
    headAxes = {'b':1, 'w':2}
    """
    def __init__(self):
        self.linearAxes = Axes(cfg.cncLinearAxesIP, cfg.cncLinearAxesPort, cfg.cncLinearAxes, cfg.serialConnectionTimeout)
        # configure
        self.linearAxes.configure_axis('x',cfg.xAxisConfig)
        self.linearAxes.configure_axis('y',cfg.yAxisConfig)
        self.linearAxes.configure_axis('z',cfg.zAxisConfig)
        self.linearAxes.save_settings_to_controller()
        self.headAxes = Axes(cfg.cncHeadAxesIP, cfg.cncHeadAxesPort, cfg.cncHeadAxes, cfg.serialConnectionTimeout)
        self.headAxes.configure_axis('w',cfg.wAxisConfig)
        self.headAxes.save_settings_to_controller()
        self.arm_length = None
        self.disable_motors()
    
    def enable_motors(self):
        self.linearAxes.enable_motor()
        self.headAxes.enable_motor()
    
    def disable_motors(self):
        self.linearAxes.disable_motor()
        self.headAxes.disable_motor()
    
    def get_motor_status(self):
        # if ANY motor is on, return True
        ret = self.linearAxes.get_motor_status()
        ret.update(self.headAxes.get_motor_status())
        for r in ret.values():
            if int(r) == 1:
                return True
        return False
    
    def calculate_arm_length(self, tipLocations, angles, wPositions):
        """Requires 3 measurements of the tip location at 3 angles"""
        cfg.cncLog.info("measuring arm length with (wPositions, tipLocations):")
        cfg.cncLog.info(wPositions)
        cfg.cncLog.info(tipLocations)
        
        # using rayfit
        rotCen, rotNorm, rotRadii = measure_rotation_plane(tipLocations, angles, wPositions)
        medRadius = median(rotRadii + wPositions)
        self.arm_length = medRadius
        
        # just measure the arm length (at w = 0)
        #self.arm_length = 184.0
                
        # old, trigonimetric algorithm
        #dists = [sqrt(sum(array(tipLocations[i-1]-tipLocations[i])**2)) for i in xrange(len(tipLocations))]
        #dists.sort()
        #a, b, c = dists
        #self.arm_length = a*b*c / sqrt(2*a**2*b**2 + 2*b**2*c**2 + 2*c**2*a**2 - a**4 - b**4 - c**4)
        #self.arm_length -= wPosition
        
        # curve fitting
        #self.arm_length -= wPosition
        
        print self.arm_length
        return self.arm_length
    
    def get_position_on_arm(self, angle, length):
        return sin(angle)*length, 0., cos(angle)*length
    
    def get_tip_position_on_arm(self):
        b = radians(float(self.headAxes.get_position('b')['b']))
        w = float(self.headAxes.get_position('w')['w']) #FIXME w axis flip
        return self.get_position_on_arm(radians(b), self.arm_length - w)