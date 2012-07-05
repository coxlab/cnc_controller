#!/usr/bin/env python

import pydc1394

import conversions

global dc1394
dc1394 = None


def open_dc1394():
    global dc1394
    if dc1394 is not None:
        return
    dc1394 = pydc1394.DC1394Library()


open_dc1394()


def close_dc1394():
    global dc1394
    if dc1394 is None:
        return
    dc1394.close()
    del dc1394
    global dc1394
    dc1394 = None


def restart_dc1394():
    close_dc1394()
    open_dc1394()


def flush_dc1394():
    restart_dc1394()
    global dc1394
    cams = [pydc1394.Camera(dc1394, cid['guid']) for cid in \
            dc1394.enumerate_cameras()]
    [cam.close() for cam in cams]
    del cams
    restart_dc1394()


class DC1394IO(object):
    def __init__(self, guid=None):
        if guid is None:
            global dc1394
            cids = dc1394.enumerate_cameras()
            if len(cids) == 0:
                raise IOError("No dc1394 cameras found")
            guid = cids[0]['guid']
        self.guid = guid
        self.connected = False
        self.cam = None

    def connect(self):
        global dc1394
        self.cam = pydc1394.Camera(dc1394, self.guid)
        self.connected = True
        return True

    def disconnect(self):
        if self.cam is not None:
            pass
        self.connected = False
        return True

    def capture(self):
        if not self.connected:
            raise IOError("capture called when connected = False")
        self.cam.start(interactive=False)
        im = self.cam.shot()
        self.cam.stop()
        # convert to cv
        return conversions.NumPy2Ipl(im)

    def configure(self):
        self.set_mode()
        self.set_parameters()
        self.set_shutter(800)

    def print_features(self):
        for feature in self.cam.features:
            f = self.cam.__getattribute__(feature)
            print "%s:" % feature
            print " Value:", f.val
            print " On?  :", f.on
            print " OnOff:", f.can_be_disabled
            print " Mode :", f.mode
            print " Modes:", f.pos_modes
            if feature != 'trigger':
                print " Range:", f.range
            print

    def set_mode(self):
        self.cam.mode = [m for m in self.cam.modes if m.name == 'FORMAT7_0'][0]

    def set_parameters(self):
        self.cam.trigger.on = False
        self.cam.exposure.on = True
        self.cam.exposure.mode = 'manual'
        self.cam.exposure.val = 0.
        self.cam.framerate.on = False
        self.cam.shutter.mode = 'manual'

    def set_shutter(self, value):
        if value == self.cam.shutter.val:
            # no need to change the values that already agree
            return self.cam.shutter.val
        self.cam.shutter.val = value
        u, s = self.cam.mode.packet_parameters
        print "Max Packet Size %i, Packet Unit %i" % (s, u)
        print "Recommended Packet Size %i" % \
                self.cam.mode.recommended_packet_size
        ps = int(self.cam.mode.recommended_packet_size * .4)
        ps = ps - ps % u
        self.cam.mode.roi = ((1392, 1040), (0, 0), 'Y8', ps)
        return self.cam.shutter.val
