#!/usr/bin/env python

import pylab

import camera

class FileCamera(camera.Camera):
    def __init__(self, camID=None):
        camera.Camera.__init__(self, camID)
        self.fileIndex = 0
        self.fileList = []
        self.connected = True
    def set_file_list(self, fileList):
        self.fileList = fileList
        self.connected = True
    def connect(self):
        self.connected = True
    def disconnect(self):
        self.connected = False
    def capture_frame(self):
        try:
            frame = pylab.imread(self.fileList[self.fileIndex])
        except:
            try:
                self.fileIndex = 0
                frame = pylab.imread(self.fileList[self.fileIndex])
            except:
                print "File list:", self.fileList
                raise IOError, "Failed to find a valid frame"
        self.fileIndex += 1
        
        # convert frame to grayscale
        if len(frame.shape) == 3:
            frame = pylab.mean(frame, 2)
        
        return frame.astype('uint8')

# =========================================================================================
# =========================================================================================
# ================================== Testing ==============================================
# =========================================================================================
# =========================================================================================

if __name__ == '__main__':
    pass