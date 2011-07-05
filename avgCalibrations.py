#!/usr/bin/env python

import os

import cv
from pylab import *
import numpy

calDirs = ['calibrations_%i' % i for i in xrange(7)]

outDir = 'median_calibration'

camIDs = (49712223528793951, 49712223528793946)

def CVtoNumPy(cvMatrix):
    m = numpy.matrix(numpy.zeros([cvMatrix.rows, cvMatrix.cols]))
    for r in xrange(cvMatrix.rows):
        for c in xrange(cvMatrix.cols):
            m[r,c] = cvMatrix[r,c]
    return m


def NumPytoCV(numpyMatrix, dataType=cv.CV_64FC1):
    m = cv.CreateMat(numpyMatrix.shape[0], numpyMatrix.shape[1], dataType)
    for r in xrange(m.rows):
        for c in xrange(m.cols):
            m[r,c] = numpyMatrix[r,c]
    return m

def cvMedian(matrices):
    ret = cv.CreateMat(matrices[0].rows, matrices[0].cols, matrices[0].type)
    for r in xrange(matrices[0].rows):
        for c in xrange(matrices[0].cols):
            vals = []
            for m in matrices:
                vals.append(m[r,c])
            ret[r,c] = median(array(vals))
    return ret

# calculate median for camMatrix and distCoeffs
ds = []
dms = []
cs = []
cms = []
for camID in camIDs:
    distCoeffs = []
    camMatrices = []
    first = True
    cMax = cv.CreateMat(3, 3, cv.CV_64FC1)
    cMin = cv.CreateMat(3, 3, cv.CV_64FC1)
    dMax = cv.CreateMat(5, 1, cv.CV_64FC1)
    dMin = cv.CreateMat(5, 1, cv.CV_64FC1)
    for calDir in calDirs:
        inDir = "%s/%i" % (calDir, camID)
        d = cv.Load("%s/distCoeffs.xml" % inDir)
        c = cv.Load("%s/camMatrix.xml" % inDir)
        distCoeffs.append(d)
        camMatrices.append(c)
        if first:
            cv.Copy(c, cMax)
            cv.Copy(c, cMin)
            cv.Copy(d, dMax)
            cv.Copy(d, dMin)
            first = False
        else:
            cv.Max(c, cMax, cMax)
            cv.Min(c, cMin, cMin)
            cv.Max(d, dMax, dMax)
            cv.Min(d, dMin, dMin)
    ds.append(distCoeffs)
    cs.append(camMatrices)
    cm = cvMedian(camMatrices)
    dm = cvMedian(distCoeffs)
    dms.append(CVtoNumPy(dm))
    cms.append(CVtoNumPy(cm))
    
    if not os.path.exists("%s/%i" % (outDir, camID)):
        os.makedirs("%s/%i" % (outDir, camID))
    cv.Save("%s/%i/camMatrix.xml" % (outDir, camID), cm)
    cv.Save("%s/%i/distCoeffs.xml" % (outDir, camID), dm)
    