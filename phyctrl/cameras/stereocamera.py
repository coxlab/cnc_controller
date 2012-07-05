#!/usr/bin/env python

import logging

import numpy

import camera


class StereoCamera(object):
    def __init__(self, left, right):
        assert isinstance(left, camera.Camera)
        assert isinstance(right, camera.Camera)
        self.left = left
        self.right = right

    def get_3d_position(self, lx, ly, rx, ry, rays=False):
        lpt3d = self.left.get_3d_position(lx, ly)
        rpt3d = self.right.get_3d_position(rx, ry)
        lc = self.left.get_position()
        rc = self.right.get_position()
        r1, r2 = intersection(lc, lpt3d, rc, rpt3d)
        p = midpoint(r1, r2)
        p = (p[0], p[1], p[2])
        if rays:
            return p, (lc, lpt3d), (rc, rpt3d)
        return p

    def locate_grid(self, grid):
        raise NotImplementedError
        #lim, lcorners, lsuccess = self.leftCamera.capture_grid_image(gridSize)
        #rim, rcorners, rsuccess = self.rightCamera.capture_grid_image(gridSize)
        #if not (lsuccess and rsuccess):
        #    return (lim, rim), None, False
        #pts = []
        #for (l, r) in zip(lcorners, rcorners):
        #    pts.append(self.get_3d_position(l, r))
        #return (lim, rim), pts, True


def det(v1, v2, v3):
    return v1[0] * v2[1] * v3[2] + v1[2] * v2[0] * v3[1] + \
            v1[1] * v2[2] * v3[0] - v1[2] * v2[1] * v3[0] - \
            v1[0] * v2[2] * v3[1] - v1[1] * v2[0] * v3[2]


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
        logging.error("Lines are parallel, 3d localization is invalid")

    t1 = det(x, d2, c) / den
    t2 = det(x, d1, c) / den

    r1 = o1 + d1 * t1
    r2 = o2 + d2 * t2

    return r1, r2


def midpoint(p1, p2):
    return (p1[0] + p2[0]) / 2., (p1[1] + p2[1]) / 2., (p1[2] + p2[2]) / 2.
