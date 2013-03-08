#!/usr/bin/env python

import os

import cconfig

import hwio
import swio

# TODO log to file


basecfg = os.path.join(
    os.path.dirname(
        os.path.realpath(
            __file__)), 'physio.ini')

print basecfg


class PhysioController(object):
    def __init__(self, cfg='~/.physio/cfg.ini'):
        self.cfg = cconfig.TypedConfig(base=basecfg,
                                       user='~/.physio/physio.ini',
                                       local='./physio.ini')

        # cameras
        self.cameras = hwio.cameras.open(self.cfg, 'cameras')

        # cnc
        self.cnc = hwio.cnc.open(self.cfg, 'cnc')

        # frames
        self.frames = swio.frames.load(self.cfg, 'frames')

        # mworks
        self.conduit = swio.conduit.load(self.cfg, 'conduit')

        # animal loading
        # path & reg points
        # update position (main update)
        # log loading/saving

        # -- passive displays --
        # atlas view (move this outside??)
        # mesh view
        pass
