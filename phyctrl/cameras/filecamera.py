#!/usr/bin/env python

import glob
import os

import cv


class FileIO(object):
    def __init__(self, directory='.', pattern='[0-9].png'):
        self.directory = directory
        self.connected = False
        self.filenames = sorted(glob.glob(os.path.join(directory, pattern)))
        assert len(self.filenames) > 0, "0 images found in %s with pattern %s"\
                % (directory, pattern)
        self.index = 0

    def connect(self):
        self.connected = True
        return True

    def disconnect(self):
        self.connected = False
        return True

    def capture(self):
        fn = self.filenames[self.index]
        self.index += 1
        if self.index >= len(self.filenames):
            self.index -= len(self.filenames)
        return cv.LoadImage(fn)
