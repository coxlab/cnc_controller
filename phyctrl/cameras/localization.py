#!/usr/bin/env python

import logging
import os

import numpy
import cv

import calibration
import grid


class Localization(calibration.Calibration):
    def __init__(self, grid):
        super(Localization, self).__init__(grid)
        # self.grid = grid  # already in Calibration.__init__
        self.localized = False
        self.image = None

        self.r = cv.CreateMat(3, 1, cv.CV_64FC1)
        self.t = cv.CreateMat(3, 1, cv.CV_64FC1)

    def set_image(self, image, process=True):
        self.image = grid.GridImage(image, self.grid)
        if process:
            s, p = self.image.process()
            if s:
                logging.info("Found %i points in localization image" % len(p))
            else:
                logging.warning("Failed to find grid in localization image")
            return s

    def locate(self):
        assert self.image is not None, \
                "No localization image found, run set_image first"
        assert len(self.image.pts) == self.grid.n, \
                "Invalid number of grid points found %i != %i" % \
                (len(self.image.pts), self.grid.n)

        im_pts = cv.CreateMat(self.grid.n, 2, cv.CV_64FC1)
        obj_pts = cv.CreateMat(self.grid.n, 3, cv.CV_64FC1)

        for j in xrange(self.grid.n):
            im_pts[j, 0] = self.image.pts[j][0]
            im_pts[j, 1] = self.image.pts[j][1]
            obj_pts[j, 0] = (j % self.grid.width) * self.grid.size
            obj_pts[j, 1] = (j / self.grid.width) * self.grid.size
            obj_pts[j, 2] = 0.

        cv.FindExtrinsicCameraParams2(obj_pts, im_pts, self.cm,
                self.dc, self.r, self.t)

        # TODO print out rotation and translation vectors

        self.calculate_image_to_world()

    def calculate_image_to_world(self):
        rm = cv.CreateMat(3, 3, cv.CV_64FC1)
        cv.Rodrigues2(self.r, rm)
        self.image_to_world = calculate_image_to_world_matrix( \
                self.t, rm, self.cm)
        self.located = True

    def get_position(self):
        if self.located:
            return self.image_to_world[3, 0], self.image_to_world[3, 1], \
                    self.image_to_world[3, 2]
        else:
            logging.warning("get_position called with located = False")
            return numpy.nan, numpy.nan, numpy.nan

    def get_3d_position(self, x, y):
        if self.located:
            src = cv.CreateMat(1, 1, cv.CV_64FC2)
            dst = cv.CreateMat(1, 1, cv.CV_64FC2)
            src[0, 0] = (x, y)
            cv.UndistortPoints(src, dst, self.cm, self.dc)
            x, y = dst[0, 0]
            tp = numpy.array([x, y, 1., 1.])
            tr = numpy.array(tp * self.itoWMatrix)[0]
            return tr[0] / tr[3], tr[1] / tr[3], tr[2] / tr[3]
        else:
            logging.warning("get_3d_position called with located = False")
            return numpy.nan, numpy.nan, numpy.nan

    def save(self, directory):
        super(Localization, self).save(directory)
        if self.located:
            cv.SaveImage(os.path.join(directory, "localizationImage.png"), \
                    self.image.im)
            numpy.savetxt(os.path.join(directory, "localizationPts.pts"), \
                    numpy.array(self.image.pts))
            cv.Save(os.path.join(directory, "rVec.xml"), self.r)
            cv.Save(os.path.join(directory, "tVec.xml"), self.t)
            numpy.savetxt(os.path.join(directory, "itoWMatrix.np"), \
                    self.image_to_world)
            logging.debug("Saved localization to %s" % directory)
        else:
            logging.warning("located = False, not saving localization")

    def load(self, directory, recompute=False):
        super(Localization, self).save(directory, recompute)
        logging.debug("Loading localization from %s" % directory)
        if recompute:
            if self.set_image(cv.LoadImage(os.path.join(\
                    directory, "localizationImage.png")), process=True):
                self.locate()
                return True
            else:
                # failed to locate from loaded image
                return False
        else:
            self.r = cv.Load(os.path.join(directory, "rVec.xml"))
            self.t = cv.Load(os.path.join(directory, "tVec.xml"))
            self.image_to_world = numpy.loadtxt(os.path.join(\
                    directory, "itoWMatrix.np"))


def calculate_image_to_world_matrix(tVec, rMatrix, camMatrix):
    # open CV is [col,row]
    t = numpy.matrix([[1., 0., 0., 0.],
                    [0., 1., 0., 0.],
                    [0., 0., 1., 0.],
                    [cv.Get1D(tVec, 0)[0], \
                            cv.Get1D(tVec, 1)[0], cv.Get1D(tVec, 2)[0], 1.]])
    r = numpy.matrix([[cv.Get1D(rMatrix, 0)[0], cv.Get1D(rMatrix, 1)[0], \
                        cv.Get1D(rMatrix, 2)[0], 0.],
                [cv.Get1D(rMatrix, 3)[0], cv.Get1D(rMatrix, 4)[0], \
                        cv.Get1D(rMatrix, 5)[0], 0.],
                [cv.Get1D(rMatrix, 6)[0], cv.Get1D(rMatrix, 7)[0], \
                        cv.Get1D(rMatrix, 8)[0], 0.],
                [0., 0., 0., 1.]])
    info = t * r

    s = numpy.matrix([[1., 0., 0., 0.],
                [0., 1., 0., 0.],
                [0., 0., 1., 0.],
                [0., 0., 0., 1.]])
    s[0, 0] = -1.
    s[1, 1] = -1.
    s[2, 2] = -1.

    t = info * s
    info = t

    return info
