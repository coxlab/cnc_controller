#!/usr/bin/env python

import pylab

import camera

class StringCamera(camera.Camera):
    def __init__(self, camID=None):
        camera.Camera.__init__(self, camID)
        self.stringBuffer = None
        self.stringBufferShape = None
        self.stringBufferType = None
        self.connected = True
    def set_string_buffer(self, stringBuffer, stringBufferShape, stringBufferType):
        self.stringBuffer = stringBuffer
        self.stringBufferShape = stringBufferShape
        self.stringBufferType = stringBufferType
    def connect(self):
        self.connected = True
    def disconnect(self):
        self.connected = False
    def capture_frame(self):
        if self.stringBuffer == None:
            print "String Buffer == None!"
            raise IOError, "String buffer must be set before capture"
        frame = pylab.fromstring(self.stringBuffer, dtype=self.stringBufferType)
        frame = pylab.reshape(frame,self.stringBufferShape)
        if len(frame.shape) == 3:
            frame = pylab.mean(frame, 2).astype(frame.dtype)
        if frame.dtype in ['float32', 'float64']:
            frame = (frame * 255).astype('uint8')
        return frame

# =========================================================================================
# =========================================================================================
# ================================== Testing ==============================================
# =========================================================================================
# =========================================================================================

if __name__ == '__main__':
    pass