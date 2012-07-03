#!/usr/bin/env python
"""
A fake cnc that keeps some internal state
"""

from base import Axis

default_state = {
        'power': False,
        'postition': 0.,
        'velocity': 0.
        }


class FakeAxis(Axis):
    def __init__(self, io, state=None):
        self._io = io
        self._state = default_state.copy()
        if state is None:
            state = {}
        self._state.update(state)

    def get_power(self):
        return self._state['power']

    def set_power(self, value):
        assert value in (True, False), "power must be True/False"
        self._state['power'] = value

    def get_position(self):
        return self._state['position']

    def get_moving(self):
        return False

    def get_velocity(self):
        return self._state['velocity']

    def set_velocity(self, value):
        value = float(value)
        self._state['velocity'] = value

    def move_relative(self, value):
        """Move axis value mm"""
        value = float(value)
        self._state['position'] += value
