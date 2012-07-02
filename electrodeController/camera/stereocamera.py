#!/usr/bin/env python

import numpy
#import cv

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
    #def __init__(self, camIDs=[None, None], fakeCameras=False):
    def __init__(self, leftCamID=None, rightCamID=None, cameraClass=None):
        global dc1394Available
        if cameraClass == None:
            if dc1394Available:
                self.leftCamera = dc1394camera.DC1394Camera(leftCamID)
                self.rightCamera = dc1394camera.DC1394Camera(rightCamID)
                #self.cameras = [dc1394camera.DC1394Camera(camIDs[0]), \
                #        dc1394camera.DC1394Camera(camIDs[1])]
            else:
                self.leftCamera = filecamera.FileCamera(leftCamID)
                self.rightCamera = filecamera.FileCamera(rightCamID)
                #self.cameras = [filecamera.FileCamera(camIDs[0]), \
                #        filecamera.FileCamera(camIDs[1])]
        else:
            self.leftCamera = cameraClass(leftCamID)
            self.rightCamera = cameraClass(rightCamID)
            #self.cameras = [cameraClass(camIDs[0]), cameraClass(camIDs[1])]

        # if fakeCameras or (dc1394Available == False):
        #     self.cameras = [filecamera.FileCamera(camIDs[0]), \
        #        filecamera.FileCamera(camIDs[1])]
        # else:
        #     self.cameras = [dc1394camera.DC1394Camera(camIDs[0]), \
        #        dc1394camera.DC1394Camera(camIDs[1])]

        # for logging #TODO find a better way to do this
        self.frameNum = 0
        self.logDirectory = '/Users/labuser/Desktop/cncControllerImages/'

    def get_connected(self):
        return [self.leftCamera.connected, self.rightCamera.connected]
        # connected = []
        # for c in self.cameras:
        #     connected.append(c.connected)
        # return connected

    def get_calibrated(self):
        return [self.leftCamera.calibrated, self.rightCamera.calibrated]
        # calibrated = []
        # for c in self.cameras:
        #     calibrated.append(c.calibrated)
        # return calibrated

    def get_located(self):
        return [self.leftCamera.located, self.rightCamera.located]
        # located = []
        # for c in self.cameras:
        #     located.append(c.located)
        # return located

    def connect(self):
        for i in xrange(len(self.cameras)):
            self.cameras[i].connect()

    def disconnect(self):
        self.leftCamera.disconnect()
        self.rightCamera.disconnect()
        # for i in xrange(len(self.cameras)):
        #     self.cameras[i].disconnect()

    def capture(self, filename=None):
        return self.leftCamera.capture(filename=filename), \
                self.rightCamera.capture(filename=filename)
        # ims = []
        # for c in self.cameras:
        #     ims.append(c.capture(filename=filename))
        # for (i, im) in enumerate(ims):
        #     cv.SaveImage("%s/%i/%i.png" % \
        #        (self.logDirectory, i, self.frameNum), im)
        # self.frameNum += 1
        # return ims

    def locate_grid(self, gridSize):
        lim, lcorners, lsuccess = self.leftCamera.capture_grid_image(gridSize)
        rim, rcorners, rsuccess = self.rightCamera.capture_grid_image(gridSize)
        if not (lsuccess and rsuccess):
            return (lim, rim), None, False
        pts = []
        for (l, r) in zip(lcorners, rcorners):
            pts.append(self.get_3d_position(l, r))
        return (lim, rim), pts, True

    def capture_calibration_images(self, gridSize):
        return self.leftCamera.capture_calibration_image(gridSize), \
                self.rightCamera.capture_calibration_image(gridSize)
        # ims = []
        # for c in self.cameras:
        #     #if len(c.calibrationImages) < 7:
        #     if True: # get lots of calibration images
        #         im, s = c.capture_calibration_image(gridSize)
        #         ims.append((im, s))
        #     else:
        #         # already enough calibration images
        #         im = c.capture()
        #         ims.append((im, True))
        # return ims

    def capture_localization_images(self, gridSize):
        return self.leftCamera.capture_localization_image(gridSize), \
                self.rightCamera.capture_localization_image(gridSize)
        # ims = []
        # success = True
        # for c in self.cameras:
        #     im, s = c.capture_localization_image(gridSize)
        #     success = success and s
        #     ims.append((im, s))
        # return ims, success

    def calibrate(self, gridSize, gridBlockSize):
        return self.leftCamera.calibrate(gridSize, gridBlockSize), \
                self.rightCamera.calibrate(gridSize, gridBlockSize)
        # errs = []
        # for c in self.cameras:
        #     errs.append(c.calibrate(gridSize, gridBlockSize))
        # return errs

    def locate(self, gridSize, gridBlockSize):
        return self.leftCamera.locate(gridSize, gridBlockSize), \
                self.rightCamera.locate(gridSize, gridBlockSize)
        # if gridSize[0] == gridSize[1]:
        #     raise ValueError, "The grid must not be square"
        # for c in self.cameras:
        #     c.locate(gridSize, gridBlockSize)

    def save_calibrations(self, directory):
        self.leftCamera.save_calibration(directory)
        self.rightCamera.save_calibration(directory)
        # for i in xrange(len(self.cameras)):
        #     self.cameras[i].save_calibration(directory)

    def load_calibrations(self, directory):
        self.leftCamera.load_calibration(directory)
        self.rightCamera.load_calibration(directory)
        # for i in xrange(len(self.cameras)):
        #     self.cameras[i].load_calibration(directory)

    def get_camera_positions(self):
        return self.leftCamera.get_position(), self.rightCamera.get_position()
        # ps = []
        # for c in self.cameras:
        #     ps.append(c.get_position())
        # return ps

    def get_3d_position(self, lpt, rpt, andRays=False):
        # if len(points) != len(self.cameras):
        #     raise ValueError("number of points must equal the "
        #     "number of cameras")

        # # point 1 corresponds to camera 1, point 2 to camera 2, etc...
        # p3ds = []
        # for i in xrange(len(points)):
        #     p3ds.append(self.cameras[i].get_3d_position(*points[i]))
        lpt3d = self.leftCamera.get_3d_position(*lpt)
        rpt3d = self.rightCamera.get_3d_position(*rpt)
        lc = self.leftCamera.get_position()
        rc = self.rightCamera.get_position()
        r1, r2 = intersection(lc, lpt3d, rc, rpt3d)
        p = midpoint(r1, r2)
        # flip z-axis
        p = (p[0], p[1], p[2])
        if andRays:
            return p, lpt3d, rpt3d
        else:
            return p


def intersection(o1, p1, o2, p2):
    # # http://softsurfer.com/Archive/algorithm_0106/algorithm_0106.htm
    # p0 = numpy.array(o1)
    # q0 = numpy.array(o2)
    # u = numpy.array(p1) - numpy.array(p0)
    # v = numpy.array(p2) - numpy.array(q0)
    # # lines are:
    # #  p0 + s*u
    # #  q0 + t*v
    # w0 = p0 - q0
    #
    # # check if lines are parallel
    # a = numpy.dot(u,u)
    # b = numpy.dot(u,v)
    # c = numpy.dot(v,v)
    # d = numpy.dot(u,w0)
    # e = numpy.dot(v,w0)
    # denom = a * c - b**2
    # if denom < 1e-9:
    #     # lines are parallel!
    #     print "Lines are parallel, 3d localization is invalid"
    #
    # sc = (b*e - c*d)/denom
    # tc = (a*e - b*d)/denom
    #
    # # calculate vector bridging closest point
    # #wc = p(sc) - q(tc)
    # r1 = p0 + sc*u
    # r2 = q0 + tc*v
    # wc = r1 - r2
    # #print "Vectors get this close:", numpy.linalg.norm(wc)
    # #print "0 0 0 0 %+.2f %+.2f %+.2f %+.2f %+.2f %+.2f" % \
    #        (r1[0], r1[1], r1[2], r2[0], r2[1], r2[2])
    # return r1, r2

    x = numpy.array(o2) - numpy.array(o1)
    d1 = numpy.array(p1) - numpy.array(o1)
    d2 = numpy.array(p2) - numpy.array(o2)

    c = numpy.array([d1[1] * d2[2] - d1[2] * d2[1],
            d1[2] * d2[0] - d1[0] * d2[2],
            d1[0] * d2[1] - d1[1] * d2[0]])
    den = c[0] ** 2 + c[1] ** 2 + c[2] ** 2

    if den < 1e-9:
        print "3d localization is invalid"

    def det(v1, v2, v3):
        return v1[0] * v2[1] * v3[2] + v1[2] * v2[0] * v3[1] + \
                v1[1] * v2[2] * v3[0] - v1[2] * v2[1] * v3[0] - \
                v1[0] * v2[2] * v3[1] - v1[1] * v2[0] * v3[2]

    t1 = det(x, d2, c) / den
    t2 = det(x, d1, c) / den

    r1 = o1 + d1 * t1
    r2 = o2 + d2 * t2

    return r1, r2


def midpoint(p1, p2):
    return (p1[0] + p2[0]) / 2., (p1[1] + p2[1]) / 2., (p1[2] + p2[2]) / 2.

# ===========================================================
# ===========================================================
# ======================== Testing ==========================
# ===========================================================
# ===========================================================

if __name__ == '__main__':
    pass
