#!/usr/bin/env python

from pylab import *

# tests to rotate about a point with a 5-axis cnc
# using ONLY
#  - B rotation
#  - W movement
#  - X movement
# and knowing only the length of the arm (~212.789617 mm [minus offset of 1317 = 0.459]) = 212.331

armLength = 10#212.331 # mm #.458956

# moving w more negative actually INCREASES the length of the arm
# max arm length can be armLength + 50mm

maxArmLength = armLength + 50. # mm

# so assume angle of 0 and minimum arm length to start

def point_on_circle(angle, radius):
    """
    Center of circle is 0,0
    Angle in degrees
    """
    x = sin(radians(angle)) * radius
    y = cos(radians(angle)) * radius
    return x,y

def virtual_rotation(angle, radius, currAngle):
    """
    Center of circle is 0,0
    Angle is target angular position in degrees
    """
    x0,y0 = point_on_circle(currAngle, radius)
    x1,y1 = point_on_circle(angle, radius)
    return x1-x0, y1-y0

# def virtual_rotation(deltaAngle, armLength, currAngle):
#     """Angle is in degrees"""
#     dx = sin(radians(currAngle+deltaAngle)) * armLength
#     dy = -((armLength - cos(radians(currAngle+deltaAngle)) * armLength))
#     # check bounds
#     # calculate speeds
#     # execute moves
#     return dx, dy

figure()
#plot([0,0],[0,-armLength]) # 0 angle, down

# def test_angle(angle,armLength,currAngle):
#     x, y = virtual_rotation(currAngle+deltaAngle, armLength)
#     plot([x,0],[y,-armLength])
#     dist = (x**2 + (y+armLength)**2) ** 0.5
#     print "dx: %.2f\tdy:%.2f\tAngle: %.2f\tDist: %f" % (x,y,angle, dist)

x, y, a = 0., armLength, 0.
for ta in arange(0,360,5):
    dx, dy = virtual_rotation(ta, armLength, a)
    x += dx
    y += dy
    a = ta
    plot([x,0],[y,0])
    dist = (x**2 + y**2) ** 0.5
    print "dx: %.2f\tdy:%.2f\tta: %.2f\tDist: %f" % (dx,dy,ta, dist)

xlims = xlim()
ylims = ylim()
hr = max(xlims[1]-xlims[0],ylims[1]-ylims[0]) / 2.
xc = (xlims[1]+xlims[0]) / 2.
yc = (ylims[1]+ylims[0]) / 2.
xlim([xc-hr,xc+hr])
ylim([yc-hr,yc+hr])

show()