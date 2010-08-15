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
import pylab
import cv
#import dc1394simple
import pydc1394

dc1394 = pydc1394.DC1394Library()

# coordinates (post flip, see: '# flipped')
#
# z+ towards camera
# y+ up
# x+ right


# gridSize = (8,5)
# gridBlockSize = 2.73
# leftCamID = 49712223528793951
# rightCamID = 49712223528793946

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


def CVtoNumPy(cvMatrix):
    m = numpy.matrix(numpy.zeros([cvMatrix.height, cvMatrix.width]))
    for r in xrange(cvMatrix.height):
        for c in xrange(cvMatrix.width):
            m[r,c] = cvMatrix[r,c]
    return m


def NumPytoCV(numpyMatrix, dataType=cv.CV_64FC1):
    m = cv.CreateMat(numpyMatrix.shape[0], numpyMatrix.shape[1], dataType)
    for r in xrange(m.rows):
        for c in xrange(m.cols):
            m[r,c] = numpyMatrix[r,c]
    return m


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


def intersection(o1, p1, o2, p2):
    x = numpy.array(o2) - numpy.array(o1)
    d1 = numpy.array(p1) - numpy.array(o1)
    d2 = numpy.array(p2) - numpy.array(o2)
    
    c = numpy.array([d1[1]*d2[2] - d1[2]*d2[1],
            d1[2]*d2[0] - d1[0]*d2[2],
            d1[0]*d2[1] - d1[1]*d2[0]])
    den = c[0]**2 + c[1]**2 + c[2]**2
    
    if den < 1e-9:
        print "3d localization is invalid"
    
    def det(v1, v2, v3):
        return v1[0]*v2[1]*v3[2] + v1[2]*v2[0]*v3[1] + v1[1]*v2[2]*v3[0] - v1[2]*v2[1]*v3[0] - v1[0]*v2[2]*v3[1] - v1[1]*v2[0]*v3[2]
    
    t1 = det(x, d2, c) / den
    t2 = det(x, d1, c) / den
    
    r1 = o1 + d1 * t1
    r2 = o2 + d2 * t2
    
    return r1, r2


def midpoint(p1, p2):
    return (p1[0] + p2[0])/2., (p1[1] + p2[1])/2., (p1[2] + p2[2])/2.


class SimpleCamera(pydc1394.Camera):
    def set_mode(self):
        self.mode = self.modes[4]
    def configure(self):
        self.framerate.mode = 'manual'
        self.framerate.val = 1.
        self.exposure.mode = 'manual'
        self.exposure.val = 1.
        self.shutter.mode = 'manual'
        self.shutter.val = 1000.
    def capture_frame(self):
        # TODO test
        # i'm not 100% sure that the settings have enought time to take effect with this,
        # it might be better to pull apart the start/stop iso transmission and capture so
        # that I start transmission, configure, allow time for settings to take effect and
        # then capture
        self.start()
        self.configure()
        i = self.shot().reshape((1040,1392))
        self.stop()
        return i


class CalibratedCamera:
    def __init__(self, camID=None):
        self.connected = False
        self.calibrated = False
        self.located = False
        self.imageSize = (-1, -1)
        self.camID = camID
        
        # for calibration
        self.calibrationImages = []
        self.calibrationImgPts = []
        
        # for localization
        self.localizationImage = None
        self.localizationCorners = None
    
    
    def connect(self):
        if self.connected:
            return True
        
        if self.camID == None:
            #cams = dc1394simple.enumerate_cameras()
            cams = dc1394.enumerate_cameras()
            if len(cams) < 1:
                raise IOError, "No cameras found"
            self.camID = cams[0]['guid']
        
        try:
            #self.camera = dc1394simple.SimpleCamera(self.camID)
            self.camera = SimpleCamera(dc1394,self.camID)
        except:
            print "Failed to connect to camera %i" % self.camID
            self.connected = False
            return False
        
        # TODO check if camera connected correctly?
        
        self.connected = True
        return True
    
    
    def disconnect(self):
        if self.connected == True:
            self.connected = False
            del self.camera
    
    def capture(self, undistort=True):
        if not self.connected:
            self.connect()
        
        frame = self.camera.capture_frame()
        image = NumPy2Ipl(frame.astype('uint8'))
        
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
        
        return image, corners, True
    
    
    def capture_localization_image(self, gridSize):
        image, corners, success = self.capture_grid_image(gridSize)
        if not success:
            return image, False
        
        self.localizationImage = image
        self.localizationCorners = corners
        return image, True
        # if not self.calibrated:
        #             raise IOError('Camera must be calibrated before localization')
        #         # from the source code (cvcalibration.cpp:1167) it looks like
        #         # cvFindExtrinsicCameraParams2 performs undistortion internally
        #         image = self.capture()#undistort=False)
        #         success, corners = cv.FindChessboardCorners(image, gridSize)
        #         
        #         if not success:
        #             return image, False
        #         
        #         corners = cv.FindCornerSubPix(image, corners, (5,5), (-1, -1),
        #                     (cv.CV_TERMCRIT_EPS + cv.CV_TERMCRIT_ITER, 30, 0.1))
        #         
        #         gridN = gridSize[0] * gridSize[1]
        #         if len(corners) != gridN:
        #             return image, False
        #         
        #         self.localizationImage = image
        #         self.localizationCorners = corners
        #         
        #         return image, True
    
    
    def capture_calibration_image(self, gridSize):
        image, corners, success = self.capture_grid_image(gridSize)
        if not success:
            return image, False
        
        self.calibrationImages.append(image)
        self.calibrationImgPts.append(corners)
        return image, True
        # # capture image (converted to IplImage)
        # image = self.capture()
        # 
        # # find chessboards
        # success, corners = cv.FindChessboardCorners(image, gridSize)
        # 
        # # if no chessboard, return the image and false
        # if not success:
        #     return image, False
        # 
        # # find subpixel coordinates of inside corners
        # corners = cv.FindCornerSubPix(image, corners, (5,5), (-1,-1),
        #             (cv.CV_TERMCRIT_EPS + cv.CV_TERMCRIT_ITER, 30, 0.1))
        # 
        # # did we find the right number of corners?
        # gridN = gridSize[0] * gridSize[1]
        # if len(corners) != gridN:
        #     return image, False
        # 
        # #cv.DrawChessboardCorners(image, gridSize, corners, success)
        # 
        # self.calibrationImages.append(image)
        # self.calibrationImgPts.append(corners)
        # 
        # return image, True
    
    
    def remove_last_calibration_point(self):
        self.calibrationImages.pop()
        self.calibrationImgPts.pop()
    
    
    def calibrate_internals(self, gridSize, gridBlockSize):
        # initialize camera matrices
        self.camMatrix = cv.CreateMat(3, 3, cv.CV_64FC1)
        cv.SetZero(self.camMatrix)
        self.camMatrix[0,0] = 1.
        self.camMatrix[1,1] = 1.
        self.distCoeffs = cv.CreateMat(5, 1, cv.CV_64FC1)
        cv.SetZero(self.distCoeffs)
        
        nGrids = len(self.calibrationImgPts)
        if nGrids != 7:
            raise ValueError('Calibration should only be performed with 7 images')
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
    
    def calibrate(self, gridSize, gridBlockSize):
        self.calibrate_internals(gridSize, gridBlockSize)
    
    
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
            return 0, 0, 0
    
    
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
            cv.Save("%s/itoWMatrix.xml" % directory, NumPytoCV(self.itoWMatrix))
        
    
    
    def load_calibration(self, directory):
        directory = "%s/%i" % (directory, self.camID)
        
        self.camMatrix = cv.Load("%s/camMatrix.xml" % directory)
        self.distCoeffs = cv.Load("%s/distCoeffs.xml" % directory)
        self.calibrated = True
        
        if os.path.exists("%s/itoWMatrix.xml" % directory):
            self.rVec = cv.Load("%s/rVec.xml" % directory)
            self.tVec = cv.Load("%s/tVec.xml" % directory)
            self.itoWMatrix = CVtoNumPy(cv.Load("%s/itoWMatrix.xml" % directory))
            self.located = True
        
        
    
    
    def get_3d_position(self, x, y):
        if self.located:
            #tp = numpy.matrix([ x - self.camMatrix[0,2], y - self.camMatrix[1,2], 1., 1. ])
            tp = numpy.array([x - self.camMatrix[0,2], y - self.camMatrix[1,2], 1., 1.])
            tr = numpy.array(tp * self.itoWMatrix)[0]
            # flipping y and z to make this left-handed
            return tr[0]/tr[3], -tr[1]/tr[3], -tr[2]/tr[3]
        else:
            return 0, 0, 0


class FileCamera(CalibratedCamera):
    def __init__(self, camID=None, frameDirectory=None):
        CalibratedCamera.__init__(self, camID)
        self.frameDirectory = frameDirectory
        self.frameIndex = 0
    def connect(self):
        if self.connected:
            return True
        if self.frameDirectory == None:
            raise IOError, "FileCamera.frameDirectory must be set before calling connect"
        
        if not os.path.exists(self.frameDirectory):
            raise IOError, "FileCamera.frameDirectory(%s) does not exist" % self.frameDirectory
        
        if not os.path.isdir(self.frameDirectory):
            raise IOError, "FileCamera.frameDirectory(%s) is not a directory" % self.frameDirectory
        
        # autoassign camID
        if self.camID == None:
            files = [f for f in os.listdir(self.frameDirectory) if os.path.isdir(f)]
            files.sort()
            for f in files:
                try:
                    self.camID = int(f)
                except:
                    pass
            if self.camID == None:
                raise IOError, "Failed to find valid int named dir in frameDirectory"
        
        self.connected = True
    
    def disconnect(self):
        self.connected = False
    
    def capture(self, undistort=True):
        if not self.connected:
            self.connect()
        
        try:
            frame = pylab.imread("%s/%i/%i.png" % (self.frameDirectory, self.camID, self.frameIndex))
        except:
            try:
                self.frameIndex = 0
                frame = pylab.imread("%s/%i/0.png" % (self.frameDirectory, self.camID))
            except:
                raise IOError, "Failed to find a valid frame (%s/%i/%i.png)" % (self.frameDirectory, self.camID, self.frameIndex)
        
        self.frameIndex += 1
        image = NumPy2Ipl((frame*255).astype('uint8'))
        
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

class CameraPair:
    """A simple class that contains two CalibratedCamera objects"""
    def __init__(self, camIDs=None):
        if camIDs == None:
            #camIDs = dc1394simple.enumerate_cameras()[:2]
            cams = dc1394.enumerate_cameras()[:2]
            if len(camIDs) != 2:
                raise IOError("Could not find two cameras")
        #self.cameras = [CalibratedCamera(camIDs[0]), CalibratedCamera(camIDs[1])]
        self.cameras = [dc1394.Camera(dc1394,cams[0]['guid']), dc1394.Camera(dc1394,cams[1]['guid'])]
        
        # for logging
        self.frameNum = 0
        self.logDirectory = '/Users/labuser/Desktop/cncControllerImages/'
    
    
    def get_connected(self):
        connected = []
        for c in self.cameras:
            connected.append(c.connected)
        return connected
    
    
    def get_calibrated(self):
        calibrated = []
        for c in self.cameras:
            calibrated.append(c.calibrated)
        return calibrated
    
    
    def get_located(self):
        located = []
        for c in self.cameras:
            located.append(c.located)
        return located
    
    
    def connect(self):
        for i in xrange(len(self.cameras)):
            self.cameras[i].connect()
    
    
    def disconnect(self):
        for i in xrange(len(self.cameras)):
            self.cameras[i].disconnect()
    
    
    def capture(self):
        ims = []
        for c in self.cameras:
            ims.append(c.capture())
        for (i, im) in enumerate(ims):
            cv.SaveImage("%s/%i/%i.png" % (self.logDirectory, i, self.frameNum), im)
        self.frameNum += 1
        return ims
    
    def locate_grid(self, gridSize):
        lim, lcorners, lsuccess = self.cameras[0].capture_grid_image(gridSize)
        rim, rcorners, rsuccess = self.cameras[1].capture_grid_image(gridSize)
        if not (lsuccess and rsuccess):
            return (lim,rim), None, False
        pts = []
        for (l, r) in zip(lcorners, rcorners):
            p = self.get_3d_position((l,r))
            pts.append(p)
        return (lim,rim), pts, True
    
    def capture_calibration_images(self, gridSize):
        ims = []
        for c in self.cameras:
            if len(c.calibrationImages) < 7:
                im, s = c.capture_calibration_image(gridSize)
                ims.append((im, s))
            else:
                # already enough calibration images
                im = c.capture()
                ims.append((im, True))
        return ims
    
    
    def capture_localization_images(self, gridSize):
        ims = []
        success = True
        for c in self.cameras:
            im, s = c.capture_localization_image(gridSize)
            success = success and s
            ims.append((im, s))
        return ims, success
    
    
    def calibrate(self, gridSize, gridBlockSize):
        for c in self.cameras:
            c.calibrate(gridSize, gridBlockSize)
    
    
    def locate(self, gridSize, gridBlockSize):
        for c in self.cameras:
            c.locate(gridSize, gridBlockSize)
    
    
    def save_calibrations(self, directory):
        for i in xrange(len(self.cameras)):
            self.cameras[i].save_calibration(directory)
    
    
    def load_calibrations(self, directory):
        for i in xrange(len(self.cameras)):
            self.cameras[i].load_calibration(directory)
    
    
    def get_camera_positions(self):
        ps = []
        for c in self.cameras:
            ps.append(c.get_position())
        return ps
    
    
    def get_3d_position(self, points):
        #TODO make this accept >2 cameras
        if len(points) != len(self.cameras):
            raise ValueError, "number of points must equal the number of cameras"
        
        # point 1 corresponds to camera 1, point 2 to camera 2, etc...
        p3ds = []
        for i in xrange(len(points)):
            p3ds.append(self.cameras[i].get_3d_position(*points[i]))
        
        r1, r2 = intersection(self.cameras[0].get_position(), p3ds[0],
            self.cameras[1].get_position(), p3ds[1])
        
        return midpoint(r1, r2)

class FileCameraPair(CameraPair):
    def __init__(self, camIDs=None, frameDirectory=None):
        if camIDs == None:
            camIDs = (None, None)
        self.cameras = [FileCamera(camIDs[0],frameDirectory), FileCamera(camIDs[1],frameDirectory)]
        
        # for logging
        self.frameNum = 0
        self.logDirectory = '/Users/labuser/Desktop/cncControllerImages/'
    
    
    def set_frame_directory(self, frameDirectory):
        for i in xrange(len(self.cameras)):
            self.cameras[i].frameDirectory = frameDirectory

class FakeCameraPair(CameraPair):
    def __init__(self, camIDs=None):
        # directory containing two directories '0' and '1' that contain images '0...1.png'
        # these images will be loaded as fake frames
        self.frameDir = None
        self.frameIndex = 0
        self.connected = [False, False]
        self.calibrated = [False, False]
        self.located = [False, False]
    
    def connect(self):
        self.connected = [True, True]
    
    def disconnect(self):
        pass
    
    def get_connected(self):
        return self.connected
    
    def calibrate(self, gridSize, gridBlockSize):
        self.calibrated = [True, True]
    
    def get_calibrated(self):
        return self.calibrated
    
    def locate(self, gridSize, gridBlockSize):
        self.located = [True, True]
    
    def get_located(self):
        return self.located
    
    def set_frame_directory(self, frameDir):
        if (not os.path.isdir('%s/0' % frameDir)) or (not os.path.isdir('%s/1' % frameDir)):
            self.frameDir = None
            return
        self.frameDir = frameDir
        def isImage(f):
            return (('.jpg' in f) or ('.png' in f))
        self.cam0Frames = ['%s/0/%s' % (self.frameDir, f) for f in os.listdir('%s/0' % self.frameDir) if isImage(f)]
        self.cam0Frames.sort()
        self.cam1Frames = ['%s/1/%s' % (self.frameDir, f) for f in os.listdir('%s/1' % self.frameDir) if isImage(f)]
        self.cam1Frames.sort()
        self.frameIndex = 0
    
    def capture(self):
        if self.frameDir == None:
            im0 = cv.CreateImage((640,480),cv.IPL_DEPTH_8U,1)
            im1 = cv.CreateImage((640,480),cv.IPL_DEPTH_8U,1)
            cv.Zero(im0)
            cv.Zero(im1)
            return im0, im1
        else:
            im0 = cv.LoadImage(self.cam0Frames[self.frameIndex], 0)
            im1 = cv.LoadImage(self.cam1Frames[self.frameIndex], 0)
            self.frameIndex = (self.frameIndex + 1) % min(len(self.cam0Frames),len(self.cam1Frames))
            return im0, im1
    
    def capture_calibration_images(self, gridSize):
        return self.capture()
    
    def capture_localization_images(self, gridSize):
        raise Exception, "This no longer agrees with CameraPair"
        ims = self.capture()
        return ims, False
    
    def save_calibrations(self, directory):
        pass
    
    def load_calibrations(self, directory):
        self.calibrate(None, None)
    
    def get_camera_positions(self):
        return [[0,0,0],[0,0,0]]
    
    def get_3d_position(self, points):
        return [0,0,0]
    

def test_single_camera(camID, gridSize, gridBlockSize, calibrationDirectory='calibrations'):
    print "Create"
    cam = CalibratedCamera(camID)
    print "Connect"
    cam.connect()
    # test capture
    print "Capture"
    im = cam.capture()
    print "Calibrate"
    while len(cam.calibrationImages) < 7:
        if poll_user("Capture next image?", "y", "n", 0):
            print "Quitting calibration"
            sys.exit(1)
        else:
            im, s = cam.capture_calibration_image(gridSize)
            if not s:
                print "Grid not found"
            else:
                print "Found grid %i" % len(cam.calibrationImages)
    
    cam.calibrate(gridSize, gridBlockSize)
    
    if poll_user("Would you like to locate the camera?", "y", "n", 0) == 0:
        success = False
        while not success:
            im, success = cam.capture_localization_image(gridSize)
            if not success:
                print "Grid not found"
                if poll_user("Try Again?", "y", "n", 0) == 1:
                    print "Quitting localization"
                    sys.exit(1)
        cam.locate(gridSize, gridBlockSize)
    
    print "Save calibration"
    cam.save_calibration(calibrationDirectory)

def test_file_camera(camID, frameDirectory, gridSize, gridBlockSize, calibrationDirectory='calibrations'):
    print "Create"
    c = FileCamera(camID,frameDirectory)
    print "Connect"
    c.connect()
    print "Capture"
    im = c.capture()
    print im
    pylab.figure()
    nim = numpy.array(CVtoNumPy(im))
    print nim
    pylab.imshow(nim)
    pylab.show()

def test_stereo_localization(camIDs, gridSize, gridBlockSize, calibrationDirectory='calibrations', frameDirectory=None):
    print "Create",
    if frameDirectory != None:
        print "FileCameraPair"
        cp = FileCameraPair(camIDs, frameDirectory)
        for c in cp.cameras:
            c.frameIndex = 3
    else:
        print "CameraPair"
        cp = CameraPair(camIDs)
    print "Connect"
    cp.connect()
    print "Capture"
    im1, im2 = cp.capture()
    print "Loading calibration",
    cp.load_calibrations(calibrationDirectory)
    print cp.cameras[0].calibrated, cp.cameras[1].calibrated
    
    print "Capture localization image"
    pylab.ion()
    success = False
    while not success:
        ims, success = cp.capture_localization_images(gridSize)
        pylab.figure()
        pylab.subplot(121)
        pylab.imshow(numpy.array(CVtoNumPy(ims[0][0])))
        pylab.gray()
        pylab.subplot(122)
        pylab.imshow(numpy.array(CVtoNumPy(ims[1][0])))
        pylab.gray()
        if not success:
            print "Both cameras did not see the grid"
            if poll_user("Try Again?", "y", "n", 0) == 1:
                print "Quitting localization"
                sys.exit(1)
    
    print "Locate"
    cp.locate(gridSize, gridBlockSize)
    
    if not all([c.located for c in cp.cameras]):
        print "Something wasn't located correctly"
        sys.exit(1)
    
    keep_capturing = True
    ptColors = ['b','g','r','c','m','y','k'] # no 'w' white
    ptIndex = 0
    
    from mpl_toolkits.mplot3d import Axes3D
    
    ax = Axes3D(pylab.figure())
    pylab.ion()
    
    while keep_capturing:
        if poll_user("Capture and locate grid points?", "y", "n", 0) == 1:
            keep_capturing = False
            continue
        
        ims, corners, success = cp.locate_grid(gridSize)
        if not success:
            print "Could not find grid"
            continue
        
        for c in corners:
            ax.scatter([c[0]],[c[1]],[c[2]],c=ptColors[divmod(ptIndex,len(ptColors))[1]])
            # scale axes 1:1
            ox, oy, oz = ax.get_xlim3d().copy(), ax.get_ylim3d().copy(), ax.get_zlim3d().copy()
            rmax = max((abs(pylab.diff(ox)), abs(pylab.diff(oy)), abs(pylab.diff(oz))))
            ox = (ox - pylab.mean(ox))/abs(pylab.diff(ox)) * rmax + pylab.mean(ox)
            oy = (oy - pylab.mean(oy))/abs(pylab.diff(oy)) * rmax + pylab.mean(oy)
            oz = (oz - pylab.mean(oz))/abs(pylab.diff(oz)) * rmax + pylab.mean(oz)
            ax.set_xlim3d([ox[0],ox[1]])
            ax.set_ylim3d([oy[0],oy[1]])
            ax.set_zlim3d([oz[0],oz[1]])
            ax.set_xlabel('x')
            ax.set_ylabel('y')
            ax.set_zlabel('z')
        ptIndex += 1
        pylab.figure()
        pylab.subplot(121)
        pylab.imshow(numpy.array(CVtoNumPy(ims[0])))
        pylab.gray()
        pylab.subplot(122)
        pylab.imshow(numpy.array(CVtoNumPy(ims[1])))
        pylab.gray()

def test_camera_pair(camIDs, gridSize, gridBlockSize, calibrationDirectory='calibrations', frameDirectory=None):
    print "Create"
    if frameDirectory != None:
        print "FileCameraPair"
        cp = FileCameraPair(camIDs, frameDirectory)
    else:
        print "CameraPair"
        cp = CameraPair(camIDs)
    
    print "Connect"
    cp.connect()
    
    print "Capture"
    im1, im2 = cp.capture()
    
    print "Loading calibration",
    cp.load_calibrations(calibrationDirectory)
    print cp.cameras[0].calibrated, cp.cameras[1].calibrated
    
    print "Capture localization image"
    success = False
    while not success:
        ims, success = cp.capture_localization_images(gridSize)
        if not success:
            print "Both cameras did not see the grid"
            if poll_user("Try Again?", "y", "n", 0) == 1:
                print "Quitting localization"
                sys.exit(1)
    
    print "Locate"
    cp.locate(gridSize, gridBlockSize)
    
    #print ims[0][0].width, ims[0][0].height #1280 x 960
    
    if not all([c.located for c in cp.cameras]):
        print "Something wasn't located correctly"
        sys.exit(1)
    
    from mpl_toolkits.mplot3d import Axes3D
    
    f = pylab.figure(1)
    a = Axes3D(f)
    cpos = []
    for c in cp.cameras:
        p = c.get_position()
        cpos.append(p)
        # a.scatter([p[0]],[p[1]],[p[2]],c='b')
    lcorners = cp.cameras[0].localizationCorners
    rcorners = cp.cameras[1].localizationCorners
    pts = []
    for (l,r) in zip(lcorners,rcorners):
        p = cp.get_3d_position((l,r))
        pts.append(p)
        a.scatter([p[0]],[p[1]],[p[2]],c='r')
    
    a.set_xlim3d([-5,20])
    a.set_ylim3d([-5,20])
    a.set_zlim3d([-5,20])
    
    pylab.savetxt('%s/gridPts' % calibrationDirectory, pylab.array(pts))
    pylab.savetxt('%s/camPos' % calibrationDirectory, pylab.array(cpos))
    
    measuredDists = pylab.sqrt(pylab.sum(pylab.array(pts)**2,1))
    y, x = divmod(pylab.arange(gridSize[0]*gridSize[1]),gridSize[0])
    actualPos = pylab.transpose(pylab.vstack((x,y))) * gridBlockSize
    actualDists = pylab.sqrt(pylab.sum(actualPos**2,1))
    distErrors = abs(measuredDists - actualDists)
    
    pylab.figure(2)
    pylab.hist(distErrors)
    print "Max Abs(Error):", distErrors.max()
    
    def dist_grid(a):
        a = pylab.array(a)
        r = pylab.zeros((len(a),len(a)))
        for i in xrange(len(a)):
            r[i,:] = pylab.sqrt(pylab.sum((a-a[i])**2,1))
        return r
    
    aGrid = dist_grid(actualPos)
    mGrid = dist_grid(pts)
    eGrid = abs(mGrid-aGrid)
    pylab.figure(3)
    pylab.subplot(221)
    pylab.imshow(mGrid,interpolation='nearest',origin='lower')
    pylab.title('Measured')
    pylab.colorbar()
    pylab.subplot(222)
    pylab.imshow(aGrid,interpolation='nearest',origin='lower')
    pylab.title('Actual')
    pylab.colorbar()
    pylab.subplot(223)
    pylab.imshow(abs(mGrid-aGrid),interpolation='nearest',origin='lower')
    pylab.title('Error')
    pylab.colorbar()
    pylab.subplot(224)
    pylab.imshow(abs(aGrid/mGrid - 1.),interpolation='nearest',origin='lower')
    pylab.title('Ratio')
    pylab.colorbar()
    
    pylab.figure(4)
    pylab.subplot(121)
    i1 = pylab.array(CVtoNumPy(ims[0][0])/255.)
    pylab.imshow(i1)
    pylab.gray()
    pylab.subplot(122)
    i2 = pylab.array(CVtoNumPy(ims[1][0])/255.)
    pylab.imshow(i2)
    pylab.gray()
    pylab.show()
    
    #print "Save calibrations/localization"
    #cp.save_calibrations(calibrationDirectory)


if __name__ == "__main__":
    # gridSize = (8,5)
    # gridBlockSize = 2.822
    # gridSize = (8,5)
    # gridBlockSize = 1.27
    gridSize = (8,6)
    gridBlockSize = 1.
    
    #left = 49712223528793951
    #right = 49712223528793946
    
    if len(sys.argv) > 1:
        test = sys.argv[1].lower()
        if len(sys.argv) > 2:
            frameDir = sys.argv[2]
            print "Reading frames from %s" % frameDir
        else:
            frameDir = None
    if test[0] == 'l':
        test_single_camera(49712223528793951, gridSize, gridBlockSize) # left
    elif test[0] == 'r':
        test_single_camera(49712223528793946, gridSize, gridBlockSize) # right
    elif test[0] == 'p':
        test_camera_pair((49712223528793951, 49712223528793946), gridSize, gridBlockSize, frameDirectory=frameDir)
    elif test[0] == 's':
        test_stereo_localization((49712223528793951, 49712223528793946), gridSize, gridBlockSize, frameDirectory=frameDir)
    elif test[0] == 'f':
        if test[1] == 'l':
            test_file_camera(49712223528793951, frameDir, gridSize, gridBlockSize)
        elif test[1] == 'r':
            test_file_camera(49712223528793946, frameDir, gridSize, gridBlockSize)
        else:
            print "unknown camera"
    else:
        test_camera_pair((49712223528793951, 49712223528793946), gridSize, gridBlockSize)
    
    # cp = CameraPair()
    # 
    # cp.connect()
    # 
    # # test capture
    # im1, im2 = cp.capture()
    # 
    # calibImages = 0
    # while calibImages < 8:
    #     if poll_user("Capture next image?", "y", "n", 0):
    #         print "Quitting calibration"
    #         sys.exit(1)
    #     else:
    #         imrs, s = cp.capture_calibration_images()
    #         if not s:
    #             print "Not enough grids found"
    #             #for (i, c) in enumerate(cp.cameras):
    #             #    print "Camera %i: %i Grids found" % (i, len(c.calibrationImages))
    #         else:
    #             calibImages += 1
    #             print "Found grids %i" % calibImages
    #             #for (i, c) in enumerate(cp.cameras):
    #             #    print "Camera %i: %i Grids found" % (i, len(c.calibrationImages))
    # 
    # for (i, c) in enumerate(cp.cameras):
    #     print "Camera %i: %i Grids found" % (i, len(c.calibrationImages))
    # 
    # cp.calibrate()
    # 
    # # save calibration to directory "stereoCalibration"
    # cp.save_calibrations("stereoCalibration")
