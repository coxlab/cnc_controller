#!/usr/bin/env python

from pylab import *

from bjg import vector

D = loadtxt('cncpts',delimiter=',')

cnc = D[:,3:]
cam = D[:,:3]
hcnc = vector.make_homogeneous(cnc)
hcam = vector.make_homogeneous(cam)

T = vector.fit_rigid_transform(hcnc,hcam)

t, r = vector.decompose_matrix(T)

print "Transform:", t
print "Rotation(d):", degrees(r)