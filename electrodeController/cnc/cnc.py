#!/usr/bin/env python

from .. import cfg
import axes
if cfg.fakeCNC:
    from axes import FakeAxes as Axes
else:
    from axes import Axes
#import cncAxes
from numpy import *

#from rayfit import measure_rotation_plane
from linefit import fit_3d_line

class FiveAxisCNC:
    """
    linearAxes = {'x':1, 'y':2, 'z':3}
    headAxes = {'b':1, 'w':2}
    """
    def __init__(self):
        self.linearAxes = Axes(cfg.cncLinearAxesIP, cfg.cncLinearAxesPort, cfg.cncLinearAxes, cfg.serialConnectionTimeout)
        # configure
        #self.linearAxes.configure_axis('x',cfg.xAxisConfig)
        #self.linearAxes.configure_axis('y',cfg.yAxisConfig)
        #self.linearAxes.configure_axis('z',cfg.zAxisConfig)
        #self.linearAxes.save_settings_to_controller()
        self.headAxes = Axes(cfg.cncHeadAxesIP, cfg.cncHeadAxesPort, cfg.cncHeadAxes, cfg.serialConnectionTimeout)
        #self.headAxes.configure_axis('w',cfg.wAxisConfig)
        #self.headAxes.save_settings_to_controller()
        self.arm_length = None
        self.pathParams = None#[0., 0., 0., 0., 1., 0.]
        #self.disable_motors()
        
        self.configure_cnc()
    
    def configure_cnc(self):
        self.linearAxes.configure_axis('x', cfg.xAxisConfig)
        self.linearAxes.configure_axis('y', cfg.yAxisConfig)
        self.linearAxes.configure_axis('z', cfg.zAxisConfig)
        # configure linear groups
        cncLinearAxes
        self.linearAxes.send('1HN%i,%i,%i' % (self.linearAxes.axes['x'], self.linearAxes.axes['y'], self.linearAxes.axes['z']), 1)
        self.linearAxes.save_settings_to_controller()
        
        self.headAxes.configure_axis('w', cfg.wAxisConfig)
        # configure head groups
        self.linearAxes.send('1HN%i,%i,%i' % (self.headAxes.axes['b'], self.headAxes.axes['w']), 1)
        self.headAxes.save_settings_to_controller()
    
    def get_positions(self):
        r = {}
        lp = self.linearAxes.send('1HP',0).split(',')
        for k, v in self.linearAxes.iteritems():
            r[k] = float(lp[v])
        hp = self.headAxes.send('1HP',0).split(',')
        for k, v in self.headAxes.iteritems():
            r[k] = float(hp[v])
        return r
    
    def enable_motors(self):
        self.linearAxes.enable_motor()
        self.headAxes.enable_motor()
    
    def disable_motors(self):
        self.linearAxes.disable_motor()
        self.headAxes.disable_motor()
    
    def motion_done(self):
        linearStatus = self.linearAxes.get_controller_status()
        headStatus = self.headAxes.get_controller_status()
        # 'left most ascii character'
        #     low = stationary, high = in motion
        #  0 : axis 1
        #  1 : axis 2
        #  2 : axis 3
        print linearStatus, headStatus
        if ord(linearStatus[0]) & 0x07 or ord(headStatus[0]) & 0x07:
            return False
        else:
            return True
        ret = self.linearAxes.motion_done()
        ret.update(self.headAxes.motion_done())
        for r in ret.values():
            if int(r) == 0:
                return False
        return True
    
    def get_motor_status(self):
        # if ANY motor is on, return True
        ret = self.linearAxes.get_motor_status()
        ret.update(self.headAxes.get_motor_status())
        for r in ret.values():
            if int(r) == 1:
                return True
        return False
    
    def measure_tip_path(self, tipLocations, wPositions):
        """
        Fit a 3d line to a collection of tip locations to determine the path 
        of the electrode in the camera frame [the frame of the tip locations]
        """
        pathParams = fit_3d_line(tipLocations, wPositions) # [x0, y0, z0, a, b, c]
        self.pathParams = pathParams
        print pathParams
        return self.pathParams
    
    def calculate_tip_position(self, t):
        """
        Given:
            -the location of the tip on the path (defined by the w-axis)
            -the pathParams
        Calculate:
            -the location of the tip in the same frame as the pathParams
        """
        o = array(self.pathParams[:3])
        m = array(self.pathParams[3:])
        p = o + t * m
        return p
    
    def calculate_arm_length(self, tipLocations, angles, wPositions):
        """Requires 3 measurements of the tip location at 3 angles"""
        raise Exception, "Does not work"
        cfg.cncLog.info("measuring arm length with (wPositions, angles, tipLocations):")
        cfg.cncLog.info(wPositions)
        cfg.cncLog.info(angles)
        cfg.cncLog.info(tipLocations)
        
        # using rayfit
        rotCen, rotNorm, rotRadii = measure_rotation_plane(tipLocations, angles, wPositions)
        cfg.cncLog.info("Center of rotation:")
        cfg.cncLog.info(rotCen)
        cfg.cncLog.info("Rotation plane normal:")
        cfg.cncLog.info(rotNorm)
        cfg.cncLog.info("Measured radii:")
        cfg.cncLog.info(rotRadii)
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
        raise Exception, "Does not work"
        return sin(angle)*length, -cos(angle)*length, 0.
    
    def get_tip_position_on_arm(self):
        raise Exception, "Does not work"
        b = radians(float(self.headAxes.get_position('b')['b']))
        w = float(self.headAxes.get_position('w')['w']) #FIXME w axis flip
        return self.get_position_on_arm(radians(b), self.arm_length - w)