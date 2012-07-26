#!/usr/bin/env python

import sys

from pylab import *
from scipy.optimize import leastsq

from bjg import vector

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

def find_normal(x, y, z):
    xyz = transpose(vstack((x,y,z)))
    xyzs = xyz - mean(xyz,0)
    u, s, vh = svd(xyzs)
    i = s.argmin()
    n = vh[i]
    return n

def project_to_plane(x, y, z, n):
    if sum((n - array([0,0,1]))**2) < 0.001:
        u = cross(n, array([0,1,0]))
    else:
        u = cross(n, array([0,0,1]))
    
    v = cross(n, u)
    u = u / norm(u)
    v = v / norm(v)
    P = vector.rebase(u, v, n)
    xyz = transpose(vstack((x,y,z)))
    tpts = vector.apply_matrix_to_points(P, vector.make_homogeneous(xyz))[:,:2]
    return tpts[:,0], tpts[:,1], P

def fit(x, y, z, b, w):
    # find normal of points
    n = find_normal(x, y, z)
    
    # project points onto plane
    u, v, P = project_to_plane(x, y, z, n)
    
    def resCircle(p, u, v, w): # leave out b for now
        """ residuals from circle fit """
        cu, cv, r = p # cu, cv = center, r = radius
        err = sqrt( (u - cu)**2 + (v - cv)**2) + w - r
        #print err
        return err
    
    params = [0., 0., 180.]
    res = leastsq(resCircle, params, args=(u,v,w), ftol=1e-12, xtol=1e-12, maxfev=1e9)#, full_output=True)
    #print res
    #print "Radius:", mParams[2]
    #return mParams
    cu, cv, r = res[0]
    mc = array(vector.apply_matrix_to_points(inv(P),array([[cu,cv,0.,1.]])))[0][:3]
    return mc[0], mc[1], mc[2], r

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
    if len(sys.argv) > 1:
        data = loadtxt(sys.argv[1])
    else:
        data = loadtxt('tipLocations')
    x = data[:,4]
    y = data[:,5]
    z = data[:,6]
    b = data[:,7]
    w = data[:,8]
    from mpl_toolkits.mplot3d import Axes3D
    ax = Axes3D(figure())
    ax.scatter(x,y,z)
    cx, cy, cz, r = fit(x, y, z, b, w)
    print "Center: %.4f %.4f %.4f" % (cx,cy,cz)
    print "Radius: %.4f" % r
    ox = ax.get_xlim3d().copy()
    oy = ax.get_ylim3d().copy()
    oz = ax.get_zlim3d().copy()
    
    xyz = transpose(vstack((x,y,z)))
    xyzs = xyz - mean(xyz,0)
    u, s, vh = svd(xyzs)
    i = s.argmin()
    n = vh[i]
    print "Normal:", n
    vToPt = array((cx,cy,cz)) - mean(xyz,0)
    vToPt = vToPt / norm(vToPt)
    
    for w in data[:,8]:
        draw_circle(ax,array([cx,cy,cz]),n,vToPt,r-w)
    ax.set_xlim3d(ox)
    ax.set_ylim3d(oy)
    ax.set_zlim3d(oz)
    show()