#!/usr/bin/env python

import glob
import logging
import os

import numpy
import cv

import grid


class Calibration(object):
    def __init__(self, grid):
        self.calibrated = False
        self.images = []
        self.grid = grid

        self.setup_matrices()

    def setup_matrices(self):
        self.cm = cv.CreateMat(3, 3, cv.CV_64FC1)
        cv.SetZero(self.cm)
        self.cm[0, 0] = 1.
        self.cm[1, 1] = 1.
        self.dc = cv.CreateMat(5, 1, cv.CV_64FC1)
        cv.SetZero(self.dc)

    def undistort_image(self, image):
        undistortedImage = cv.CreateImage((image.width, image.height),
                                            image.depth, image.nChannels)
        cv.Undistort2(image, undistortedImage, self.cm, self.dc)
        return undistortedImage

    def add_image(self, image, process=False):
        self.images.append(grid.GridImage(image, self.grid))
        if process:
            s, p = self.images[-1].process()
            if s:
                logging.info("Found %i points in image %i" % \
                        (len(p), len(self.images)))
            else:
                logging.warning("Failed to find grid in image %i" % \
                        (len(self.images)))
            return s

    def remove_image(self, index=0):
        self.images.pop(index)
        logging.debug("Removed image %i" % index)

    def calibrate(self):
        assert len(self.images) > 0, "Cannot calibrate with 0 images"
        if len(self.images) < 7:
            logging.warn("Attempt to calibrate %s with %i < 7 images" % \
                    (self, len(self.images)))
        errs = self.calibrate_internals()
        return errs

    def calibrate_internals(self):
        ngrids = len(self.images)

        im_pts = cv.CreateMat(ngrids * self.grid.n, 2, cv.CV_64FC1)
        obj_pts = cv.CreateMat(ngrids * self.grid.n, 3, cv.CV_64FC1)
        pt_counts = cv.CreateMat(ngrids, 1, cv.CV_32SC1)

        # organize self.im.pts (to im_pts) and
        # construct obj_pts and pt_counts
        for (i, im) in enumerate(self.images):
            for j in xrange(self.grid.n):
                im_pts[j + i * self.grid.n, 0] = im.pts[j][0]
                im_pts[j + i * self.grid.n, 1] = im.pts[j][1]
                obj_pts[j + i * self.grid.n, 0] = \
                        (j % self.grid.width) * self.grid.size
                obj_pts[j + i * self.grid.n, 1] = \
                        (j / self.grid.width) * self.grid.size
                obj_pts[j + i * self.grid.n, 2] = 0.
            pt_counts[i, 0] = len(im.pts)

        # get image size
        im_size = (self.images[0].im.width, self.images[0].im.height)

        # calibrate
        cv.CalibrateCamera2(obj_pts, im_pts, pt_counts, im_size,
            self.cm, self.dc,
            cv.CreateMat(ngrids, 3, cv.CV_64FC1),
            cv.CreateMat(ngrids, 3, cv.CV_64FC1), 0)

        # camera is now calibrated
        self.calibrated = True
        # TODO print out camera matrix and distortion coefficients

        errs = self.measure_calibration_error()
        return errs

    def measure_calibration_error(self):
        if not self.calibrated:
            logging.warning("measure_calibration_error called "
            "when calibrated = False")
            return numpy.nan

        # pre-allocate
        im_pts = cv.CreateMat(self.grid.n, 2, cv.CV_64FC1)
        obj_pts = cv.CreateMat(self.grid.n, 3, cv.CV_64FC1)
        r = cv.CreateMat(3, 1, cv.CV_64FC1)
        t = cv.CreateMat(3, 1, cv.CV_64FC1)
        pim_pts = cv.CreateMat(self.grid.n, 2, cv.CV_64FC1)
        errs = []

        # setup object points
        for j in xrange(self.grid.n):
            obj_pts[j, 0] = (j % self.grid.width) * self.grid.size
            obj_pts[j, 1] = (j / self.grid.width) * self.grid.size
            obj_pts[j, 2] = 0.

        # for each image, locate the camera, and reproject the points
        for (i, im) in enumerate(self.images):
            pts = im.pts
            for j in xrange(self.grid.n):
                im_pts[j, 0] = pts[j][0]
                im_pts[j, 1] = pts[j][1]

            cv.FindExtrinsicCameraParams2(obj_pts, im_pts, self.cm,
                self.dc, r, t)

            cv.ProjectPoints2(obj_pts, r, t, self.cm, self.dc, pim_pts)

            err = []
            for j in xrange(self.grid.n):
                err.append([im_pts[j, 0] - pim_pts[j, 0], \
                        im_pts[j, 1] - pim_pts[j, 1]])

            de = numpy.sqrt(numpy.sum(numpy.array(err) ** 2., 1))
            me, se = numpy.mean(de), numpy.std(de)

            logging.debug("Reprojection error for image %i: "
            "mean=%.2f, std=%.2f [pixels]" % (i, me, se))

            errs.append(err)

        aerrs = numpy.array(errs)
        de = numpy.sqrt(numpy.sum(aerrs.reshape(aerrs.size / 2, 2) ** 2., 1))
        me, se = numpy.mean(de), numpy.std(de)
        logging.info("Reprojection error across all images: "
        "mean=%.2f, std=%.2f [pixels]" % (me, se))

        return errs

    def save(self, directory):
        # save the following
        # 1) self.cm (camera matrix, cvMatrix)
        # 2) self.dc (distortion coefficients, cvMatrix)
        # 3) self.images (calibration images, grid.GridImage)
        if not os.path.exists(directory):
            os.makedirs(directory)
        imdir = os.path.join(directory, "images")
        if not os.path.exists(imdir):
            os.makedirs(imdir)

        cv.Save(os.path.join(directory, "camMatrix.xml"), self.cm)
        cv.Save(os.path.join(directory, "distCoeffs.xml"), self.dc)
        for (i, im) in enumerate(self.images):
            cv.SaveImage(os.path.join(imdir, "%i.png" % i), im.im)
            pts = numpy.array(im.pts)
            numpy.savetxt(os.path.join(imdir, "%i.pts" % i), pts)
        logging.debug("Saved calibration to %s" % directory)

    def load(self, directory, recompute=False):
        # load the following
        # 1) self.cm (camera matrix, cvMatrix)
        # 2) self.dc (distortion coefficients, cvMatrix)
        # 3) self.images (calibration images, grid.GridImage)
        logging.debug("Loading calibration from %s" % directory)
        if not os.path.exists(directory):
            raise IOError("Cannot load calibration, "
            "directory %s does not exist" % directory)
        if recompute:
            r = {}  # key=image filename, value=found grid?
            for imfn in sorted(glob.glob(os.path.join(\
                    directory, "images", "[0-9]*.png"), \
                    key=lambda fn: int(os.path.splitext(\
                    os.path.basename(fn))[0]))):
                s = self.add_image(cv.LoadImage(imfn), process=True)
                r[imfn] = s
            return r, self.calibrate()
        else:
            self.cm = cv.Load(os.path.join(directory, "camMatrix.xml"))
            self.dc = cv.Load(os.path.join(directory, "distCoeffs.xml"))
            self.calibrated = True
