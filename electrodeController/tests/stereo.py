#!/usr/bin/env python

import os, time

import pylab

from electrodeController import stereocamera
from electrodeController.stereocamera import conversions

gridSize = (5,5) #(8,5)
gridBlockSize = 2.

# order of these frames within the directory is critically important!!!
lFrameDir = 'blender_stereo/left'
rFrameDir = 'blender_stereo/right'
lFileList = [lFrameDir + '/' + f for f in os.listdir(lFrameDir)]
rFileList = [rFrameDir + '/' + f for f in os.listdir(rFrameDir)]

sCam = stereocamera.stereocamera.StereoCamera(fakeCameras=True)
sCam.cameras[0].set_file_list(lFileList)
sCam.cameras[1].set_file_list(rFileList)

print "Capturing calibration images"
pylab.ion()
for i in xrange(7):
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
sCam.calibrate(gridSize, gridBlockSize)

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
print "Detla position:", dp
print "Distance between cameras:", d

pylab.subplot(211)
pylab.imshow(conversions.CVtoNumPy(lims[0]))
pylab.gray(); pylab.colorbar()
pylab.subplot(212)
pylab.imshow(conversions.CVtoNumPy(lims[1]))
pylab.gray(); pylab.colorbar()
pylab.show()