#!/usr/bin/env python

import numpy
import cv

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
    elif input.dtype == numpy.uint16:
        depth = cv.IPL_DEPTH_16U
    elif input.dtype == numpy.float32:
        depth = cv.IPL_DEPTH_32F
    elif input.dtype == numpy.float64:
        depth = cv.IPL_DEPTH_64F
    
    # array.shape = (height, width)
    result = cv.CreateImage(input.shape[::-1], depth, channels)
    if input.dtype == numpy.uint16:
        cv.SetData(result, input.tostring(), input.shape[1]*2)
    else:
        cv.SetData(result, input.tostring(), input.shape[1])
    #result.imageData = input.tostring()
    
    return result


def CVtoNumPy(im):
    if im.depth == cv.IPL_DEPTH_8U:
        d = numpy.uint8
    elif im.depth == cv.IPL_DEPTH_16U:
        d = numpy.uint16
    elif im.depth == cv.IPL_DEPTH_32F:
        d = numpy.float32
    elif im.depth == cv.IPL_DEPTH_64F:
        d = numpy.float64
    else:
        raise Exception, "unknown depth" + str(cv.depth)
    #a = numpy.zeros((cv.height,cv.width),dtype=d)
    a = numpy.fromstring(im.tostring(),dtype=d).reshape((im.height,im.width))
    if (a.shape[0] != im.height) or (a.shape[1] != im.width):
        raise Exception, "shapes don't match, something went wrong numpy:"+str(a.shape)+" cv:"+str(im.height)+"x"+str(im.width)
    return a

#def CVtoNumPy(cvMatrix):
#    m = numpy.matrix(numpy.zeros([cvMatrix.height, cvMatrix.width]))
#    for r in xrange(cvMatrix.height):
#        for c in xrange(cvMatrix.width):
#            m[r,c] = cvMatrix[r,c]
#    return m


def NumPytoCV(numpyMatrix, dataType=cv.CV_64FC1):
    m = cv.CreateMat(numpyMatrix.shape[0], numpyMatrix.shape[1], dataType)
    for r in xrange(m.rows):
        for c in xrange(m.cols):
            m[r,c] = numpyMatrix[r,c]
    return m
