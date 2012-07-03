#!/usr/bin/env python

import zmq

import camera


class ZMQCamera(camera.Camera):
    def connect(self, cmd, publish, context=None):
        if context is None:
            context = zmq.Context()
        self._zcmd = zmq.Socket(context, zmq.REP)
        self._zcmd.bind(cmd)

        self._zpub = zmq.Socket(context, zmq.PUB)
        self._zpub.bind(publish)

    def process_incoming(self):
        pass

    def publish_image(self):
        im = self.capture_frame()
