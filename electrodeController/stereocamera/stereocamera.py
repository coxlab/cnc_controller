#!/usr/bin/env python

import numpy
import cv

import filecamera

global dc1394Available
dc1394Available = False
try:
    import dc1394camera
    dc1394Available = True
except:
    dc1394Available = False

class StereoCamera:
    """A simple class that contains two Camera objects"""
    def __init__(self, camIDs=[None, None], fakeCameras=False):
        global dc1394Available
        if fakeCameras or (dc1394Available == False):
            self.cameras = [filecamera.FileCamera(camIDs[0]), filecamera.FileCamera(camIDs[1])]
        else:
            self.cameras = [dc1394camera.DC1394Camera(camIDs[0]), dc1394camera.DC1394Camera(camIDs[1])]
        
        # for logging #TODO find a better way to do this
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

# =========================================================================================
# =========================================================================================
# ================================== Testing ==============================================
# =========================================================================================
# =========================================================================================

if __name__ == '__main__':
    pass