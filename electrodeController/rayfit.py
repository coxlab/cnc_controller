#!/usr/bin/env python

import logging

from pylab import *
from scipy.optimize import leastsq
from scipy.stats import linregress

from mpl_toolkits.mplot3d import Axes3D

import vector #bjg.vector

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


def measure_rotation_plane(pts, angles, radii, debugPlotting=False):
    pts = pts[:,:3] # remove extra dimension from homogeneous imputs
    # measure normal [mn]
    xyzs = pts - mean(pts, 0)
    u, s, vh = svd(xyzs)
    mn = vh[s.argmin()] / norm(vh[s.argmin()])
    #mn = array([0,0,1])

    # project points onto plane
    if sum((mn - array([0,0,1]))**2) < 0.001:
        u = cross(mn, array([0,1,0]))
    else:
        u = cross(mn, array([0,0,1]))
    v = cross(mn, u)
    u = u / norm(u)
    v = v / norm(v)
    P = vector.rebase(u, v, mn)
    tpts = vector.apply_matrix_to_points(P, vector.make_homogeneous(xyzs))[:,:2]

    # reorganize data
    ua = sort(unique(angles))
    ur = sort(unique(radii))
    gd = zeros((len(ua),len(ur),2))
    for (p,a,r) in zip(tpts,angles,radii):
        ai = where(ua == a)[0][0]
        ri = where(ur == r)[0][0]
        gd[ai,ri] = p
    
    if debugPlotting:
        # print tpts
        # print gd
        #     
        # print tpts[0], tpts[2]
        # print gd[0,0], gd[0,1]
        
        figure()
        for (i,p) in enumerate(tpts):
            text(p[0],p[1],i)
        scatter(tpts[:,0],tpts[:,1])
    
    # find  ray intersection
    ms = zeros(len(ua))
    bs = zeros(len(ua))
    for i in xrange(len(ua)):
        r = linregress(gd[i,:,0], gd[i,:,1]) # r = slope, intercept r, ttp, stderr
        ms[i] = r[0]
        bs[i] = r[1]
        ## assume two points per ray for right now
        #ms[i] = (gd[i,1,1] - gd[i,0,1])/(gd[i,1,0] - gd[i,0,0])
        #bs[i] = gd[i,1,1] - ms[i] * gd[i,1,0]
    
    # assume only two angles
    ix = (bs[1] - bs[0])/(ms[0] - ms[1])
    iy = ms[0] * ix + bs[0]
    
    if debugPlotting:
        scatter(ix,iy)
        for i in xrange(len(ua)):
            plot([gd[i,-1,0],gd[i,0,0]],[gd[i,-1,1],gd[i,0,1]])
    
    
    # reproject center to 3d
    mc = array(vector.apply_matrix_to_points(inv(P),array([[ix,iy,0.,1.]])))[0][:3] + mean(pts,0)
    
    # measure radii
    mrs = zeros(len(radii))
    for i in xrange(len(radii)):
        mrs[i] = sqrt(sum((pts[i] - mc)**2))
    
    return mc, mn, mrs


def generate_fake_data(n, c, radii, angles, noise=0.):
    n = n / norm(n)
    if sum((n - array([0,0,1]))**2) < 0.001:
        u = cross(n,array([0,1,0]))
    else:
        u = cross(n,array([0,0,1]))
    v = cross(n,u)
    u = u / norm(u)
    v = v / norm(v)
    
    pts = array([c + r*cos(a)*u + r*sin(a)*v for r,a in zip(radii, angles)])
    pts += (rand(*pts.shape) - 0.5) * noise
    return pts

def basic_test():
    import bjg.cfgBase as cfg
    
    cfg.random = False
    cfg.verbose = False
    cfg.plot = True
    cfg.noise = 0.0 # peak-to-peak
    cfg.err = 0.001 # acceptable error [mm]
    cfg.dataFile = None
    cfg.nAngles = 2
    cfg.nRadii = 3
    cfg.process_command_line()
    
    if cfg.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)
    
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
    
    # --------------- Get Data ---------------
    if cfg.dataFile != None:
        d = loadtxt(cfg.dataFile)
        pts = d[:,4:7]
        angles = d[:,7]
        radii = d[:,8]
        
        mc, mn, mrs = measure_rotation_plane(pts, angles, radii, cfg.plot)
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
        mr3 = median((mrs[4],mrs[5]))
    else:
        # generate fake data (4 points, 2 at radius r1 at angles a1 and a2, 2 at radius r2 at a1 and a2)
        if cfg.random:
            c = (rand(3) - 0.5)*1000.0
            n = (rand(3) - 0.5)
        else:
            c = array([0,0,0]) # center of rotation
            n = array([0,1,0]) # rotation plane normal
        
        n = n / norm(n)
        
        radii = arange(cfg.nRadii) + 90.
        angles = arange(cfg.nAngles) + 40.
        radii = transpose(vstack([radii]*cfg.nAngles)).flatten()
        angles = hstack([angles]*cfg.nRadii)
        # r1 = 90.
        # r2 = 91.
        # r3 = 92.
        # a1 = radians(40.)
        # a2 = radians(45.)
        # radii = array([r1, r1, r2, r2, r3, r3])
        # angles = array([a1, a2, a1, a2, a1, a2])
        #pts = c + radii*cos(angles)*u + radii*sin(angles)*v
        pts = generate_fake_data(n,c,radii,angles,cfg.noise)
        
        mc, mn, mrs = measure_rotation_plane(pts, angles, radii, cfg.plot)
        
        mr1 = median((mrs[0],mrs[1]))
        mr2 = median((mrs[2],mrs[3]))
        mr3 = median((mrs[4],mrs[5]))
        
        logit('Normal', n, mn)
        logit('Center(3d)', c, mc)
        # logit('R', radii, mrs)
        logit('R', 0., median(mrs - radii))
        # logit('R1', r1, mr1)
        # logit('R2', r2, mr2)
        # logit('R3', r3, mr3)
    
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
        draw_circle(ax, mc, mn, mr3)
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
        
        ax.set_xlim3d(oxl)
        ax.set_ylim3d(oyl)
        ax.set_zlim3d(ozl)
        
        show()

def plot_error():
    import bjg.cfgBase as cfg
    
    cfg.random = False
    cfg.verbose = False
    cfg.plot = True
    cfg.noise = 0.0 # peak-to-peak
    cfg.err = 0.001 # acceptable error [mm]
    cfg.dataFile = None
    cfg.nAngles = 2
    cfg.nRadii = 3
    cfg.nReps = 10
    cfg.process_command_line()
    
    radii = arange(cfg.nRadii) + 2.
    
    errs = []
    for r in radii:
        errs.append([])
        for i in xrange(cfg.nReps):
            errs[-1] += list(test_error(r,cfg.noise))
    figure()
    for (i,err) in enumerate(errs):
        subplot(221)
        scatter([radii[i]]*len(err),err)
        subplot(222)
        scatter(radii[i],median(err))
        subplot(223)
        scatter(radii[i],std(err))
        subplot(224)
        scatter(radii[i],mean(err))
    subplot(221)
    title('error')
    xlabel('radii used')
    ylabel('error (actual-measured)')
    subplot(222)
    title('median')
    subplot(223)
    title('std')
    subplot(224)
    title('mean')
    
    # errs = zeros((cfg.nReps,cfg.nRadii*cfg.nAngles))
    # for i in xrange(len(errs)):
    #     errs[i] = test_error(cfg.nRadii,cfg.noise)
    # 
    # for (i,err) in enumerate(errs):
    #     scatter([i]*len(err),err)
    # xlabel('repetitions')
    # ylabel('error (actual-measured)')
    
    # radii = arange(3) + 3
    # noise = arange(0.0,0.1,0.001)
    # errGrid = zeros((len(radii),len(noise)))
    # for (i,r) in enumerate(radii):
    #     for (j,n) in enumerate(noise):
    #         errGrid[i,j] = sum(test_error(r,n))
    # #imshow(errGrid)
    # c = contourf(noise,radii,errGrid)
    # colorbar(c)
    
    show()

def test_error(nRadii, noise):
    c = (rand(3) - 0.5)*1000.0
    n = (rand(3) - 0.5)
    n = n / norm(n)
    
    #nRadii = 3
    nAngles = 2
    radii = arange(nRadii) + 90.
    angles = arange(nAngles) * 1. + 40.
    radii = transpose(vstack([radii]*nAngles)).flatten()
    angles = hstack([angles]*nRadii)
    
    pts = generate_fake_data(n,c,radii,angles,noise)
    
    mc, mn, mrs = measure_rotation_plane(pts, angles, radii, False)
    
    # logit('Normal', n, mn)
    # logit('Center(3d)', c, mc)
    
    return (radii - mrs)

if __name__ == '__main__':
    basic_test()
    #plot_error()
    