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
        self._ai = axis_index
        if cfg is None:
            cfg = ""
        self._cfg = cfg

    def get_power(self):
        # TODO type conversion?
        return self._io.get_motor_status(self._ai)

    def set_power(self, value):
        assert value in (True, False), "power must be True/False"
        if value:
            self._io.enable_motor(self._ai)
        else:
            self._io.disable_motor(self._ai)

    power = property(get_power, set_power, \
            doc='Axis power: True=on, False=off')

    def get_position(self):
        return float(self._io.get_position(self._ai))

    position = property(get_position, doc="Axis position in mm")

    def get_moving(self):
        # TODO type conversion
        return self._io.motion_done(self._ai)

    moving = property(get_moving, doc="Is axis moving? True/False")

    def get_velocity(self):
        return float(self._io.get_velocity(self._ai))

    def set_velocity(self, value):
        value = float(value)
        self._io.set_velocity(self._ai, value)

    velocity = property(get_velocity, set_velocity, \
            doc="Axis velocity in mm/s")

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

    def enable_joystick(self):
        self._io.enable_joystick()

    def disable_joystick(self):
        self._io.disable_joystick()
