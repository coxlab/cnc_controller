#!/usr/bin/env python

from pylab import *
from mpl_toolkits.mplot3d import Axes3D

lx, ly, rx, ry, mx, my, mz, x, y, z = loadtxt('data', unpack=True)

# flip z, conversion from left to right handed
z = -z

# calculate offset
mc = array((mx.mean(), my.mean(), mz.mean()))
c = array((x.mean(), y.mean(), z.mean()))
o = tuple(c - mc)
print "Offset: %+.2f %+.2f %+.2f" % o

# compensate for offset of grid (cv measures from bottom left, xyz is relative to center)
c = [0., 0., 0.]
mc = [3., -2.5, 0.]
x = x - c[0]; y = y - c[1]; z = z - c[2]
mx = mx - mc[0]; my = my - mc[1]; mz = mz - mc[2]

# plot actual and measured data on same plot
ax = Axes3D(figure())
ax.scatter(mx,my,mz,color='r',alpha=0.5)
ax.scatter(x,y,z,color='b',alpha=0.5)

for i in xrange(len(lx)):
    ax.plot([x[i],mx[i]],[y[i],my[i]],[z[i],mz[i]], c='k',alpha=0.1)

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')

maxError = max(abs(x - mx).max(), abs(y - my).max(), abs(z - mz).max())
print "Max Error: %.2f mm (post z-flip and offset)" % maxError

show()