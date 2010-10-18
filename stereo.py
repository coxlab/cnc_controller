#!/usr/bin/env python

import os

from pylab import *
from mpl_toolkits.mplot3d import Axes3D

import cv

from electrodeController.camera.stereocamera import StereoCamera
from electrodeController.camera.filecamera import FileCamera
from electrodeController.camera.conversions import *

logDir = 'inLogs/1287438569'
#logDir = 'inLogs/1286990302' # TODO find most recent
#logDir = 'logs/1286963673'
calDir = 'electrodeController/calibrations'
leftCamID = 49712223528793951
rightCamID = 49712223528793946
gridSize = (11,9)#(8,6)
gridBlockSize = 1.

rcPts = loadtxt(logDir+'/registerCameraPts') # lx ly rx ry

lCamImages = [logDir+'/cameras/'+ str(leftCamID) + '/' + f for f in os.listdir(logDir+'/cameras/' + str(leftCamID))]
lCamImages.sort()
rCamImages = [logDir+'/cameras/'+ str(rightCamID) + '/' + f for f in os.listdir(logDir+'/cameras/' + str(rightCamID))]
rCamImages.sort()

sCam = StereoCamera(leftCamID, rightCamID, FileCamera)
sCam.leftCamera.set_file_list(lCamImages)
sCam.rightCamera.set_file_list(rCamImages)

# calibrate and locate cameras
sCam.load_calibrations(calDir)
lr, rr = sCam.capture_localization_images(gridSize)
if lr[1] == True and rr[1] == True:
    print "Cameras located!"
else:
    print "Cameras could not be located"
sCam.locate(gridSize, gridBlockSize)

figure()
lpts = array(sCam.leftCamera.localizationCorners)
rpts = array(sCam.rightCamera.localizationCorners)
subplot(121)
imshow(CVtoNumPy(sCam.leftCamera.localizationImage))
gray()
plot(lpts[:,0], lpts[:,1], c='b')
scatter(lpts[:,0], lpts[:,1], c='b')
scatter(lpts[0,0], lpts[0,1], c='k')
scatter(rcPts[:,0], rcPts[:,1], c='g')
subplot(122)
imshow(CVtoNumPy(sCam.rightCamera.localizationImage))
gray()
plot(rpts[:,0], rpts[:,1], c='r')
scatter(rpts[:,0], rpts[:,1], c='r')
scatter(rpts[0,0], rpts[0,1], c='k')
scatter(rcPts[:,2], rcPts[:,3], c='g')

ax = Axes3D(figure())

for p in sCam.get_camera_positions():
    ax.scatter([p[0]],[p[1]],[p[2]])

# trying stereo calibrate
gridN = gridSize[0] * gridSize[1]
imPts1 = cv.CreateMat(gridN, 2, cv.CV_64FC1)
imPts2 = cv.CreateMat(gridN, 2, cv.CV_64FC1)
objPts = cv.CreateMat(gridN, 3, cv.CV_64FC1)
npoints = cv.CreateMat(1, 1, cv.CV_32S)
npoints[0,0] = gridN
for j in xrange(gridN):
    imPts1[j,0] = sCam.leftCamera.localizationCorners[j][0]
    imPts1[j,1] = sCam.leftCamera.localizationCorners[j][1]
    imPts2[j,0] = sCam.rightCamera.localizationCorners[j][0]
    imPts2[j,1] = sCam.rightCamera.localizationCorners[j][1]
    objPts[j,0] = (j % gridSize[0]) * gridBlockSize
    objPts[j,1] = (j / gridSize[0]) * gridBlockSize
    objPts[j,2] = 0.

R = cv.CreateMat(3, 3, cv.CV_64FC1)
T = cv.CreateMat(3, 1, cv.CV_64FC1)
E = cv.CreateMat(3, 3, cv.CV_64FC1)
F = cv.CreateMat(3, 3, cv.CV_64FC1)

cv.StereoCalibrate(objPts, imPts1, imPts2, npoints, sCam.leftCamera.camMatrix, sCam.leftCamera.distCoeffs,
                    sCam.rightCamera.camMatrix, sCam.rightCamera.distCoeffs, sCam.leftCamera.imageSize,
                    R, T, E, F,
                    (cv.CV_TERMCRIT_EPS + cv.CV_TERMCRIT_ITER, 30, 0.01), cv.CV_CALIB_FIX_INTRINSIC)
print array(T)
print norm(T)
print array(R)
print array(E)
print array(F)
print array(sCam.leftCamera.itoWMatrix)
print array(sCam.rightCamera.itoWMatrix)
# ------- stereo calibrate

p1, p2 = sCam.get_camera_positions()
p1 = array(p1)
p2 = array(p2)
d = sqrt(sum((p1 - p2)**2))
print "Distance between cameras:", d

# find a grid
ims, pts, s = sCam.locate_grid(gridSize)
if s:
    for p in pts:
        ax.scatter([p[0]],[p[1]],[p[2]],c='k')
else:
    print "failed to find grid in image for 3d"

# find registration points
ref3dPts = []
lrays = []
rrays = []
for p in rcPts:
    print p[0], p[1], p[2], p[3]
    p, lr, rr = sCam.get_3d_position((p[2],p[3]), (p[0],p[1]), andRays=True)
    ref3dPts.append(p)
    lrays.append(lr)
    rrays.append(rr)

for p in ref3dPts:
    ax.scatter([p[0]],[p[1]],[p[2]],c='r')

lc, rc = sCam.get_camera_positions()
lc = array(lc)
rc = array(rc)
for l in lrays:
    l = array(l)
    l = lc + (lc - l)*300.
    ax.plot([lc[0],l[0]],[lc[1],l[1]],[lc[2],l[2]],c='g')
for r in rrays:
    r = array(r)
    r = rc + (rc - r)*300.
    ax.plot([rc[0],r[0]],[rc[1],r[1]],[rc[2],r[2]],c='g')

ax.plot([0,10],[0,0],[0,0],c='r')
ax.plot([0,0],[0,10],[0,0],c='g')
ax.plot([0,0],[0,0],[0,10],c='b')

xl = ax.get_xlim3d(); yl = ax.get_ylim3d(); zl = ax.get_zlim3d()
xr = abs(xl[1] - xl[0]); yr = abs(yl[1] - yl[0]); zr = abs(zl[1] - zl[0])
mr = max((xr,yr,zr))
xl = [xl[0] - (mr - xr)/2., xl[1] + (mr - xr)/2.]
yl = [yl[0] - (mr - yr)/2., yl[1] + (mr - yr)/2.]
zl = [zl[0] - (mr - zr)/2., zl[1] + (mr - zr)/2.]
ax.set_xlim3d(xl); ax.set_ylim3d(yl); ax.set_zlim3d(zl)

ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')

show()