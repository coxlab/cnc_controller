#!/usr/bin/env python

import numpy


def project_point_onto_line(p, o, m):
    """
    Project a point onto a line defined by:
    <xy...> = o + t * m

    Returns: (pp, t)
        pp = the resulting projected point located on the line
        t = the location of the projected point on the line
        (relative to the origin)
    """
    t = numpy.dot(m, p - o) / numpy.dot(m, m)
    pp = o + t * m
    return pp, t


def reassign_origin(o, m, p, t):
    """
    Reassign the origin of a line defined by:
    <xy...> = o + t * m
    by providing:
        -a point (p, that will be projected onto the line)
        -the desired t (location on the line of the projected point)

    Returns: (newO, m)
        newO = new origin
        m = slope (unchanged)
    """
    pp, ppt = project_point_onto_line(p, o, m)
    dt = ppt - t
    newO = o + dt * m
    return newO, m


def fit_3d_line(pts, ts):
    #print "in fit_3d_line"
    #TODO add some sort of ransac type cleaning of the data
    pts = numpy.array(pts)
    ptsCentroid = pts.mean(0)
    uu, dd, vv = numpy.linalg.svd(pts - ptsCentroid)
    m = vv[0]
    #print m
    m = m / numpy.linalg.norm(m)
    #print m
    o = ptsCentroid

    # make sure that the direction was not flipped
    # method to fix flipping the direction of the line
    # (especially when m is parallel to an axis)
    if ts[1] > ts[0]:
        coarseM = pts[1] - pts[0]
    elif ts[0] > ts[1]:
        coarseM = pts[0] - pts[1]
    else:
        raise ValueError("ts[0] == ts[1], they should be different")
    coarseM = coarseM / numpy.linalg.norm(coarseM)
    # both vectors were previously normalized
    angle = numpy.arccos(numpy.dot(coarseM, m))
    if angle > (numpy.pi / 2.):
        m *= -1.

    # reassign the origin so that the given 'ts'
    # (locations on the line) are correct
    newOs = []
    for i in xrange(len(ts)):
        newOs.append(reassign_origin(o, m, pts[i], ts[i])[0])

    # find the median of the possible new origins
    newOs = numpy.array(newOs)
    #print newOs
    mO = numpy.median(newOs, 0)

    #print "leaving fit_3d_line"
    return numpy.hstack((mO[:3], m[:3]))
