#!/usr/bin/env python

# from .. import cfg
import axes
# if cfg.fakeCNC:
#     from axes import FakeAxes as Axes
# else:
#     from axes import Axes
#import cncAxes
from numpy import *

#from rayfit import measure_rotation_plane
from linefit import fit_3d_line


def point_on_circle(angle, radius):
    """
    Center of circle is 0,0
    Angle in degrees
    """
    x = sin(radians(angle)) * radius
    y = cos(radians(angle)) * radius
    return x, y


class FiveAxisCNC:
    """
    linearAxes = {'x':1, 'y':2, 'z':3}
    headAxes = {'b':1, 'w':2}
    """
    def __init__(self, cfgDict={}):
        self.cfg = cfgDict
        if self.cfg.get('fake', False):
            Axes = axes.FakeAxes
        else:
            Axes = axes.Axes
        self.linearAxes = Axes(self.cfg.get('linear_ip', "169.254.0.9"),
                               self.cfg.get('linear_port', 8003),
                               self.cfg.get('linear_axes', \
                                       {'x': 1, 'y': 2, 'z': 3}),
                               self.cfg.get('serial_timeout', 4.0))
        # self.linearAxes = Axes(cfg.cncLinearAxesIP, \
        #        cfg.cncLinearAxesPort, cfg.cncLinearAxes, \
        #        cfg.serialConnectionTimeout)
        # configure
        #self.linearAxes.configure_axis('x',cfg.xAxisConfig)
        #self.linearAxes.configure_axis('y',cfg.yAxisConfig)
        #self.linearAxes.configure_axis('z',cfg.zAxisConfig)
        #self.linearAxes.save_settings_to_controller()
        self.headAxes = Axes(self.cfg.get('head_ip', "169.254.0.9"),
                             self.cfg.get('head_pot', 8004),
                             self.cfg.get('head_axes', {'b': 1, 'w': 2}),
                             self.cfg.get('serial_timeout', 4.0))
        # self.headAxes = Axes(cfg.cncHeadAxesIP, cfg.cncHeadAxesPort, \
        #        cfg.cncHeadAxes, cfg.serialConnectionTimeout)
        #self.headAxes.configure_axis('w',cfg.wAxisConfig)
        #self.headAxes.save_settings_to_controller()
        self.armLength = self.cfg.get('arm_length', None)
        # if 'cncArmLength' in dir(cfg):
        #     self.armLength = cfg.cncArmLength
        # else:
        #     self.armLength = None
        self.pathParams = None  # [0., 0., 0., 0., 1., 0.]
        self.pathPoints = 0
        #self.disable_motors()

        #self.configure()

    def configure(self):
        self.linearAxes.send("1XX", 1)
        self.linearAxes.send("1EP", 1)
        self.linearAxes.enable_joystick()
        self.linearAxes.send("QP", 1)

        self.linearAxes.send("2XX", 1)
        self.linearAxes.send("2EP", 1)
        self.linearAxes.disable_joystick()
        self.linearAxes.send("QP", 1)

        self.linearAxes.send("3XX", 1)  # delete program 3
        # enter 'program mode' (automatically stored to non-volitile memory)
        self.linearAxes.send("3EP", 1)
        self.linearAxes.configure_axis('x', self.cfg['x_cfg'])
        self.linearAxes.configure_axis('y', self.cfg['y_cfg'])
        self.linearAxes.configure_axis('z', self.cfg['z_cfg'])
        self.linearAxes.send("QP", 1)  # quit 'program mode'
        self.linearAxes.send("3EO", 1)  # run program 1 on power-on
        self.linearAxes.save_settings_to_controller()
        self.linearAxes.send("3EX", 1)  # execute configure program

        self.headAxes.send("3XX", 1)  # delete program 3
        # enter 'program mode' (automatically stored to non-voltile memory)
        self.headAxes.send("3EP", 1)
        self.headAxes.configure_axis('w', self.cfg['w_cfg'])
        # b is already configured
        self.headAxes.send("QP", 1)  # quit ''program mode'
        self.headAxes.send("3EO", 1)  # run program 1 on power-on
        self.headAxes.save_settings_to_controller()
        self.headAxes.send("3EX", 1)  # execute configure program

    def enable_motors(self):
        self.linearAxes.enable_motor()
        self.headAxes.enable_motor()

    def disable_motors(self):
        self.linearAxes.disable_motor()
        self.headAxes.disable_motor()

    def motion_done(self):
        if self.cfg.get('fake', False):
            return True
        linearStatus = self.linearAxes.get_controller_status()
        headStatus = self.headAxes.get_controller_status()
        # 'left most ascii character'
        #     low = stationary, high = in motion
        #  0 : axis 1
        #  1 : axis 2
        #  2 : axis 3
        # print 'controller status:', ord(linearStatus[0]) \
        #        & 0x07, ord(headStatus[0]) & 0x07
        if ord(linearStatus[0]) & 0x07 or ord(headStatus[0]) & 0x07:
            return False
        else:
            return True
        #ret = self.linearAxes.motion_done()
        #ret.update(self.headAxes.motion_done())
        #for r in ret.values():
        #    if int(r) == 0:
        #        return False
        #return True

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
        # [x0, y0, z0, a, b, c]
        self.pathParams = fit_3d_line(tipLocations, wPositions)
        self.pathPoints = len(tipLocations)
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

    def calculate_point_rotation(self, deltaAngle, speed, tipOffset):
        """
        Due to the position of the rotation stage, this rotation moves
        the x, z and b axes
        """
        currArmLength = self.armLength - \
                float(self.headAxes.get_position('w')['w']) + tipOffset
        currAngle = float(self.headAxes.get_position('b')['b'])

        # get current virtual x,z position on rotation circle
        x0, z0 = point_on_circle(currAngle, currArmLength)
        # get target virtual x,z position on rotation circle
        x1, z1 = point_on_circle(currAngle + deltaAngle, currArmLength)

        dx, dz = x1 - x0, z1 - z0

        ttm = deltaAngle / speed
        xds = abs(dx / ttm)
        zds = abs(dz / ttm)

        return -dx, -dz, xds, zds  # fixing directions
