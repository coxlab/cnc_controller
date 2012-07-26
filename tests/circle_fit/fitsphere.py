#!/usr/bin/env python

from pylab import *
from scipy.optimize import leastsq

def draw_circle(ax, center, normal, vToPt, radius):
    r = radius
    c = center
    n = normal
    u = vToPt
    #u = array([n[0],n[2],n[1]]) # 90 degrees? this is WRONG
    v = cross(n,u)
    #a = arange(-pi,pi,pi/32.)
    angles = arange(-pi,pi+pi/320.,pi/320.)
    pts = zeros((len(angles),3))
    for (i,a) in enumerate(angles):
        pts[i] = c + r*cos(a)*u + r*sin(a)*v
    ax.plot(pts[:,0],pts[:,1],pts[:,2])

def generate_fake_data(center, radius, normal, angles, noise):
    r = radius
    c = center
    n = normal

def fit_rays(x, y, z, a, w):
    # x, y, z : tip coordinate in 3d
    # a : angle of b axis
    # w : position of w axis (necessary?)
    
    # project points onto plane (using svd?)
    # xyz = transpose(vstack((x,y,z)))
    # xyzs = xyz - mean(xyz,0)
    # u, s, vh = svd(xyzs)
    # i = s.argmin()
    # n = vh[i]
    # print "Normal:", n
    # vToPt = array((a,b,c)) - mean(xyz,0)
    # vToPt = vToPt / norm(vToPt)
    
    # draw vectors (rays) between points with the same angle (a)
    
    # find location of closest intersection of all rays
    
    # measure radius of rotation (average dist of points from center)
    
    pass

def fit_sphere(x, y, z, angles):
    def resSphere(p,x,y,z,angles):
        """ residuals from sphere fit """
        #print x,y,z
        a,b,c,r = p # a,b,c are center x,y,c coords to be fit, r is the radius to be fit
        distance = sqrt( (x-a)**2 + (y-b)**2 + (z-c)**2 )
        err = distance - r # err is distance from input point to current fitted surface
        return err
    
    params = [0.,400.,0.,180.]
    myResult = leastsq(resSphere, params, args=(x,y,z,angles), ftol=1e-6, xtol=1e-6, maxfev=1e9)
    return myResult[0]

def draw_circle(ax, center, normal, vToPt, radius):
    r = radius
    c = center
    n = normal
    u = vToPt
    #u = array([n[0],n[2],n[1]]) # 90 degrees? this is WRONG
    v = cross(n,u)
    #a = arange(-pi,pi,pi/32.)
    angles = arange(-pi,pi+pi/320.,pi/320.)
    pts = zeros((len(angles),3))
    for (i,a) in enumerate(angles):
        pts[i] = c + r*cos(a)*u + r*sin(a)*v
    ax.plot(pts[:,0],pts[:,1],pts[:,2])

if __name__ == '__main__':
    # data = loadtxt('tip_pts_on_arc')
    # x = data[:,4]
    # y = data[:,5]
    # z = data[:,6]
    # angles = data[:,7]
    data = loadtxt('tipLocations')
    s = 1
    x = data[s::8,4]
    y = data[s::8,5]
    z = data[s::8,6]
    angles = data[s::8,7]
    from mpl_toolkits.mplot3d import Axes3D
    ax = Axes3D(figure())
    ax.scatter(x,y,z)
    # ax.set_xlim3d([-10,15])
    # ax.set_ylim3d([-10,15])
    # ax.set_zlim3d([-10,15])
    #draw circle 
    a,b,c,r = fit_sphere(x,y,z,angles)
    print "Center: %.4f %.4f %.4f" % (a,b,c)
    print "Radius: %.4f" % r
    averageW = average(data[s::8,8])
    print "AverageW: %.4f" % averageW
    armLength = r + averageW
    print "Arm Length: %.4f" % armLength
    
    xyz = transpose(vstack((x,y,z)))
    xyzs = xyz - mean(xyz,0)
    u, s, vh = svd(xyzs)
    i = s.argmin()
    n = vh[i]
    print "Normal:", n
    vToPt = array((a,b,c)) - mean(xyz,0)
    vToPt = vToPt / norm(vToPt)
    
    draw_circle(ax,array([a,b,c]),n,vToPt,r)
    #ax.set_xlim3d([-10,15])
    #ax.set_ylim3d([-10,15])
    #ax.set_zlim3d([-10,15])
    
    show()
