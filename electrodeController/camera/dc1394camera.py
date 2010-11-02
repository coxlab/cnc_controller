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
        #self.configure()
    
    def configure(self):
        self.trigger.on = False
        self.exposure.on = True
        self.exposure.mode = 'manual'
        self.exposure.val = 0.
        self.framerate.on = False
        self.shutter.mode = 'manual'
        self.shutter.val = 100.
        u, s = self.mode.packet_parameters
        print "Max Packet Size %i, Packet Unit %i" % (s, u)
        #fps = (1. / self.shutter.val)
        #NP = min(int(1./(0.000125/fps) + 0.5), 4096)
        #d = NP*8
        #ps = (1392 * 1040 * 8 + d - 1)/d
        #ps = min((ps + ps % u, s))/2
        #print "Calculated Packet Size %i, N Packets %i, for fps %.3f" % (ps, NP, fps)
        print "Recommended Packet Size %i" % self.mode.recommended_packet_size
        ps = int(self.mode.recommended_packet_size * .4)
        ps = ps - ps % u
        self.mode.roi = ((1392, 1040), (0,0), 'Y8', ps)
        self.print_features()
        # self.framerate.mode = 'manual'
        # self.framerate.val = 0.5#1.0
        # self.exposure.mode = 'manual'
        # self.exposure.val = 1.#1.
        # self.shutter.mode = 'manual'
        # self.shutter.val = 1000#533
    
    def print_features(self):
        for feature in self.features:
            f = self.__getattribute__(feature)
            print "%s:" % feature
            print " Value:", f.val
            print " On?  :", f.on
            print " OnOff:", f.can_be_disabled
            print " Mode :", f.mode
            print " Modes:", f.pos_modes
            if feature != 'trigger':
                print " Range:", f.range
            print
    
    def connect(self):
        if self.connected:
            return True
    
    def disconnect(self):
        if self.connected == True:
            if self.streaming == True:
                self.stop_streaming()
            self.close()
            self.connected = False
    
    def start_streaming(self, interactive=True):
        self.start(interactive=interactive)
        self.streaming = True
    
    def stop_streaming(self):
        self.stop()
        self.streaming = False
    
    def poll_stream(self):
        if self.streaming == False:
            #print "not streaming exitting"
            return None
        #print "acquiring lock"
        self._new_image.acquire()
        #print "grabbing image"
        i = self._current_img
        #print "i =", i
        if i != None and i._id != self.frameID:
            #print "found frame:", i._id
            self._new_image.release()
            self.frameID = i._id
            return i
        else:
            #print "no good frame found"
            self._new_image.release()
            return None
    
    def set_shutter(self, value):
        if value == self.shutter.val:
            # no need to change the values that already agree
            return self.shutter.val
        self.shutter.val = value
        #s, u = self.mode.packet_parameters
        #self.mode.roi = ((1392, 1040), (0,0), 'Y8', s/2)
        u, s = self.mode.packet_parameters
        print "Max Packet Size %i, Packet Unit %i" % (s, u)
        #fps = (1. / self.shutter.val)
        #NP = min(int(1./(0.000125/fps) + 0.5), 4096)
        #d = NP*8
        #ps = (1392 * 1040 * 8 + d - 1)/d
        #ps = min((ps + ps % u, s))/2
        #print "Calculated Packet Size %i, N Packets %i, for fps %.3f" % (ps, NP, fps)
        print "Recommended Packet Size %i" % self.mode.recommended_packet_size
        ps = int(self.mode.recommended_packet_size * .4)
        ps = ps - ps % u
        if self.streaming:
            self.stop_streaming()
            self.mode.roi = ((1392, 1040), (0,0), 'Y8', ps)
            self.start_streaming()
        else:
            self.mode.roi = ((1392, 1040), (0,0), 'Y8', ps)
        #self.print_features()
        return self.shutter.val
    
    def capture_frame(self):
        if self.streaming == False:
            self.start_streaming(interactive=False)
            i = self.shot()
            self.stop_streaming()
            ##print "started streaming"
            #self._new_image.acquire()
            ##print "acquired lock"
            #i = self._current_img
            ##print "i =", i
            #while i == None:
            #    #print "waiting..."
            #    self._new_image.wait()
            #    i = self._current_img
            #    #print "i =", i
            #self._new_image.release()
            ##print "releaseed"
            #self.stop_streaming()
            ##print "stopped streaming"
            return i
        else:
            self._new_image.acquire()
            i = self._current_img
            while i == None:
                self._new_image.wait()
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