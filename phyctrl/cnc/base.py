#!/usr/bin/env python
"""
CNC interaction should be as simple as possible.

At the moment the following controls are used:
    Move Relative
    Motion Done
    Stop Motion

    On/Off
    Get Motor Status

    Get Position

    Set Velocity
    Get Velocity
    Configure
    Enable/Disable Joystick

    Measure Tip Path (should be pulled out)
    Calculate Point Rotation (should be pulled out)
    Path Params (should be pulled out)

So it looks like motors should have the following properties:
    power (get/set)

    position (get)

    moving (get)

    move_relative (func)
    stop (func)
    configure (func)

    velocity (get/set)

    joystick (set) [newport specific?]
"""


class Axis(object):
    def __init__(self, io):
        self._io = io

    def get_power(self):
        pass

    def set_power(self, value):
        assert value in (True, False), "power must be True/False"

    power = property(get_power, set_power, \
            doc='Axis power: True=on, False=off')

    def get_position(self):
        pass

    position = property(get_position, doc="Axis position in mm")

    def get_moving(self):
        pass

    moving = property(get_moving, doc="Is axis moving? True/False")

    def get_velocity(self):
        pass

    def set_velocity(self, value):
        value = float(value)

    velocity = property(get_velocity, set_velocity, \
            doc="Axis velocity in mm/s")

    def stop(self):
        """Stop axis"""
        pass

    def move_relative(self, value):
        """Move axis value mm"""
        value = float(value)

    def configure(self):
        """Configure the axis"""
        pass
