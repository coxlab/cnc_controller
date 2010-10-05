#!/usr/bin/env python

import os

import numpy
import cv

import conversions

class Camera:
    def __init__(self, camID=None):
        self.connected = False
        self.calibrated = False
        self.located = False
        
        self.logDir = None
        
        self.imageSize = (-1, -1)
        self.camID = camID
        
        # for calibration
        self.calibrationImages = []
        self.calibrationImgPts = []
        
        # for localization
        self.localizationImage = None
        self.localizationCorners = None
    
    
    # ==== Override these ====
    def connect(self):
        # should set self.connected
        raise Exception("Override this")
    
    def disconnect(self):
        # should set self.connected
        raise Exception("Override this")
    
    def capture_frame(self):
        # should return a numpy array
        raise Exception("Override this")
    # ==========================
    
    
    def capture(self, undistort=True, filename=None):
        if not self.connected:
            self.connect()
        
        frame = self.capture_frame()
        
        image = conversions.NumPy2Ipl(frame)#.astype('uint8'))
        #image = NumPy2Ipl(frame.astype('uint16'))
        
        #print self.logDir, filename
        if self.logDir != None and filename != None:
            # save image
            cv.SaveImage("%s/%s" % (self.logDir, filename), image)
        
        # TODO find a better way to do this
        if self.imageSize == (-1, -1):
            self.imageSize = (image.width, image.height)
        
        if self.calibrated and undistort:
            # undistort image
            undistortedImage = cv.CreateImage((image.width, image.height),
                                            image.depth, image.nChannels)
            #result = cv.CreateImage(input.shape[::-1], depth, channels)
            cv.Undistort2(image, undistortedImage, self.camMatrix, self.distCoeffs)
            return undistortedImage
            
        return image
    
    def capture_grid_image(self, gridSize):
        #if not self.calibrated:
        #    raise IOError('Camera must be calibrated before capturing grid')
        
        image = self.capture()
        success, corners = cv.FindChessboardCorners(image, gridSize)
        
        if not success:
            return image, corners, False
        
        corners = cv.FindCornerSubPix(image, corners, (5,5), (-1, -1),
                    (cv.CV_TERMCRIT_EPS + cv.CV_TERMCRIT_ITER, 30, 0.1))
        
        gridN = gridSize[0] * gridSize[1]
        if len(corners) != gridN:
            return image, corners, False
        
        # check order of corners
        # # check that grid is not rotated
        # dyh = abs(corners[1][1] - corners[0][1])
        # dyv = abs(corners[gridSize[0]][1] - corners[0][1])
        # if dyh > dyv:
        #     # grid is rotated (columns and rows are swapped)
        #     newCorners = []
        #     for i in xrange(len(corners)):
        #         divmod(i,gridSize[0])
        #          * gridSize
        #         newCorners.append()
        # xs should be ascending
        if corners[0][0] > corners[1][0]:
            #print "flipping rows"
            for r in xrange(gridSize[1]):
                for c in xrange(gridSize[0]/2):
                    i = c + r * gridSize[0]
                    i2 = (gridSize[0] - c - 1) + r * gridSize[0]
                    o = corners[i]
                    corners[i] = corners[i2]
                    corners[i2] = o
        
        # ys should be descending
        if corners[0][1] < corners[gridSize[0]][1]:
            #print "flipping columns"
            for c in xrange(gridSize[0]):
                for r in xrange(gridSize[1]/2):
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
        return self.calibrate_internals(gridSize, gridBlockSize)
    
    def calibrate_internals(self, gridSize, gridBlockSize):
        # initialize camera matrices
        self.camMatrix = cv.CreateMat(3, 3, cv.CV_64FC1)
        cv.SetZero(self.camMatrix)
        self.camMatrix[0,0] = 1.
        self.camMatrix[1,1] = 1.
        self.distCoeffs = cv.CreateMat(5, 1, cv.CV_64FC1)
        cv.SetZero(self.distCoeffs)
        
        nGrids = len(self.calibrationImages)
        #if nGrids != 7:
        #    raise ValueError('Calibration should only be performed with 7 images')
        gridN = gridSize[0] * gridSize[1]
        
        imPts = cv.CreateMat(nGrids*gridN, 2, cv.CV_64FC1)
        objPts = cv.CreateMat(nGrids*gridN, 3, cv.CV_64FC1)
        ptCounts = cv.CreateMat(nGrids, 1, cv.CV_32SC1)
        
        # organize self.calibrationImgPts (to imPts) and construct objPts and ptCounts
        for (i,c) in enumerate(self.calibrationImgPts):
            for j in xrange(gridN):
                imPts[j+i*gridN, 0] = c[j][0]
                imPts[j+i*gridN, 1] = c[j][1]
                # TODO should thes be actual points? how do I know what they are?
                objPts[j+i*gridN, 0] = j % gridSize[0] * gridBlockSize
                objPts[j+i*gridN, 1] = j / gridSize[0] * gridBlockSize
                objPts[j+i*gridN, 2] = 0.
            ptCounts[i,0] = len(c)
        
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
            raise Exception, "Attempted to measure calibration error of uncalibrated camera"
        gridN = gridSize[0] * gridSize[1]
        errs = []
        for (i,im) in enumerate(self.calibrationImages):
            # im = image with chessboard
            corners = self.calibrationImgPts[i]
            imPts = cv.CreateMat(gridN, 2, cv.CV_64FC1)
            objPts = cv.CreateMat(gridN, 3, cv.CV_64FC1)
            for j in xrange(gridN):
                imPts[j,0] = corners[j][0]
                imPts[j,1] = corners[j][1]
                objPts[j,0] = j % gridSize[0] * gridBlockSize
                objPts[j,1] = j / gridSize[0] * gridBlockSize
                objPts[j,2] = 0.
            
            # measure rVec and tVec for this image
            rVec = cv.CreateMat(3, 1, cv.CV_64FC1)
            tVec = cv.CreateMat(3, 1, cv.CV_64FC1)
            cv.FindExtrinsicCameraParams2(objPts, imPts, self.camMatrix,
                self.distCoeffs, rVec, tVec)
            
            # reproject points
            pimPts = cv.CreateMat(gridN, 2, cv.CV_64FC1)
            cv.ProjectPoints2(objPts, rVec, tVec, self.camMatrix, self.distCoeffs, pimPts)
            
            # measure error
            err = []
            for j in xrange(gridN):
                err.append([imPts[j,0] - pimPts[j,0], imPts[j,1] - pimPts[j,1]])
            
            errs.append(err)
        
        return errs
    
    def save_calibration(self, directory):
        if not self.calibrated:
            raise Exception, "Attempted to save calibration of uncalibrated camera"
        
        directory = "%s/%i" % (directory, self.camID)
        
        if not os.path.exists(directory):
            os.makedirs(directory)
        if not os.path.exists("%s/images" % directory):
            os.makedirs("%s/images" % directory)
        
        cv.Save("%s/camMatrix.xml" % directory, self.camMatrix)
        cv.Save("%s/distCoeffs.xml" % directory, self.distCoeffs)
        for (i,im) in enumerate(self.calibrationImages):
            cv.SaveImage("%s/images/%i.png" % (directory, i), im)
        
        if self.located:
            cv.Save("%s/rVec.xml" % directory, self.rVec)
            cv.Save("%s/tVec.xml" % directory, self.tVec)
            cv.Save("%s/itoWMatrix.xml" % directory, conversions.NumPytoCV(self.itoWMatrix))
    
    def load_calibration(self, directory):
        directory = "%s/%i" % (directory, self.camID)
        
        self.camMatrix = cv.Load("%s/camMatrix.xml" % directory)
        self.distCoeffs = cv.Load("%s/distCoeffs.xml" % directory)
        self.calibrated = True
        
        if os.path.exists("%s/itoWMatrix.xml" % directory):
            self.rVec = cv.Load("%s/rVec.xml" % directory)
            self.tVec = cv.Load("%s/tVec.xml" % directory)
            self.itoWMatrix = conversions.CVtoNumPy(cv.Load("%s/itoWMatrix.xml" % directory))
            self.located = True
    
    # ============================================
    #           Localization
    # ============================================
    
    def capture_localization_image(self, gridSize):
        image, corners, success = self.capture_grid_image(gridSize)
        if not success:
            return image, False
        
        self.localizationImage = image
        self.localizationCorners = corners
        return image, True
    
    def locate(self, gridSize, gridBlockSize):
        if self.localizationImage == None or self.localizationCorners == None:
            raise ValueError('You must successfully call capture_localization_image before locate')
        self.rVec = cv.CreateMat(3, 1, cv.CV_64FC1)
        self.tVec = cv.CreateMat(3, 1, cv.CV_64FC1)
        gridN = gridSize[0] * gridSize[1]
        imPts = cv.CreateMat(gridN, 2, cv.CV_64FC1)
        objPts = cv.CreateMat(gridN, 3, cv.CV_64FC1)
        
        for j in xrange(gridN):
            imPts[j,0] = self.localizationCorners[j][0]
            imPts[j,1] = self.localizationCorners[j][1]
            objPts[j,0] = j % gridSize[0] * gridBlockSize
            objPts[j,1] = j / gridSize[0] * gridBlockSize
            objPts[j,2] = 0.
        
        cv.FindExtrinsicCameraParams2(objPts, imPts, self.camMatrix,
            self.distCoeffs, self.rVec, self.tVec)
        
        # convert rVec to rMatrix
        rMatrix = cv.CreateMat(3, 3, cv.CV_64FC1)
        cv.Rodrigues2(self.rVec, rMatrix)
        # calculate image-to-world transformation matrix
        self.itoWMatrix = calculate_image_to_world_matrix(self.tVec, rMatrix, self.camMatrix)
        self.located = True
    
    def get_position(self):
        #if not self.calibrated:
        #    raise Exception, "Camera must be calibrated before calling get_position"
        if self.located:
            # flipping y and z to make this left-handed
            return self.itoWMatrix[3,0], -self.itoWMatrix[3,1], -self.itoWMatrix[3,2]
        else:
            raise Exception
            return 0, 0, 0
    
    def get_3d_position(self, x, y):
        if self.located:
            #tp = numpy.matrix([ x - self.camMatrix[0,2], y - self.camMatrix[1,2], 1., 1. ])
            tp = numpy.array([x - self.camMatrix[0,2], y - self.camMatrix[1,2], 1., 1.])
            tr = numpy.array(tp * self.itoWMatrix)[0]
            # trm = numpy.zeros(4,dtype=numpy.float64)
            # for i in xrange(4):
            #     for j in xrange(4):
            #         trm[i] += tp[j] * self.itoWMatrix[j,i]
            # if sum(numpy.abs(tr - trm)) > 1e-9:
            #     print tr, trm
            #     tr = trm
            # flipping y and z to make this left-handed
            return tr[0]/tr[3], -tr[1]/tr[3], -tr[2]/tr[3]
        else:
            raise Exception, "camera was not localized prior to call to get_3d_position"
            return 0, 0, 0

def calculate_image_to_world_matrix(tVec, rMatrix, camMatrix):
    #print "t"
    t = numpy.matrix([[1., 0., 0., 0.],
                    [0., 1., 0., 0.],
                    [0., 0., 1., 0.],
                    [tVec[0,0], tVec[1,0], tVec[2,0], 1.]])
    #print "r"
    r = numpy.matrix([[rMatrix[0,0], rMatrix[0,1], rMatrix[0,2], 0.],
                [rMatrix[1,0], rMatrix[1,1], rMatrix[1,2], 0.],
                [rMatrix[2,0], rMatrix[2,1], rMatrix[2,2], 0.],
                [0., 0., 0., 1.] ])
    # r = numpy.matrix(([rMatrix[0,0], rMatrix[1,0], rMatrix[2,0], 0.],
    #                 [rMatrix[0,1], rMatrix[1,1], rMatrix[2,1], 0.],
    #                 [rMatrix[0,2], rMatrix[1,2], rMatrix[2,2], 0.],
    #                 [0., 0., 0., 1.]))
    info = t * r

    # info = numpy.matrix([[rMatrix[0,0], rMatrix[0,1], rMatrix[0,2], tVec[0,0]],
    #                     [rMatrix[1,0], rMatrix[1,1], rMatrix[1,2], tVec[1,0]],
    #                     [rMatrix[2,0], rMatrix[2,1], rMatrix[2,2], tVec[2,0]],
    #                     [0., 0., 0., 1.] ])
    #return info

    s = numpy.matrix([ [1., 0., 0., 0.],
                [0., 1., 0., 0.],
                [0., 0., 1., 0.],
                [0., 0., 0., 1.] ])
    s[0,0] = -1.
    s[1,1] = -1.
    s[2,2] = -1.

    #return info

    t = info * s
    #return info
    s[0,0] = 1. / camMatrix[0,0]
    s[1,1] = 1. / camMatrix[1,1]
    s[2,2] = 1.

    info = s * t

    return info

# =========================================================================================
# =========================================================================================
# ================================== Testing ==============================================
# =========================================================================================
# =========================================================================================


if __name__ == '__main__':
    pass