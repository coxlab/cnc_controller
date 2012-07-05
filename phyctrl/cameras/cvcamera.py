#!/usr/bin/env python

import cv


class CVIO(object):
    def __init__(self, index=0):
        self.index = index
        self.connected = False
        self.cap = None

    def connect(self):
        self.cap = cv.CreateCameraCapture(self.index)
        self.connected = True
        return True

    def disconnect(self):
        if hasattr(cv, "ReleaseCapture"):
            cv.ReleaseCapture(self.cap)
        else:
            del self.cap
        self.cap = None
        return True

    def capture(self):
        if not self.connected:
            raise IOError("capture called when connected = False")
        return cv.QueryFrame(self.cap)

#    def get_streaming(self):
#        return self._streaming
#
#    def set_streaming(self, value):
#        value = bool(value)
#        self._streaming = value
#
#    streaming = property(get_streaming, set_streaming, \
#            doc="Stream camera images")
