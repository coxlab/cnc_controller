#!/usr/bin/env python
"""
Newport ESP300/301 CNC plugin
"""

from base import Axis
from newportesp import NewportESP


class NewportAxis(Axis):
    def __init__(self, io, axis_index, cfg=None):
        assert isinstance(io, NewportESP), \
                "IO control must be of type NewportESP"
        super(NewportAxis, self).__init__(io)
        axis_index = int(axis_index)
        assert axis_index in io._axes, \
                "Invalid axis_index [%i], not in ESP axes[%s]" \
                % (axis_index, io._axes)
        self._ai = axis_index
        if cfg is None:
            cfg = ""
        self._cfg = cfg

    def get_power(self):
        # returns "1" or "0", convert to int, then bool
        return bool(int(self._io.get_motor_status(self._ai)))

    def set_power(self, value):
        assert value in (True, False), "power must be True/False"
        if value:
            self._io.enable_motor(self._ai)
        else:
            self._io.disable_motor(self._ai)

    def get_position(self):
        return float(self._io.get_position(self._ai))

    def get_moving(self, strict=False):
        """
        strict : True/False(default)
            Check only this axis, non-strict just checks all
        """
        # this is a bit ugly as motion done does not seem to do what I want
        # instead, get_controller_status
        # 'left most ascii character'
        #     low = stationary, high = in motion
        #  0 : axis 1
        #  1 : axis 2
        #  2 : axis 3
        s = self._io.get_controller_status()
        if strict:
            bm = (0b1 << (self._ai - 1))
        else:
            bm = 0b111
        return not bool(ord(s[0]) & bm)
        #return self._io.motion_done(self._ai)

    def get_velocity(self):
        return float(self._io.get_velocity(self._ai))

    def set_velocity(self, value):
        value = float(value)
        self._io.set_velocity(self._ai, value)

    def stop(self):
        """Stop axis"""
        self._io.stop_motion(self._ai)

    def move_relative(self, value):
        """Move axis value mm"""
        value = float(value)
        self._io.move_relative(self._ai, value)

    def configure(self):
        """Configure the axis"""
        self._io.configure_axis(self._ai, self._cfg)

    # --- Newport Specific ---

    def enable_joystick(self):
        self._io.enable_joystick()

    def disable_joystick(self):
        self._io.disable_joystick()