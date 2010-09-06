#!/usr/bin/env python

import os, sys, time

import pylab

sys.path.append('../..')

from electrodeController import stereocamera
from electrodeController.stereocamera import conversions

gridSize = (5,5) #(8,5)
gridBlockSize = 2.

# order of these frames within the directory is critically important!!!
lFrameDir = 'blender_stereo/left'
rFrameDir = 'blender_stereo/right'
imageExt = '.jpg'
lFileList = [lFrameDir + '/' + f for f in os.listdir(lFrameDir) if imageExt in f]
rFileList = [rFrameDir + '/' + f for f in os.listdir(rFrameDir) if imageExt in f]

sCam = stereocamera.stereocamera.StereoCamera(fakeCameras=True)
sCam.cameras[0].set_file_list(lFileList)
sCam.cameras[1].set_file_list(rFileList)

print "Capturing calibration images"
pylab.ion()
for i in xrange(len(lFrameDir)-2):
    rs = sCam.capture_calibration_images(gridSize)
    print "Found grid?", rs[0][1], rs[1][1]
    if (rs[0][1] == False) or (rs[1][1] == False):
        pylab.subplot(211)
        pylab.imshow(conversions.CVtoNumPy(rs[0][0]))
        pylab.gray()
        pylab.colorbar()
        pylab.subplot(212)
        pylab.imshow(conversions.CVtoNumPy(rs[1][0]))
        pylab.gray()
        pylab.colorbar()
        pylab.show()

print "Calibrating cameras"
errs = sCam.calibrate(gridSize, gridBlockSize)
errs = pylab.array(errs)
print "Calibration errors:"
print "mean(errs)   = c1: %.4f, c2: %.4f" % (pylab.mean(errs[0,:]), pylab.mean(errs[1,:]))
print "max(|errs|)  = c1: %.4f, c2: %.4f" % (abs(errs[0,:]).max(), abs(errs[1,:]).max())

print "Capturing localization images:",
ims, s = sCam.capture_localization_images(gridSize)
print s
if s == False:
    pylab.subplot(211)
    pylab.imshow(conversions.CVtoNumPy(ims[0][0]))
    pylab.gray(); pylab.colorbar()
    pylab.subplot(212)
    pylab.imshow(conversions.CVtoNumPy(ims[1][0]))
    pylab.gray(); pylab.colorbar()
    pylab.show()

lims = (ims[0][0], ims[1][0])

print "Locating cameras"
sCam.locate(gridSize, gridBlockSize)

print "Camera positions", sCam.get_camera_positions()
ps = sCam.get_camera_positions()
dp = pylab.array(ps[0]) - pylab.array(ps[1])
d = pylab.sqrt(pylab.sum(dp ** 2))
print "Delta position:", dp
print "Distance between cameras:", d
print "Distance should be 16, error:", d - 16

pylab.subplot(211)
pylab.imshow(conversions.CVtoNumPy(lims[0]))
pylab.gray(); pylab.colorbar()
pylab.subplot(212)
pylab.imshow(conversions.CVtoNumPy(lims[1]))
pylab.gray(); pylab.colorbar()

# plot error
c1errMean = []
c2errMean = []
c1errMax = []
c2errMax = []
for x in xrange(gridSize[0]):
    for y in xrange(gridSize[1]):
        c1errMean.append(pylab.mean(errs[0,:,x+y*gridSize[0],:]))
        c2errMean.append(pylab.mean(errs[1,:,x+y*gridSize[0],:]))
        c1errMax.append(abs(errs[0,:,x+y*gridSize[0],:]).max())
        c2errMax.append(abs(errs[1,:,x+y*gridSize[0],:]).max())
c1errMean = pylab.array(c1errMean).reshape(gridSize)
c2errMean = pylab.array(c2errMean).reshape(gridSize)
c1errMax = pylab.array(c1errMax).reshape(gridSize)
c2errMax = pylab.array(c2errMax).reshape(gridSize)
pylab.figure(2)
pylab.subplot(221)
pylab.title('c1mean')
pylab.imshow(c1errMean)
pylab.colorbar()
pylab.subplot(222)
pylab.title('c2mean')
pylab.imshow(c2errMean)
pylab.colorbar()
pylab.subplot(223)
pylab.title('c1max')
pylab.imshow(c1errMax)
pylab.colorbar()
pylab.subplot(224)
pylab.title('c2max')
pylab.imshow(c2errMax)
pylab.colorbar()

pylab.show()