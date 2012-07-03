#!/usr/bin/env python

import os, sys

from pylab import *
import cv

calDir = 'calibrations/0'
imFiles = [calDir+'/images/'+f for f in os.listdir(calDir+'/images') if 'png' in f]
ptFiles = [calDir+'/images/'+f for f in os.listdir(calDir+'/images') if 'pts' in f]
imFiles.sort()
ptFiles.sort()

for i in xrange(len(imFiles)):
    im = imread(imFiles[i])
    pts = loadtxt(ptFiles[i])
    f = figure()
    imshow(im)
    gray()
    scatter(pts[:,0],pts[:,1],c='b')
    scatter(pts[0,0],pts[0,1],c='r')
    plot(pts[:,0],pts[:,1])

im = imread(calDir+'/localizationImage.png')
pts = loadtxt(calDir+'/localizationPts.pts')
f = figure()
imshow(im)
gray()
scatter(pts[:,0],pts[:,1],c='b')
scatter(pts[0,0],pts[0,1],c='r')
plot(pts[:,0],pts[:,1])
title('localization')


show()