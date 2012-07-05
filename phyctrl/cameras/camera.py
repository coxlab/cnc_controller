#!/usr/bin/env python


class Camera(object):
    def __init__(self, io, localization):
        self._io = io
        self._loc = localization

    def capture(self, undistort=False):
        # self._io.capture should return a Ipl image
        if undistort:
            return self._loc.undistort_image(self._io.capture())
        return self._io.capture()

#    def start_streaming(self):
#        return self._io.start_streaming()
#
#    def stop_streaming(self):
#        return self._io.stop_streaming()
#
#    def poll_streaming(self):
#        return self._io.poll_streaming()

    # used for intersection i.e. stereo localization
    def get_position(self):
        return self._loc.get_position()

    def get_3d_position(self, x, y):
        return self._loc.get_3d_position(x, y)
