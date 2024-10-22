#!/usr/bin/env python

from PIL import Image
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
        #print self.fileList[self.fileIndex]
        #im = Image.open(self.fileList[self.fileIndex])
        try:
            im = Image.open(self.fileList[self.fileIndex])
            # frame = pylab.imread(self.fileList[self.fileIndex])
        except:
            try:
                self.fileIndex = 0
                im = Image.open(self.fileList[self.fileIndex])
                # frame = pylab.imread(self.fileList[self.fileIndex])
            except:
                print "File list:", self.fileList
                raise IOError, "Failed to find a valid frame"
        im.transpose(Image.FLIP_TOP_BOTTOM)
        frame = pylab.asarray(im)
        #print "loaded %s" % self.fileList[self.fileIndex]
        self.fileIndex += 1
        # convert frame to grayscale
        if len(frame.shape) == 3:
            frame = pylab.mean(frame, 2).astype(frame.dtype)
        # type conversion
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