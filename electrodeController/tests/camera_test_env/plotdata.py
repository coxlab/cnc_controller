#!/usr/bin/env python

from pylab import *
from mpl_toolkits.mplot3d import Axes3D
import cv

lx, ly, rx, ry, mx, my, mz, x, y, z = loadtxt('data', unpack=True)

# flip z, conversion from left to right handed
z = -z
# y = -y
# x = -x

# calculate offset
mc = array((mx.mean(), my.mean(), mz.mean()))
c = array((x.mean(), y.mean(), z.mean()))
o = tuple(c - mc)
print "Offset: %+.2f %+.2f %+.2f" % o

# compensate for offset of grid (cv measures from bottom left, xyz is relative to center)
c = [-3.5, -2.5, 0.]
#mc = [3.5, 2.5, 0.]
mc = [0., 0., 0.]
x = x - c[0]; y = y - c[1]; z = z - c[2]
mx = mx - mc[0]; my = my - mc[1]; mz = mz - mc[2]

# plot actual and measured data on same plot
ax = Axes3D(figure())
ax.scatter(mx,my,mz,color='r',alpha=0.5)
ax.scatter(x,y,z,color='b',alpha=0.5)

for i in xrange(len(lx)):
    ax.plot([x[i],mx[i]],[y[i],my[i]],[z[i],mz[i]], c='k',alpha=0.1)

# plot camera locations in green
m0 = cv.Load('calibrations/0/itoWMatrix.xml')
m1 = cv.Load('calibrations/1/itoWMatrix.xml')
p0 = (m0[3,0], m0[3,1], m0[3,2])
p1 = (m1[3,0], m1[3,1], m1[3,2])
ax.scatter([p0[0]],[p0[1]],[p0[2]],c='g')
ax.scatter([p1[0]],[p1[1]],[p1[2]],c='g')

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')

maxXErr = abs(x-mx).max()
maxYErr = abs(y-my).max()
maxZErr = abs(z-mz).max()
print "Max Errors: X: %.2f Y: %.2f Z: %.2f mm" % (maxXErr, maxYErr, maxZErr)

maxError = max(maxXErr, maxYErr, maxZErr)
print "Max Error: %.2f mm (post z-flip and offset)" % maxError

show()