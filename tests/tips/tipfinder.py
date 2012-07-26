#!/usr/bin/env python
"""
Given an image of an electrode on a white background...
 1. find the location of the tip of the electrode

play some tricks:
    we know...
        1. the length of the shaft (10 mm)
        2. the angle of the cnc head (n degrees)
        3. approximate distance from camera to shaft (? mm)
    use this to guess:
        candidate angles for the shaft
        candidate lengths for the shaft
   
"""

import sys

# lazy me
import numpy
from pylab import *
from scipy import ndimage
from scipy.ndimage import convolve
from scipy.stats import mode

#import pymorph

def gabor(sigma, theta=0., lam=None, psi=0.0, gamma=1.0, ksize=None, removeDC=True):
    """
    sigma = sigma of the gaussian envelope [pixels]
    theta = orientation of the normal of the parallel stripes [radians]
    lam = (lambda) = wavelength of cosine factor [pixels, default = sigma*2.]
    psi = phase offset [radians]
    gamma = spatial aspect ratio [0-1.?]
    ksize = size of kernel in pixels [pixels, default = odd(sigma*6.)]
    """
    if ksize == None:
        ksize = sigma * 6
        ksize = int(ksize + 1 - ksize % 2)
    
    if lam == None:
        lam = sigma * 2.
    
    y, x = numpy.lib.index_tricks.nd_grid()[:ksize,:ksize] - ksize/2
    xp = x * cos(theta) + y * sin(theta)
    yp = -x * sin(theta) + y * cos(theta)
    gb = exp(- (xp**2 + gamma**2 * yp**2) / (2 * sigma**2)) * cos(2. * pi * xp / lam + psi)
    if removeDC:
        return gb - average(gb)
    else:
        return gb

def measure_binary_image_bounds(binaryImage, border=100, targetBool=True):
    """measures the left, right, top, and bottom extremes
    of the elements of a binary image plus some border"""
    bys, bxs = where(binaryImage == targetBool)
    l = max(bxs.min() - border, 0)
    r = min(bxs.max() + border, binaryImage.shape[1])
    t = max(bys.min() - border, 0)
    b = min(bys.max() + border, binaryImage.shape[0])
    return l, r, t, b
    

if __name__ == '__main__':
    testDir = '6/1/'
    bg = imread('%s/0.png' % testDir)
    for i in arange(1,11):
        testImage = '%s.png' % i
    
        # load image
        im = imread('%s/%s' % (testDir, testImage))
    
        # subtract background
        dim = abs(im - bg)
    
        # find probe
        pim = dim > dim.max()/2.
        pl, pr, pt, pb = measure_binary_image_bounds(pim, 100, True) # TODO define border
    
        # crop out everything but probe
        cim = dim[pt:pb,pl:pr]
    
        # find probe shaft (non-tip)
        lapim = ndimage.gaussian_laplace(cim, 30) # TODO define sigma
        sim = abs(lapim) > abs(lapim).max()/2.
        sl, sr, st, sb = measure_binary_image_bounds(sim, 50, True)
    
        # crop out shaft (leaving tip)
        tim = cim[sb:,:]
        tl, tr, tt, tb = measure_binary_image_bounds(tim > tim.max()/2., 50, True)
        ctim = tim[tt:tb,tl:tr]
        figure()
        subplot(221)
        imshow(ctim,interpolation='nearest')
        gray()
    
        # try to find tip
        rowMaxs = ctim.max(1) # len = NCols
        colMaxs = ctim.max(0) # len = NRows
        # m1, m2 = mode(ctim)
        # m1 = m1.flatten()
        # m2 = m2.flatten()
        # mo = m1[m2.argmax()]
        # print mo
        mo = 0.05
        threshold = 0.1
        y = where(rowMaxs < threshold)[0].min()
        x = where(colMaxs > threshold)[0].max()
        print x, y
        plot(x,y,'r*')
        subplot(222)
        imshow(ctim,interpolation='nearest')
        gray()
        plot(x,y,'r*')
        xlim((x-10,x+10))
        ylim((y+10,y-10))
        subplot(223)
        plot(rowMaxs)
        plot(ones(len(rowMaxs))*mo)
        title('rowMaxs')
        subplot(224)
        plot(colMaxs)
        plot(ones(len(colMaxs))*mo)
        title('colMaxs')
    
    show()

# def old_find_tip():
#     # read stage angle from testImageStageAngle
#     stageAngles = loadtxt('testImageStageAngles')
#     
#     # read camera locations from testImageCameraLocations
#     lCamLocation, rCamLocation = loadtxt('testImageCameraLocations')
#     # 20 x 15.1 degree field of view
#     
#     imageIndex = 2
#     if len(sys.argv) > 1:
#         imageIndex = int(sys.argv[1])
#     
#     leftImage = imread('0/%i.png' % imageIndex)
#     rightImage = imread('1/%i.png' % imageIndex)
#     
#     stageAngle = stageAngles[imageIndex]
#     
#     # guess a length based on the location of the cameras
#     pixPerDeg = leftImage.shape[1] / 20.0 # image width / 20 degrees horizontal field of view
#     leftLengthGuess = arctan2(10., norm(lCamLocation)) * 2. * pixPerDeg
#     rightLengthGuess = arctan2(10., norm(rCamLocation)) * 2. * pixPerDeg
#     print "Shaft length guess (in pixels): %.3f %.3f" % (leftLengthGuess, rightLengthGuess)
#     
#     leftTipLocation = find_tip(leftImage, a0=stageAngle, l0=leftLengthGuess)
#     rightTipLocation = find_tip(rightImage, a0=stageAngle, l0=rightLengthGuess)
#     
#     # might be faster to do this together (so that I only generate the gabors once)
#     #leftTipLocation, rightTipLocation = find_tip(leftImage, rightImage, stageAngle, lCamLocation, rCamLocation)
#     
#     figure()
#     subplot(121)
#     imshow(leftImage)
#     gray()
#     scatter(leftTipLocation[0], leftTipLocation[1], c='r')
#     subplot(122)
#     imshow(rightImage)
#     gray()
#     scatter(rightTipLocation[0], rightTipLocation[1], c='r')
#     show()