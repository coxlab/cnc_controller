#!/usr/bin/env python

import logging

from pylab import *
from scipy.optimize import leastsq

from mpl_toolkits.mplot3d import Axes3D

import bjg.vector
import bjg.cfgBase as cfg

cfg.random = False
cfg.verbose = False
cfg.plot = True
cfg.noise = 0.0 # peak-to-peak
cfg.err = 0.001 # acceptable error [mm]
cfg.dataFile = None
cfg.process_command_line()

if cfg.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.WARNING)

def draw_circle(ax, center, normal, radius):
    r = radius
    c = center
    n = normal
    u = cross(n,array([0,0,1]))
    v = cross(n,u)
    u = u / norm(u)
    v = v / norm(v)
    #a = arange(-pi,pi,pi/32.)
    angles = arange(-pi,pi+pi/320.,pi/320.)
    pts = zeros((len(angles),3))
    for (i,a) in enumerate(angles):
        pts[i] = c + r*cos(a)*u + r*sin(a)*v
    ax.plot(pts[:,0],pts[:,1],pts[:,2])

def logit(label, actual, measured, threshold = cfg.err):
    sse = sum((actual-measured)**2)
    if sse > threshold:
        p = logging.warning
    else:
        p = logging.debug
    p(label)
    p('\tActual:'+str(actual))
    p('\tMeasured:'+str(measured))
    p('\tSSE:'+str(sse))


def measure_rotation_plane(pts, angles, radii):
    # measure normal [mn]
    xyzs = pts - mean(pts, 0)
    u, s, vh = svd(xyzs)
    mn = vh[s.argmin()] / norm(vh[s.argmin()])

    # project points onto plane
    u = cross(mn, array([0,0,1]))
    v = cross(mn, u)
    u = u / norm(u)
    v = v / norm(v)
    P = bjg.vector.rebase(u, v, mn)
    tpts = bjg.vector.apply_matrix_to_points(P, bjg.vector.make_homogeneous(xyzs))[:,:2]

    # reorganize data
    ua = sort(unique(angles))
    ur = sort(unique(radii))
    gd = zeros((len(ua),len(ur),2))
    for (p,a,r) in zip(tpts,angles,radii):
        ai = where(ua == a)[0][0]
        ri = where(ur == r)[0][0]
        gd[ai,ri] = p
    
    print tpts
    print gd
    
    print tpts[0], tpts[2]
    print gd[0,0], gd[0,1]
    
    figure()
    for (i,p) in enumerate(tpts):
        text(p[0],p[1],i)
    scatter(tpts[:,0],tpts[:,1])
    
    # find  ray intersection
    ms = zeros(len(ua))
    bs = zeros(len(ua))
    for i in xrange(len(ua)):
        # assume two points per ray for right now
        ms[i] = (gd[i,1,1] - gd[i,0,1])/(gd[i,1,0] - gd[i,0,0])
        bs[i] = gd[i,1,1] - ms[i] * gd[i,1,0]
    
    # assume only two angles
    ix = (bs[1] - bs[0])/(ms[0] - ms[1])
    iy = ms[0] * ix + bs[0]
    
    scatter(ix,iy)
    for i in xrange(len(ua)):
        plot([gd[i,1,0],gd[i,0,0]],[gd[i,1,1],gd[i,0,1]])
    

    # reproject center to 3d
    mc = array(bjg.vector.apply_matrix_to_points(inv(P),array([[ix,iy,0.,1.]])))[0][:3] + mean(pts,0)

    # measure radii
    mrs = zeros(len(radii))
    for i in xrange(len(radii)):
        mrs[i] = sqrt(sum((pts[i] - mc)**2))

    return mc, mn, mrs


# --------------- Get Data ---------------
if cfg.dataFile != None:
    d = loadtxt(cfg.dataFile)
    pts = d[:,4:7]
    angles = d[:,7]
    radii = d[:,8]
    
    mc, mn, mrs = measure_rotation_plane(pts, angles, radii)
    print "Center:", mc
    print "Normal:", mn
    print "Radii:", mrs
    print
    print "Radius", median(mrs - radii)
    
    # for plottings
    c = mc
    n = mn
    
    mr1 = median((mrs[0],mrs[1]))
    mr2 = median((mrs[2],mrs[3]))
else:
    # generate fake data (4 points, 2 at radius r1 at angles a1 and a2, 2 at radius r2 at a1 and a2)
    if cfg.random:
        c = (rand(3) - 0.5)*1000.0
        n = (rand(3) - 0.5)
    else:
        c = array([0,0,0]) # center of rotation
        n = array([0,1,0]) # rotation plane normal

    n = n / norm(n)
    u = cross(n,array([0,0,1])) # vector to a point on the circle
    v = cross(n,u)
    u = u / norm(u)
    v = v / norm(v)
    r1 = 50.
    r2 = 55.
    a1 = radians(40.)
    a2 = radians(45.)
    radii = array([r1, r1, r2, r2])
    angles = array([a1, a2, a1, a2])
    #pts = c + radii*cos(angles)*u + radii*sin(angles)*v
    pts = array([ c + r1*cos(a1)*u + r1*sin(a1)*v,
                c + r1*cos(a2)*u + r1*sin(a2)*v,
                c + r2*cos(a1)*u + r2*sin(a1)*v,
                c + r2*cos(a2)*u + r2*sin(a2)*v])
    # add noise
    pts += (rand(*pts.shape) - 0.5) * cfg.noise

    mc, mn, mrs = measure_rotation_plane(pts, angles, radii)

    mr1 = median((mrs[0],mrs[1]))
    mr2 = median((mrs[2],mrs[3]))

    logit('Normal', n, mn)
    logit('Center(3d)', c, mc)
    logit('R1', r1, mr1)
    logit('R2', r2, mr2)


# # -------------- Normal: measure normal of points --------------------
# xyzs = pts - mean(pts,0)
# u, s, vh = svd(xyzs)
# i = s.argmin()
# mn = vh[i]
# mn = mn/norm(mn)
# logit('Normal', n, mn)
# 
# 
# # -------------- Project onto Plane -----------------------------------
# # TODO there has to be a better way to do this, brain is not working
# u = cross(mn, array([0,0,1]))
# v = cross(mn, u)
# u = u / norm(u)
# v = v / norm(v)
# P = bjg.vector.rebase(u, v, mn)
# v1 = u
# v2 = v
# v3 = mn
# 
# # ss = sort(s)[::-1]
# # v1 = vh[list(s).index(ss[0])]
# # v2 = vh[list(s).index(ss[1])]
# # v3 = vh[list(s).index(ss[2])]
# 
# P = bjg.vector.rebase(v1/norm(v1), v2/norm(v2), v3/norm(v3))
# hpts = bjg.vector.make_homogeneous(xyzs)
# tpts = bjg.vector.apply_matrix_to_points(P,hpts)[:,:2]
# 
# 
# # --------------- Find Ray Intersection --------------------------------
# m1 = (tpts[2,1] - tpts[0,1])/(tpts[2,0] - tpts[0,0])
# m2 = (tpts[3,1] - tpts[1,1])/(tpts[3,0] - tpts[1,0])
# b1 = tpts[2,1] - m1 * tpts[2,0]
# b2 = tpts[3,1] - m2 * tpts[3,0]
# ix = (b2 - b1)/(m1 - m2)
# iy = m1*ix + b1
# 
# 
# # ------------------ Reproject center to 3d ----------------------
# mc = array(bjg.vector.apply_matrix_to_points(inv(P),array([[ix,iy,0.,1.]])))[0][:3] + mean(pts,0)
# logit('Center(3d)', c, mc)
# 
# 
# # --------------- Measure Radius ----------------------------------------
# ds = sqrt(sum((pts-mc)**2,1))
# mr1a, mr1b, mr2a, mr2b = ds
# # mr1a = sqrt((tpts[0,0] - ix)**2 + (tpts[0,1] - iy)**2)
# # mr1b = sqrt((tpts[1,0] - ix)**2 + (tpts[1,1] - iy)**2)
# # mr1a = sqrt(sum((tpts[0] - (ix,iy))**2))
# # mr1b = sqrt(sum((tpts[1] - (ix,iy))**2))
# mr1 = median((mr1a,mr1b))
# logit('R1', r1, mr1)
# 
# # mr2a = sqrt((tpts[2,0] - ix)**2 + (tpts[2,1] - iy)**2)
# # mr2b = sqrt((tpts[3,0] - ix)**2 + (tpts[3,1] - iy)**2)
# # mr2a = sqrt(sum((tpts[2] - (ix,iy))**2))
# # mr2b = sqrt(sum((tpts[3] - (ix,iy))**2))
# mr2 = median((mr2a,mr2b))
# logit('R2', r2, mr2)


# --------------------- Plotting -----------------------------------
if cfg.plot:
    ax = Axes3D(figure())
    ax.scatter(pts[:,0],pts[:,1],pts[:,2])
    for i in xrange(pts.shape[0]):
        ax.text3D(pts[i,0],pts[i,1],pts[i,2],str(i))
    oxl = ax.get_xlim3d().copy()
    oyl = ax.get_ylim3d().copy()
    ozl = ax.get_zlim3d().copy()
    ax.scatter([c[0]],[c[1]],[c[2]], c='b')
    ax.scatter([mc[0]],[mc[1]],[mc[2]], c='r')
    draw_circle(ax, mc, mn, mr1)
    draw_circle(ax, mc, mn, mr2)
    # scale 1:1:1
    xl = ax.get_xlim3d()
    yl = ax.get_ylim3d()
    zl = ax.get_zlim3d()
    xr = xl[1] - xl[0]
    yr = yl[1] - yl[0]
    zr = zl[1] - zl[0]
    nr = max((xr,yr,zr))
    xl = (xl - (xl[0] + xr/2.)) * nr / xr + xl[0] + xr/2.
    yl = (yl - (yl[0] + yr/2.)) * nr / yr + yl[0] + yr/2.
    zl = (zl - (zl[0] + zr/2.)) * nr / zr + zl[0] + zr/2.
    ax.set_xlim3d(xl)
    ax.set_ylim3d(yl)
    ax.set_zlim3d(zl)
    
    print oxl
    ax.set_xlim3d(oxl)
    ax.set_ylim3d(oyl)
    ax.set_zlim3d(ozl)
    
    
    # figure()
    # scatter(tpts[:,0],tpts[:,1],c='b')
    # scatter(ix,iy,c='r')
    # plot([tpts[2,0],ix],[tpts[2,1],iy],c='g')
    # plot([tpts[3,0],ix],[tpts[3,1],iy],c='g')
    
    show()