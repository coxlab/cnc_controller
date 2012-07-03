#!/usr/bin/env python

# procedure, move cnc to approximate position, measure position, repeat
# !!!! 3 points on arc, to define plane of rotation and length of arm
# http://www.physicsforums.com/showthread.php?t=173847
#
#  ============== assuming I know the arm length =================
# assuming I know the arm length (which I can measure to some degree of accuracy from drawing)
#   I can calculate the rigid transform from tc coordinates to cnc coordinates (or cam to cnc etc...)
# Then, I might be able to estimate the length of the arm by calculating the point of rotation (in cnc coords)
#
#
#
# test measurement of arm length using calibration procedure
#   assumptions, positions all have same y-axis position
#
#   measure position at the following points
#   0 angle = straight down = +Z
#
#             1 p(a+da,l)
#      2 p(a,l)
#
#                     4 p(a+da,l+dl)
#                   
#          3 p(a,l+dl)
#  movements between 1 & 2 and 3 & 4 are the same (or known angles)
#  movement between 2 & 3 is a known distance (mm)
#
# equation to caculate tip position given angle ang arm length:
#  z = cos(a) * l
#  x = sin(a) * l
# where a = angle (0 = down)
# and l = arm length (static length + w-axis position)
#

from pylab import *
from mpl_toolkits.mplot3d import Axes3D

import vector

l = 2.12
ia = 0.
da = radians(45.) # absurdly large for now
dl = 0.1

# !!!!!!!!!!!!!!!!!!!!!!!!!! order is important
points = matrix([ [sin(ia-da)*l, 0., cos(ia+da)*l, 1.],
            [sin(ia)*l, 0., cos(ia)*l, 1.],
            [sin(ia+da)*l, 0., cos(ia-da)*l, 1.] ])
            # [sin(a)*(l+dl), 0., cos(a)*(l+dl), 1.],
            # [sin(a+da)*(l+dl), 0., cos(a+da)*(l+dl), 1.] ])

# # plot original points
# angles = arange(-pi,pi+0.1,0.1)
# # small circle
# plot(sin(angles)*l,cos(angles)*l, c='b')
# # large circle
# plot(sin(angles)*(l+dl),cos(angles)*(l+dl), c='b')
# # points
# scatter(points[:,0],points[:,1], c='b')
rr = pi/2.
tr = 4.0
A = vector.transform_to_matrix(tr*(rand()-0.5), tr*(rand()-0.5), tr*(rand()-0.5), rr*(rand()-0.5), rr*(rand()-0.5), rr*(rand()-0.5))

transformedPoints = points * A

# ================== measure arm length =====================
# of points
dists1 = [sqrt(sum(array(points[i-1]-points[i])**2)) for i in xrange(len(points))]
r1 = product(dists1) / sqrt(2*dists1[0]**2*dists1[1]**2 + 2*dists1[1]**2*dists1[2]**2 + 2*dists1[2]**2*dists1[0]**2 - dists1[0]**4 - dists1[1]**4 - dists1[2]**4)
print "Found radius of original circle:",r1
print "  Error:", r1 - l

# of transformed points
dists2 = [sqrt(sum(array(transformedPoints[i-1]-transformedPoints[i])**2)) for i in xrange(len(transformedPoints))]
r2 = product(dists2) / sqrt(2*dists2[0]**2*dists2[1]**2 + 2*dists2[1]**2*dists2[2]**2 + 2*dists2[2]**2*dists2[0]**2 - dists2[0]**4 - dists2[1]**4 - dists2[2]**4)
print "Found radius of transformed circle:",r2
print "  Error:", r2 - l

# =================== measure center of rotation ================
# calculate position of d (point halfway along ac)
a = array(points[0])[0]
b = array(points[1])[0]
c = array(points[2])[0]
n1 = vector.calculate_normal(a[:3],b[:3],c[:3])
d1 = a + (c-a)/2.
o1 = ones(4, dtype=float64)
ldb = sqrt(sum((d1[:3] - b[:3])**2))
o1[:3] = (d1[:3] - b[:3]) * (r1/ldb) + b[:3]

a = array(transformedPoints[0])[0]
b = array(transformedPoints[1])[0]
c = array(transformedPoints[2])[0]
n2 = vector.calculate_normal(a[:3],b[:3],c[:3])
d2 = a + (c-a)/2.
o2 = ones(4, dtype=float64)
ldb = sqrt(sum((d2[:3] - b[:3])**2))
o2[:3] = (d2[:3] - b[:3]) * (r2/ldb) + b[:3]

# ================== measure transformation matrix =============
generatedPoints = matrix([ [sin(ia-da)*r2, 0., cos(ia+da)*r2, 1.],
            [sin(ia)*r2, 0., cos(ia)*r2, 1.],
            [sin(ia+da)*r2, 0., cos(ia-da)*r2, 1.] ])
P = vector.calculate_rigid_transform(generatedPoints, transformedPoints)

correctedPoints = transformedPoints * P
print "SSError in transform:", sum(array(correctedPoints - points)**2)

# ================== plotting =========================

def scatter_hPoints(axes, points, **kwargs):
    xs = array(points[:,0])
    ys = array(points[:,1])
    zs = array(points[:,2])
    axes.scatter(xs, ys, zs, **kwargs)

def draw_circle(axes, radius, transformationMatrix=None, **kwargs):
    angles = arange(-pi,pi+0.1,0.1)
    xs = sin(angles) * radius
    ys = zeros(len(angles),dtype=float64)
    zs = cos(angles) * radius
    if transformationMatrix != None:
        ws = ones(len(angles),dtype=float64)
        points = matrix(transpose(vstack((xs,ys,zs,ws)))) * transformationMatrix
        xs = array(points[:,0])
        ys = array(points[:,1])
        zs = array(points[:,2])
    axes.plot3D(ravel(xs),ravel(ys),ravel(zs),**kwargs)

def draw_point(axes, point, **kwargs):
    #axes.scatter(array(point[0]), array(point[1]), array(point[2]), **kwargs)
    axes.text(point[0], point[1], point[2], '.')

def draw_normal(axes, origin, normal, **kwargs):
    axes.plot3D(array([origin[0],origin[0]+normal[0]]),
                array([origin[1],origin[1]+normal[1]]),
                array([origin[2],origin[2]+normal[2]]), **kwargs)

f = figure()
a = Axes3D(f)
scatter_hPoints(a, points, c='b')
#draw_point(a, d1, c='b')
scatter_hPoints(a, vstack((d1,o1)), c='b')
draw_normal(a, o1, n1, c='b')
draw_circle(a, l, c='b')
#draw_circle(a, l+dl, c='b')

scatter_hPoints(a, transformedPoints, c='g')
#draw_point(a, d2, c='g')
scatter_hPoints(a, vstack((d2,o2)), c='g')
draw_normal(a, o2, n2, c='g')
draw_circle(a, l, A, c='g')
#draw_circle(a, l+dl, A, c='g')

scatter_hPoints(a, correctedPoints, c='r')
#draw_point(a, d2, c='g')
#scatter_hPoints(a, vstack((d2,o2)), c='g')
#draw_normal(a, o2, n2, c='g')
#draw_circle(a, l, A, c='g')
#draw_circle(a, l+dl, A, c='g')

a.set_aspect(1.0)

a.set_xlim3d([-tr,tr])
a.set_ylim3d([-tr,tr])
a.set_zlim3d([-tr,tr])

show()

# ============================================
# assuming I know the arm length, I can calculate a rigid transform

# try to calculate arm length
#   given: dl, a, a+da
# z / cos(a) - dl = l
# x / sin(a) - dl = l

