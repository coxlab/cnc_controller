#!/usr/bin/env python

import pydc1394

import camera

# clean up the iso bus in case the previous time this program was open it crashed
l = pydc1394.DC1394Library()
cids = l.enumerate_cameras()
cams = [pydc1394.Camera(l,cid['guid']) for cid in cids]
[cam.close() for cam in cams]
del cams
l.close()
del l 

global dc1394
dc1394 = pydc1394.DC1394Library()

def close_dc1394():
    global dc1394
    #print "closing dc1394"
    dc1394.close()
    #print "deleting dc1394"
    del dc1394


class DC1394Camera(camera.Camera, pydc1394.Camera):
    def __init__(self, camID=None):
        global dc1394
        if camID == None:
            cams = dc1394.enumerate_cameras()
            if len(cams) < 1:
                raise IOError, "No Camera Found"
            camID = cams[0]['guid']
        camera.Camera.__init__(self, camID)
        pydc1394.Camera.__init__(self, dc1394, camID)
        self.set_mode()
        self.configure()
        self.connected = True
        self.frameID = 0 # maybe move this to camera superclass
    
    def set_mode(self):
        self.mode = [m for m in self.modes if m.name == 'FORMAT7_0'][0]
    
    def configure(self):
        self.trigger.on = False
        self.exposure.on = False
        self.shutter.mode = 'manual'
        self.shutter.val = 100.
        self.mode.roi = ((1392, 1040), (0,0), 'Y8', -3)
        # self.framerate.mode = 'manual'
        # self.framerate.val = 0.5#1.0
        # self.exposure.mode = 'manual'
        # self.exposure.val = 1.#1.
        # self.shutter.mode = 'manual'
        # self.shutter.val = 1000#533
    
    def connect(self):
        if self.connected:
            return True
    
    def disconnect(self):
        if self.connected == True:
            self.close()
            self.connected = False
    
    def start_streaming(self):
        self.start(interactive=True)
        self.streaming = True
    
    def stop_streaming(self):
        self.stop()
        self.streaming = False
    
    def poll_stream(self):
        if self.streaming == False:
            return None
        self._new_image.acquire()
        i = self._current_img
        if i != None and i._id != self.frameID:
            self._new_image.release()
            self.frameID = i._id
            return i
        else:
            self._new_image.release()
            return None
    
    def set_shutter(self, value)
        self.shutter.val = value
        self.mode.roi = ((1392, 1040), (0,0), 'Y8', -3)
    
    def capture_frame(self):
        if self.streaming == False:
            self.start_streaming()
            self._new_image.acquire()
            i = self._current_img
            while i == None:
                cam._new_image.wait()
                i = self._current_img
            self._new_image.release()
            self.stop_streaming()
            return i
        else:
            self._new_image.acquire()
            i = self._current_img
            while i == None:
                cam._new_image.wait()
                i = self._current_img
            self._new_image.release()
            return i
        
        # TODO test
        # i'm not 100% sure that the settings have enought time to take effect with this,
        # it might be better to pull apart the start/stop iso transmission and capture so
        # that I start transmission, configure, allow time for settings to take effect and
        # then capture
        self.start()
        self.configure()
        i = self.shot().reshape((1040,1392))#.reshape((1040,1392)).astype('uint8')
        self.stop()
        
        #print i.dtype
        if i.dtype != 'uint8':
            i = (i * 2.**-8.).astype('uint8')
        #print i.dtype
        
        #print "max,min:", i.max(), i.min()
        #pylab.ion()
        #pylab.figure()
        #pylab.subplot(131)
        #pylab.imshow(i[:100,:100])
        #i = i.reshape((1040,1392))
        #pylab.subplot(132)
        #pylab.imshow(i[:100,:100])
        #i = (i * 2.**-8.).astype('uint8')
        #pylab.subplot(133)
        #pylab.imshow(i[:100,:100])
        
        return i#(i * 2.**-8.).astype('uint8')