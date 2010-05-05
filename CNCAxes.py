#!/usr/bin/env python

#TODO
#  setup estop to stop motion but NOT kill motors
#  setup softwares limits to stop motion but NOT kill motors
#  remove software limits (I don't think they're important
#  fix parameters
#  assign different parameters to each axis


from IPSerialBridge import IPSerialBridge

class CNCLinearAxes(IPSerialBridge):
    """
    x: 1: left(-)/right(+) : home=positive
    y: 2: forward(-)/back(+) : home=negative
    z: 3: down(-)/up(+) : home=positive
    
    It is a BAD idea to home these axes automatically. Therefore the homing velocity
    is set to 0.0 on all axes.
    
    y give negative home velocity
    
    minimum 'step' is 0.0127 mm
    """
    
    espConfigCommand="""QM3
        QI2.0
        QV30.0
        SN2
        SU0.0127
        FR0.0127
        QS1000
        VU12.7
        VA6.35
        JH6.35
        JW3.175
        OH0.0
        AU6.35
        AC6.35
        AG6.35
        FE25.3999
        TJ1
        OM3
        SL%g
        SR%g
        ZA323H
        ZB0H
        ZE3H
        ZF2H
        ZH24H
        ZS24H
        QD"""
    
    def __init__(self, address, port, xAxis = 1, yAxis = 2, zAxis = 3,
                xyzLimits=((-355.6, 0.0), (-355.6, 0.0), (-101.6, 0.0)),
                timeout=None):
        IPSerialBridge.__init__(self, address, port)
        self.connect(timeout=timeout)
        
        self.xAxis = xAxis
        self.yAxis = yAxis
        self.zAxis = zAxis
        
        self.configure_axis(self.xAxis, *xyzLimits[0])
        self.configure_axis(self.yAxis, *xyzLimits[1])
        self.configure_axis(self.zAxis, *xyzLimits[2])
        self.power_down()
        self.save_settings_to_controller()
    
    def configure_axis(self, axis, leftLimit, rightLimit):
        filledCommand = self.espConfigCommand % (leftLimit, rightLimit)
        for command in filledCommand.splitlines():
            #print "sending:", "%d%s" % (axis, command)
            self.send("%d%s" % (axis, command), 1)
    
    def power_down(self, axis=None):
        if axis == None:
            self.send("1MF", 1)
            self.send("2MF", 1)
            self.send("3MF", 1)
        else:
            self.send("%dMF" % axis, 1)
    
    def power_up(self, axis=None):
        if axis == None:
            self.send("1MO", 1)
            self.send("2MO", 1)
            self.send("3MO", 1)
        else:
            self.send("%dMO" % axis, 1)
    
    def save_settings_to_controller(self):
        self.send("SM",1) # store controller settings to non-volatile memory
    
    def composite_move_relative(self, x, y, z):
        return (move_relative(self.xAxis, x),
                move_relative(self.yAxis, y),
                move_relative(self.zAxis, z))
    
    def move_relative(self, axis, pos):
        self.send("%dPR%.4f" % (axis, float(pos)), 1) # set target as relative position
        self.send("%dWS" % axis, 1) # tell controller to wait till movement ends
        return self.get_position(axis) # report position of axis
    
    def get_position(self, axis=None):
        if axis==None:
            return (self.get_position(self.xAxis),
                    self.get_position(self.yAxis),
                    self.get_position(self.zAxis))
        else:
            return self.send("%dTP" % axis)
    
    def set_software_home(self, axis):
        return self.send("%dDH00" % axis)
    
    def set_software_limits(self, axis, posLimit, negLimit):
        """
        Set left and right limits, enable sw limits, disable motors on limit,
        and abort motion on limit.
        """
        return (self.send("%dSL%d" % (axis, posLimit)),
                self.send("%dSR%d" % (axis, negLimit)),
                self.send("%dZS0FFFFH" % axis))
    
    def is_motion_done(self, axis=None):
        if axis == None:
            return all((self.send("1MD"), self.send("2MD"), self.send("3MD")))
        else:
            return self.send("%dMD" % axis)
    
    #def home(self, axis):
    #    homeVelocity = 5.0
    #    if axis == self.yAxis:
    #        homeVelocity *= -1
    #    # home axis
    #    self.send("%dOH%g" % (axis, homeVelocity), 1)
    #    #self.send("%dOR3" % axis, 1)
    #    #self.send("%dWS" % axis, 1)
    #    # reset home velocity to 0
    #    self.send("%dOH0" % axis, 1)

class CNCFakeLinearAxes():
    def __init__(self):
        self.pos = [0., 0., 0.]
        self.moving = 0
    def power_down(self, axis=None):
        pass
    def power_up(self, axis=None):
        pass
    def save_settings_to_controller(self):
        pass
    def composite_move_relative(self, x, y, z):
        self.pos = [self.pos[0] + x, self.pos[1] + y, self.pos[2] + z]
    def move_relative(self, axis, pos):
        self.pos[axis-1] += pos
        self.moving += 1
    def get_position(self, axis=None):
        if axis == None:
            return self.pos[0], self.pos[1], self.pos[2]
        else:
            return self.pos[axis-1]
    def set_software_home(self, axis):
        self.pos = [0., 0., 0.]
    def set_software_limits(self, axis, posLimit, negLimit):
        pass
    def is_motion_done(self, axis=None):
        if self.moving > 0:
            self.moving -= 1
            return False
        else:
            return True

class CNCHeadAxes(IPSerialBridge):
    """
    b: rotation clockwise(-)/counterclockwise(+)
    w: fine Z up(-)/down(+)
    
    minimum 'step' is ?
    """
    def __init__(self, address, port, bAxis = 1, wAxis = 2, timeout=None):
        IPSerialBridge.__init__(self, address, port)
        self.connect(timeout=timeout)
        
        self.bAxis = bAxis
        self.wAxis = wAxis
        
        #self.configure_axis(self.xAxis, *xyzLimits[0])
        self.power_down()
        #self.save_settings_to_controller()
    
    def configure_axis(self, axis, leftLimit, rightLimit):
        #filledCommand = self.espConfigCommand % (leftLimit, rightLimit)
        #for command in filledCommand.splitlines():
        #    #print "sending:", "%d%s" % (axis, command)
        #    self.send("%d%s" % (axis, command), 1)
        pass
    
    def power_down(self, axis=None):
        if axis == None:
            self.send("1MF", 1)
            self.send("2MF", 1)
            #self.send("3MF", 1)
        else:
            self.send("%dMF" % axis, 1)
    
    def power_up(self, axis=None):
        if axis == None:
            self.send("1MO", 1)
            self.send("2MO", 1)
            #self.send("3MO", 1)
        else:
            self.send("%dMO" % axis, 1)
    
    def save_settings_to_controller(self):
        self.send("SM",1) # store controller settings to non-volatile memory
    
    def composite_move_relative(self, b, w):
        return (move_relative(self.bAxis, x),
                move_relative(self.wAxis, y))
    
    def move_relative(self, axis, pos):
        self.send("%dPR%.4f" % (axis, float(pos)), 1) # set target as relative position
        self.send("%dWS" % axis, 1) # tell controller to wait till movement ends
        return self.get_position(axis) # report position of axis
    
    def get_position(self, axis=None):
        if axis==None:
            return (self.get_position(self.bAxis),
                    self.get_position(self.wAxis))
        else:
            return self.send("%dTP" % axis)
    
    def set_software_home(self, axis):
        return self.send("%dDH00" % axis)
    
    def set_software_limits(self, axis, posLimit, negLimit):
        """
        Set left and right limits, enable sw limits, disable motors on limit,
        and abort motion on limit.
        """
        return (self.send("%dSL%d" % (axis, posLimit)),
                self.send("%dSR%d" % (axis, negLimit)),
                self.send("%dZS0FFFFH" % axis))   
    
    def is_motion_done(self, axis=None):
        if axis == None:
            return all((self.send("1MD"), self.send("2MD"), self.send("3MD")))
        else:
            return self.send("%dMD" % axis)
    
    #def home(self, axis):
    #    #homeVelocity = 5.0
    #    #if axis == self.yAxis:
    #    #    homeVelocity *= -1
    #    # home axis
    #    #self.send("%dOH%g" % (axis, homeVelocity), 1)
    #    if axis == self.wAxis:
    #        raise Exception("This should be a notification reminding you to remove the preamp prior to homing the w-axis")
    #    else:
    #        self.send("%dOR3" % axis, 1)
    #        self.send("%dWS" % axis, 1)

class CNCFakeHeadAxes():
    def __init__(self):
        self.pos = [0., 0.]
        self.moving = 0
    def power_down(self, axis=None):
        pass
    def power_up(self, axis=None):
        pass
    def save_settings_to_controller(self):
        pass
    def composite_move_relative(self, b, w):
        self.pos = [self.pos[0] + b, self.pos[1] + w]
    def move_relative(self, axis, pos):
        self.pos[axis-1] += pos
        self.moving += 1
    def get_position(self, axis=None):
        if axis == None:
            return self.pos[0], self.pos[1]
        else:
            return self.pos[axis-1]
    def set_software_home(self, axis):
        self.pos = [0., 0.]
    def set_software_limits(self, axis, posLimit, negLimit):
        pass
    def is_motion_done(self, axis=None):
        if self.moving > 0:
            self.moving -= 1
            return False
        else:
            return True

if __name__ == '__main__':
    axes = CNCLinearAxes("169.254.0.9", 8003)
    #axes.disconnect()