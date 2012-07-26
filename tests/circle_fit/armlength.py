#! /usr/bin/env python

from numpy import *
import sys

lx, ly, rx, ry, x, y, z, a, w = loadtxt(sys.argv[1],unpack=True)

# construct dictionary ordered: byW[w-axis value][angle] = array(x,y,z)
byW = {}
for uw in unique(w):
    byW[uw] = {}

for i in xrange(len(w)):
    byW[w[i]][a[i]] = array([x[i], y[i], z[i]])

# calculate radius of arc for 
radii = {}
mR = []
for (w, byA) in byW.iteritems():
    angles = sort(byA.keys())
    
    accumRadius = 0
    for i in xrange(len(angles)-1):
        dA = angles[i+1] - angles[i]
        v1 = byA[angles[i+1]]
        v2 = byA[angles[i]]
        # calculate distance between tip locations at the two angles of interest
        d = sqrt(sum((v1 -v2)**2))
        # v1, v2, and d create a triangle with base c
        # v1 (or v2), d/2 and c create a right triangle
        # use the right triangle to obtain a measurement of the radius of rotation
        r = (d/2.) / sin(radians(dA/2.))
        # compensate for the known w position
        r += -w # w-axis is flipped
        mR.append(r)
        accumRadius += (sqrt(sum((v1-v2)**2))/2) / sin(radians(dA/2))
    
    radii[w] = accumRadius / (len(angles)-1)

ws = radii.keys()
sorted_ws = sort(ws)
for w in sorted_ws:
    print("%.4f: %.4f : %.4f" % (-w, radii[w], radii[w] + w))


for i in range(0, len(sorted_ws)-1):
    print("w diff: %f, radius diff: %f" % (sorted_ws[i+1] - sorted_ws[0], radii[sorted_ws[0]] - radii[sorted_ws[i+1]]))

print mR
print "Mean R:", mean(array(mR))
print "Median R:", median(array(mR))

import pylab
pylab.hist(mR, bins=15)
pylab.show()