#!/usr/bin/env python

import cv

import conversions


class Grid(object):
    def __init__(self, size, width, height):
        self.size = float(size)
        self.width = int(width)
        self.height = int(height)
        self.n = self.width * self.height

    def find(self, image):
        if image.nChannels != 1:
            # convert to grayscale
            image = conversions.to_grayscale(image)

        success, corners = cv.FindChessboardCorners(image, \
                (self.width, self.height))
        if not success:
            return False, []
        corners = cv.FindCornerSubPix(image, corners, (11, 11), (-1, -1),
                    (cv.CV_TERMCRIT_EPS + cv.CV_TERMCRIT_ITER, 30, 0.01))
        if len(corners) != self.n:
            return False, corners

        return True, self.sort_corners(corners)

    def sort_corners(self, corners):
        # xs should be ascending
        if corners[0][0] > corners[1][0]:
            #print "flipping rows"
            for r in xrange(self.height):
                for c in xrange(self.width / 2):
                    i = c + r * self.width
                    i2 = (self.width - c - 1) + r * self.width
                    o = corners[i]
                    corners[i] = corners[i2]
                    corners[i2] = o

        # ys should be descending
        if corners[0][1] > corners[self.width][1]:
            #print "flipping columns"
            for c in xrange(self.width):
                for r in xrange(self.height / 2):
                    i = c + r * self.width
                    i2 = c + (self.height - r - 1) * self.width
                    o = corners[i]
                    corners[i] = corners[i2]
                    corners[i2] = o

        return corners


class GridImage(object):
    def __init__(self, im, grid):
        self.im = cv.CloneImage(im)
        self.grid = grid
        self._pts = None

    def process(self):
        s, self._pts = self.grid.find(self.im)
        return s, self._pts

    def get_pts(self):
        if self._pts is None:
            self.process()  # sets self._pts
        return self._pts

    pts = property(get_pts, doc="Location of grid intersections")
