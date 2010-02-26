#!/usr/bin/env python

# functions to be use:
#   StereoCalibrate
#   StereoRectify (post-StereoCalibrate)
#   StereoRectifyUncalibrated (if no StereoCalibrate,
#       should still use CalibrateCamera2 on each camera and Undistort2/UndistortPoints

import sys
import time
import os

import numpy
import cv
import dc1394simple

def poll_user(question, choice1, choice2, default=0):
    if default:
        print "%s %s/[%s]" % (question, choice1, choice2)
    else:
        print "%s [%s]/%s" % (question, choice1, choice2)
    response = raw_input()
    if response == '':
        return default
    elif response == choice1:
        return 0
    elif response == choice2:
        return 1
    else:
        raise IOError, "User provided unknown response: %s" % response

def NumPy2Ipl(input):
    if not isinstance(input, numpy.ndarray):
        raise TypeError, 'Must be called with numpy.ndarray!'
    
    ndim = input.ndim
    if not ndim in (2,3):
        raise ValueError, 'Only 2D or 3D arrays are supported!'
    
    if ndim == 2:
        channels = 1
    else:
        channels = input.shape[2]
    
    if input.dtype == numpy.uint8:
        depth = cv.IPL_DEPTH_8U
    elif input.dtype == numpy.float32:
        depth = cv.IPL_DEPTH_32F
    elif input.dtype == numpy.float64:
        depth = cv.IPL_DEPTH_64F
    
    # array.shape = (height, width)
    result = cv.CreateImage(input.shape[::-1], depth, channels)
    cv.SetData(result, input.tostring(), input.shape[1])
    #result.imageData = input.tostring()
    
    return result

class CameraPair:
    def __init__(self):
        self.calibrated = False
        self.connected = False
    
    def connect(self, indexes=[0,1]):
        if self.connected:
            return
        
        if len(indexes) != 2:
            raise ValueError, "Indexes must be of length 2 (length:%i)" % len(indexes)
        
        cams = dc1394simple.enumerate_cameras()
        
        if max(indexes) >= len(cams):
            raise ValueError, "Invalid indexes passed to CameraPair:%i,%i" % indexes
        if len(cams) < 2:
            raise IOError, "Less than 2 cameras found"
        
        self.cam1 = dc1394simple.SimpleCamera(cams[indexes[0]])
        self.cam2 = dc1394simple.SimpleCamera(cams[indexes[1]])
        
        self.connected = True
    
    def capture(self):
        if not self.connected:
            self.connect()
        frame1 = self.cam1.capture_frame()
        frame2 = self.cam2.capture_frame()
        image1 = NumPy2Ipl(frame1.astype('uint8'))
        image2 = NumPy2Ipl(frame2.astype('uint8'))
        return image1, image2
    
    def calibrate(self, nGrids=8, captureDelay=-1, gridSize=(5,5)):
        """
        captureDelay [-1] : seconds to wait between image capture attempts
                if -1 : manually trigger capture via command line
        """
        if not self.connected:
            self.connect()
        lastFrameTime = time.time()
        imageSize = (0, 0) # width, height
        gridN = gridSize[0] * gridSize[1]
        
        # allocate space
        imPts1 = cv.CreateMat(nGrids*gridN, 2, cv.CV_64FC1)
        imPts2 = cv.CreateMat(nGrids*gridN, 2, cv.CV_64FC1)
        objPts = cv.CreateMat(nGrids*gridN, 3, cv.CV_64FC1)
        ptCounts = cv.CreateMat(nGrids, 1, cv.CV_32SC1)
        
        # find nGrids images with grid present
        successes = 0
        while successes < nGrids:
            # perform next capture?
            if captureDelay == -1:
                if poll_user("Capture next frame", "y", "n", 0):
                    continue
            else:
                time.sleep(captureDelay)
            
            im1, im2 = self.capture()
            
            s1, c1 = cv.FindChessboardCorners(im1, gridSize)
            s2, c2 = cv.FindChessboardCorners(im2, gridSize)
            
            # did we find two grids?
            if not all((s1,s2)):
                print "Couldn't find grids:%i,%i" % (s1, s2)
                continue
            
            # find subpixel positions
            imageSize = (im1.width, im1.height)
            c1 = cv.FindCornerSubPix(im1, c1, (5,5), (-1,-1),
                (cv.CV_TERMCRIT_EPS+cv.CV_TERMCRIT_ITER, 30, 0.1))
            c2 = cv.FindCornerSubPix(im2, c2, (5,5), (-1,-1),
                (cv.CV_TERMCRIT_EPS+cv.CV_TERMCRIT_ITER, 30, 0.1))
            
            # did we find the right number of internal corners
            if len(c1) != gridN or len(c2) != gridN:
                print "Couldn't find right number of grid corners:%i,%i!=%i" % (len(c1), len(c2), gridN)
                continue
            
            print "Found good grids:%i" % successes
            # store data for future analysis
            # TODO add ability to save data/images to file
            step = successes*gridN
            for i in xrange(gridN):
                imPts1[i+step, 0] = c1[i][0]
                imPts1[i+step, 1] = c1[i][1]
                imPts2[i+step, 0] = c2[i][0]
                imPts2[i+step, 1] = c2[i][1]
                objPts[i+step, 0] = i/float(gridN)
                objPts[i+step, 1] = i % gridN
                objPts[i+step, 2] = 0.
            ptCounts[successes, 0] = gridN
            
            successes += 1
        
        self.cam1Matrix = cv.CreateMat(3, 3, cv.CV_64FC1)
        cv.SetZero(self.cam1Matrix)
        self.cam1Matrix[0,0] = 1.0
        self.cam1Matrix[1,1] = 1.0
        self.cam1DistCoeffs = cv.CreateMat(5, 1, cv.CV_64FC1)
        cv.SetZero(self.cam1DistCoeffs)
        
        self.cam2Matrix = cv.CreateMat(3, 3, cv.CV_64FC1)
        cv.SetZero(self.cam2Matrix)
        self.cam2Matrix[0,0] = 1.0
        self.cam2Matrix[1,1] = 1.0
        self.cam2DistCoeffs = cv.CreateMat(5, 1, cv.CV_64FC1)
        cv.SetZero(self.cam2DistCoeffs)
        
        self.R = cv.CreateMat(3, 3, cv.CV_64FC1)
        cv.SetZero(self.R)
        
        self.T = cv.CreateMat(3, 1, cv.CV_64FC1)
        cv.SetZero(self.T)
        
        # print objPts
        # print imPts1
        # print imPts2
        # print ptCounts
        # print self.cam1Matrix
        # print self.cam1DistCoeffs
        # print self.cam2Matrix
        # print self.cam2DistCoeffs
        # print imageSize
        # print self.R
        # print self.T
        # 
        # cv.Save("sMs/objPts.xml", objPts)
        # cv.Save("sMs/imPts1.xml", imPts1)
        # cv.Save("sMs/imPts2.xml", imPts2)
        # cv.Save("sMs/ptCounts.xml", ptCounts)
        
        cv.CalibrateCamera2(objPts, imPts1, ptCounts, imageSize,
                self.cam1Matrix, self.cam1DistCoeffs,
                cv.CreateMat(nGrids, 3, cv.CV_64FC1), cv.CreateMat(nGrids, 3, cv.CV_64FC1), 0)
        
        cv.CalibrateCamera2(objPts, imPts2, ptCounts, imageSize,
                self.cam2Matrix, self.cam2DistCoeffs,
                cv.CreateMat(nGrids, 3, cv.CV_64FC1), cv.CreateMat(nGrids, 3, cv.CV_64FC1), 0)
        
        cv.StereoCalibrate(objPts, imPts1, imPts2, ptCounts,
                self.cam1Matrix, self.cam1DistCoeffs, self.cam2Matrix, self.cam2DistCoeffs,
                imageSize, self.R, self.T,
                cv.CreateMat(3, 3, cv.CV_64FC1), cv.CreateMat(3, 3, cv.CV_64FC1),
                flags=cv.CV_CALIB_FIX_INTRINSIC)
        
        self.calibrated = True
        self.compute_rectify_matrices(imageSize)
    
    def save_calibration(self, directory):
        if self.calibrated:
            cv.Save("%s/cam1Matrix.xml" % directory, self.cam1Matrix)
            cv.Save("%s/cam1DistCoeffs.xml" % directory, self.cam1DistCoeffs)
            cv.Save("%s/cam2Matrix.xml" % directory, self.cam2Matrix)
            cv.Save("%s/cam2DistCoeffs.xml" % directory, self.cam2DistCoeffs)
            cv.Save("%s/R.xml" % directory, self.R)
            cv.Save("%s/T.xml" % directory, self.T)
    
    def load_calibration(self, directory):
        self.cam1Matrix = cv.Load("%s/cam1Matrix.xml"  % directory)
        self.cam1DistCoeffs = cv.Load("%s/cam1DistCoeffs.xml" % directory)
        self.cam2Matrix = cv.Load("%s/cam2Matrix.xml" % directory)
        self.cam2DistCoeffs = cv.Load("%s/cam2DistCoeffs.xml" % directory)
        self.R = cv.Load("%s/R.xml" % directory)
        self.T = cv.Load("%s/T.xml" % directory)
        self.calibrated = True
    
    def compute_rectify_matrices(self, imageSize):
        if not self.calibrated:
            self.calibrate()
        self.rR1 = cv.CreateMat(3, 3, cv.CV_64FC1)
        self.rR2 = cv.CreateMat(3, 3, cv.CV_64FC1)
        self.rP1 = cv.CreateMat(3, 4, cv.CV_64FC1)
        self.rP2 = cv.CreateMat(3, 4, cv.CV_64FC1)
        self.rQ = cv.CreateMat(4, 4, cv.CV_64FC1)
        
        cv.StereoRectify(self.cam1Matrix, self.cam2Matrix,
                    self.cam1DistCoeffs, self.cam2DistCoeffs,
                    imageSize, self.R, self.T,
                    self.rR1, self.rR2, self.rP1, self.rP2,
                    self.rQ)
        # later, use self.rQ to rectify the points on the image using
        #   cvPerspectiveTransform(const CvArr* src, CvArr* dst, const CvMat* mat)
        # so pt1 = (x, y, d) : d = disparity
        # cvPerspectiveTransform(pt, npt, rQ)
        # should give me the 3d position of the point (x, y, z)

if __name__ == "__main__":
    cp = CameraPair()
    
    cp.connect()
    
    # test capture
    im1, im2 = cp.capture()
    
    cp.calibrate()
    
    # save calibration to directory "stereoCalibration"
    cp.save_calibration("stereoCalibration")