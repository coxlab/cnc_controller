#!/usr/bin/env python

import os

import numpy
import cv

import conversions


class CalibrationImage(object):
    def __init__(self, im, grid):
        self.im = im
        self.grid = grid
        self._pts = None

    def get_pts(self):
        if self._pts is None:
            s, self._pts = grid.find(self.im)
        return self._pts

    pts = property(get_pts, doc="Location of grid intersections")


class Calibration(object):
    def __init__(self):
        self.calibrated = False
        self.images = []
        self.pts = []

        # TODO make these defaults
        self.camMatrix = None
        self.distCoeffs = None

    def undistort_image(self, image):
        undistortedImage = cv.CreateImage((image.width, image.height),
                                            image.depth, image.nChannels)
        cv.Undistort2(image, undistortedImage, self.camMatrix, self.distCoeffs)
        return undistortedImage

    def capture_grid_image(self, gridSize):
        #if not self.calibrated:
        #    raise IOError('Camera must be calibrated before capturing grid')

        image = self.capture(undistort=False)
        success, corners = cv.FindChessboardCorners(image, gridSize)

        if not success:
            return image, corners, False

        corners = cv.FindCornerSubPix(image, corners, (11, 11), (-1, -1),
                    (cv.CV_TERMCRIT_EPS + cv.CV_TERMCRIT_ITER, 30, 0.01))

        gridN = gridSize[0] * gridSize[1]
        if len(corners) != gridN:
            return image, corners, False

        # xs should be ascending
        if corners[0][0] > corners[1][0]:
            #print "flipping rows"
            for r in xrange(gridSize[1]):
                for c in xrange(gridSize[0] / 2):
                    i = c + r * gridSize[0]
                    i2 = (gridSize[0] - c - 1) + r * gridSize[0]
                    o = corners[i]
                    corners[i] = corners[i2]
                    corners[i2] = o

        # ys should be descending
        if corners[0][1] > corners[gridSize[0]][1]:
            #print "flipping columns"
            for c in xrange(gridSize[0]):
                for r in xrange(gridSize[1] / 2):
                    i = c + r * gridSize[0]
                    i2 = c + (gridSize[1] - r - 1) * gridSize[0]
                    o = corners[i]
                    corners[i] = corners[i2]
                    corners[i2] = o

        return image, corners, True

    # ============================================
    #           Calibration
    # ============================================
    def capture_calibration_image(self, gridSize):
        image, corners, success = self.capture_grid_image(gridSize)
        if not success:
            return image, False

        self.calibrationImages.append(image)
        self.calibrationImgPts.append(corners)
        return image, True

    def remove_last_calibration_point(self):
        self.calibrationImages.pop()
        self.calibrationImgPts.pop()

    def calibrate(self, gridSize, gridBlockSize):
        errs = self.calibrate_internals(gridSize, gridBlockSize)
        if self.logDir != None:
            self.save_calibration("%s/calibration/" % self.logDir)
        return errs

    def calibrate_internals(self, gridSize, gridBlockSize):
        # initialize camera matrices
        self.camMatrix = cv.CreateMat(3, 3, cv.CV_64FC1)
        cv.SetZero(self.camMatrix)
        self.camMatrix[0, 0] = 1.
        self.camMatrix[1, 1] = 1.
        self.distCoeffs = cv.CreateMat(5, 1, cv.CV_64FC1)
        cv.SetZero(self.distCoeffs)

        nGrids = len(self.calibrationImages)
        gridN = gridSize[0] * gridSize[1]

        imPts = cv.CreateMat(nGrids * gridN, 2, cv.CV_64FC1)
        objPts = cv.CreateMat(nGrids * gridN, 3, cv.CV_64FC1)
        ptCounts = cv.CreateMat(nGrids, 1, cv.CV_32SC1)

        # organize self.calibrationImgPts (to imPts) and
        # construct objPts and ptCounts
        for (i, c) in enumerate(self.calibrationImgPts):
            for j in xrange(gridN):
                imPts[j + i * gridN, 0] = c[j][0]
                imPts[j + i * gridN, 1] = c[j][1]
                objPts[j + i * gridN, 0] = (j % gridSize[0]) * gridBlockSize
                objPts[j + i * gridN, 1] = (j / gridSize[0]) * gridBlockSize
                objPts[j + i * gridN, 2] = 0.
            ptCounts[i, 0] = len(c)

        cv.CalibrateCamera2(objPts, imPts, ptCounts, self.imageSize,
            self.camMatrix, self.distCoeffs,
            cv.CreateMat(nGrids, 3, cv.CV_64FC1),
            cv.CreateMat(nGrids, 3, cv.CV_64FC1), 0)

        # camera is now calibrated
        self.calibrated = True

        errs = self.measure_calibration_error(gridSize, gridBlockSize)
        return errs

    def measure_calibration_error(self, gridSize, gridBlockSize):
        if not self.calibrated:
            raise Exception("Attempted to measure calibration "
            "error of uncalibrated camera")
        gridN = gridSize[0] * gridSize[1]
        errs = []
        for (i, im) in enumerate(self.calibrationImages):
            # im = image with chessboard
            corners = self.calibrationImgPts[i]
            imPts = cv.CreateMat(gridN, 2, cv.CV_64FC1)
            objPts = cv.CreateMat(gridN, 3, cv.CV_64FC1)
            for j in xrange(gridN):
                imPts[j, 0] = corners[j][0]
                imPts[j, 1] = corners[j][1]
                objPts[j, 0] = (j % gridSize[0]) * gridBlockSize
                objPts[j, 1] = (j / gridSize[0]) * gridBlockSize
                objPts[j, 2] = 0.

            # measure rVec and tVec for this image
            rVec = cv.CreateMat(3, 1, cv.CV_64FC1)
            tVec = cv.CreateMat(3, 1, cv.CV_64FC1)
            cv.FindExtrinsicCameraParams2(objPts, imPts, self.camMatrix,
                self.distCoeffs, rVec, tVec)

            # reproject points
            pimPts = cv.CreateMat(gridN, 2, cv.CV_64FC1)
            cv.ProjectPoints2(objPts, rVec, tVec, \
                    self.camMatrix, self.distCoeffs, pimPts)

            # measure error
            err = []
            for j in xrange(gridN):
                err.append([imPts[j, 0] - pimPts[j, 0], \
                        imPts[j, 1] - pimPts[j, 1]])

            errs.append(err)

        return errs

    def save_calibration(self, directory):
        if not self.calibrated:
            raise Exception("Attempted to save calibration of "
            "uncalibrated camera")

        directory = "%s/%i" % (directory, self.camID)

        if not os.path.exists(directory):
            os.makedirs(directory)
        if not os.path.exists("%s/images" % directory):
            os.makedirs("%s/images" % directory)

        cv.Save("%s/camMatrix.xml" % directory, self.camMatrix)
        cv.Save("%s/distCoeffs.xml" % directory, self.distCoeffs)
        for (i, im) in enumerate(self.calibrationImages):
            cv.SaveImage("%s/images/%i.png" % (directory, i), im)
            corners = numpy.array(self.calibrationImgPts[i])
            numpy.savetxt("%s/images/%i.pts" % (directory, i), corners)

        if self.located:
            cv.SaveImage("%s/localizationImage.png" % (directory), \
                    self.localizationImage)
            numpy.savetxt("%s/localizationPts.pts" % (directory), \
                    numpy.array(self.localizationCorners))
            cv.Save("%s/rVec.xml" % directory, self.rVec)
            cv.Save("%s/tVec.xml" % directory, self.tVec)
            cv.Save("%s/itoWMatrix.xml" % directory, \
                    conversions.NumPytoCV(self.itoWMatrix))

    def load_calibration(self, directory):
        directory = "%s/%i" % (directory, self.camID)

        self.camMatrix = cv.Load("%s/camMatrix.xml" % directory)
        self.distCoeffs = cv.Load("%s/distCoeffs.xml" % directory)
        self.calibrated = True

        if os.path.exists("%s/itoWMatrix.xml" % directory):
            self.rVec = cv.Load("%s/rVec.xml" % directory)
            self.tVec = cv.Load("%s/tVec.xml" % directory)
            # self.itoWMatrix = \
            #        conversions.CVtoNumPy(cv.Load("%s/itoWMatrix.xml" % \
            #        directory))
            # print self.itoWMatrix
            rMatrix = cv.CreateMat(3, 3, cv.CV_64FC1)
            cv.Rodrigues2(self.rVec, rMatrix)
            self.itoWMatrix = calculate_image_to_world_matrix(\
                    self.tVec, rMatrix, self.camMatrix)
            self.located = True

        #print "RADAR: Faking distCoeffs"
        #self.distCoeffs[0,0] = 0.#0.25
        #self.distCoeffs[1,0] = 0.#-10.#-30.
        #self.distCoeffs[2,0] = 0.#-0.02
        #self.distCoeffs[3,0] = 0.#-0.01
        #self.distCoeffs[4,0] = 0.
