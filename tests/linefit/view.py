#!/usr/bin/env python

import sys

# importing glumpy messes with pylab.show, not sure the best way to handle this
import glumpy
import glumpy.atb as atb
from ctypes import *

import OpenGL.GL as gl
import OpenGL.GLUT as glut

import numpy
import pylab
import mpl_toolkits.mplot3d as m3d
from scipy.optimize import leastsq

from bjg import glObj

scanFile = 'scans/H7/hatInSkull_cropped.obj'
texFile = 'scans/H7/hatInSkull.png'

from linefit import fit_3d_line

def quit(*args, **kwargs):
    sys.exit()

def view():
    # generate 4 random points in 3 space with noise
    # line in 3d
    # [x y z] = [a b c]t + [x0 y0 z0]
    #xyz0 = pylab.matrix((0., 0., 0.))
    global pts, noise, a, b, c, x0, y0, z0, ts, npts, lineParams, dataFile
    dataFile = 'tipLocations'
    noise = 0.1
    noise = c_float(0.1)
    a = c_float(0.)
    b = c_float(1.)
    c = c_float(0.)
    x0 = c_float(0.)
    y0 = c_float(0.)
    z0 = c_float(0.)
    npts = c_int(10)
    #abc = pylab.matrix((0., 1., 0.))
    ts = range(npts.value) # locations on line
    pts = []
    lineParams = [0., 0., 0., 0., 1., 0.]
    
    atb.init()
    
    # load obj file
    obj = glObj.GLOBJ()
    obj.load(scanFile, texFile)
    obj.prep_lists()
    
    glut.glutInit(sys.argv)
    glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGBA | glut.GLUT_DEPTH)
    
    window = glumpy.Window(600,600)
    trackball = glumpy.Trackball(65,135,1.25,50)
    
    bar = atb.Bar(name="Controls", label="Controls",
                    help="Scene Controls", position=(10,10), size=(200,320))
    bar.add_var("Trackball/Phi", step=0.5,
                getter=trackball._get_phi, setter=trackball._set_phi)
    bar.add_var("Trackball/Theta", step=0.5,
                getter=trackball._get_theta, setter=trackball._set_theta)
    bar.add_var("Trackball/Zoom", step=0.01,
                getter=trackball._get_zoom, setter=trackball._set_zoom)
    bar.add_var("Slope/a", a, step=0.01)
    bar.add_var("Slope/b", b, step=0.01)
    bar.add_var("Slope/c", c, step=0.01)
    bar.add_var("Origin/x", x0, step=0.01)
    bar.add_var("Origin/y", y0, step=0.01)
    bar.add_var("Origin/z", z0, step=0.01)
    bar.add_var("Noise", noise, step=0.01)
    bar.add_var("NPts", npts)
    
    def load_points():
        global dataFile, pts, ts, lineParams
        data = pylab.loadtxt(dataFile)
        pts = data[:,4:7]
        ts = data[:,8]
        lineParams = fit_3d_line(pts,ts)
    
    bar.add_button("LoadPoints", load_points, help="Load Points from Datafile", key="l")
    
    def regenerate_points():
        global pts, a, b, c, x0, y0, z0, noise, ts, npts, lineParams
        ts = pylab.array(range(npts.value)) * -1.
        abc = pylab.matrix((a.value, b.value, c.value))
        abc = abc / pylab.norm(abc)
        a.value = float(abc[0,0])
        b.value = float(abc[0,1])
        c.value = float(abc[0,2])
        xyz0 = pylab.matrix((x0.value, y0.value, z0.value))
        pts = []
        for t in ts:
            pts.append(pylab.array(abc*t + xyz0)[0] + (pylab.random(3)-0.5) * noise.value * 2.)
        pts = pylab.array(pts)
        # # fit line to points, I know:
        # # x y z t of all points (x,y,z = location, t = distance from origin)
        # # I need to know, a,b,c
        # #
        # # I'm assuming xyz0 = 0,0,0
        # #
        # # so params to be fit are:
        # # - a, b, c
        # ps = [0., 0., 0., 0., 0., 0.]
        # 
        # # function for calculating residuals of fit
        # def res_line(p, pts, ts):
        #     a, b, c, x0, y0, z0 = p
        #     abc = pylab.matrix([a,b,c])
        #     xyz0 = pylab.matrix([x0,y0,z0])
        #     errs = []
        #     for i in xrange(len(ts)):
        #         pxyz = abc*ts[i] + xyz0
        #         err = pylab.sqrt(sum((pylab.array(pxyz)[0] - pts[i])**2))
        #         errs.append(err)
        #     return errs
        # 
        # # compute least squares best fit
        # res = leastsq(res_line, ps, args=(pts, ts))
        lineParams = fit_3d_line(pts,ts)
        #res = [lineParams, 0] # I'm lazy
        
        # print results
        print ""
        print "--ABC--"
        print "Found  a: %.3f b: %.3f c: %.3f" % (lineParams[3], lineParams[4], lineParams[5])
        print "Actual a: %.3f b: %.3f c: %.3f" % (a.value, b.value, c.value)
        print "Diff   a: %.3f b: %.3f c: %.3f" % (a.value - lineParams[3], b.value - lineParams[4], c.value - lineParams[5])
        print ""
        print "--XYZ--"
        print "Found  x: %.3f y: %.3f z: %.3f" % (lineParams[0], lineParams[1], lineParams[2])
        print "Actual x: %.3f y: %.3f z: %.3f" % (x0.value, y0.value, z0.value)
        print "Diff   x: %.3f y: %.3f z: %.3f" % (x0.value - lineParams[0], y0.value - lineParams[1], z0.value - lineParams[2])
        
    
    bar.add_button("RegenPoints", regenerate_points, help="Regenerate Points", key="r")
    #bar.add_var("Trackball/Distance", step=0.5,
    #            getter=trackball._get_distance, setter=trackball._set_distance)
    bar.add_separator("")
    bar.add_button("Quit", quit, key="ESCAPE", help="Quit Application")
    
    def draw_background():
        viewport = gl.glGetIntegerv(gl.GL_VIEWPORT)
        gl.glDisable (gl.GL_LIGHTING)
        gl.glDisable (gl.GL_DEPTH_TEST);
        gl.glBegin(gl.GL_QUADS)
        gl.glColor(1.0,1.0,1.0)
        gl.glVertex(0,0,-1)
        gl.glVertex(viewport[2],0,-1)
        gl.glColor(0.0,0.5,1.0)
        gl.glVertex(viewport[2],viewport[3],0)
        gl.glVertex(0,viewport[3],0)
        gl.glEnd()
    
    def draw_axes():
        gl.glColor(1.,0.,0.)
        gl.glBegin(gl.GL_LINES)
        gl.glVertex3f(0., 0., 0.)
        gl.glVertex3f(1., 0., 0.)
        gl.glEnd()
        gl.glColor(0.,1.,0.)
        gl.glBegin(gl.GL_LINES)
        gl.glVertex3f(0., 0., 0.)
        gl.glVertex3f(0., 1., 0.)
        gl.glEnd()
        gl.glColor(0.,0.,1.)
        gl.glBegin(gl.GL_LINES)
        gl.glVertex3f(0., 0., 0.)
        gl.glVertex3f(0., 0., 1.)
        gl.glEnd()
    
    def draw_points():
        gl.glColor(0.,0.,0.)
        gl.glBegin(gl.GL_POINTS)
        for p in pts:
            gl.glVertex3f(p[0],p[1],p[2])
        gl.glEnd()
    
    def draw_line():
        xyz0 = pylab.matrix(lineParams[:3]) + pylab.matrix(lineParams[3:])*-1000.
        xyz1 = pylab.matrix(lineParams[:3]) + pylab.matrix(lineParams[3:])*1000.
        xyz0 = pylab.array(xyz0)[0]
        xyz1 = pylab.array(xyz1)[0]
        gl.glColor(1., 0., 0.)
        gl.glBegin(gl.GL_LINES)
        gl.glVertex3f(*xyz0)
        gl.glVertex3f(*xyz1)
        gl.glEnd()
        gl.glColor(0., 1., 0.)
        gl.glPointSize(10)
        gl.glBegin(gl.GL_POINTS)
        gl.glVertex3f(*(lineParams[:3]))
        gl.glEnd()
    
    def on_init():
        gl.glEnable (gl.GL_LIGHT0)
        gl.glLightfv (gl.GL_LIGHT0, gl.GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))
        gl.glLightfv (gl.GL_LIGHT0, gl.GL_AMBIENT, (0.1, 0.1, 0.1, 1.0))
        gl.glLightfv (gl.GL_LIGHT0, gl.GL_POSITION,(0.0, 2.0, 2.0, 0.0))
        gl.glEnable (gl.GL_BLEND)
        gl.glEnable (gl.GL_COLOR_MATERIAL)
        gl.glColorMaterial(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE)
        gl.glBlendFunc (gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
    
    def on_draw():
        window.clear()
        draw_background()
        trackball.push()
        gl.glEnable(gl.GL_DEPTH_TEST)
        #
        obj.display()
        draw_points()
        draw_line()
        draw_axes()
        trackball.pop()
    
    def on_mouse_drag(x, y, dx, dy, button):
        trackball.drag_to(x,y,dx,dy)
        window.draw()
    
    def on_mouse_scroll(x, y, dx, dy):
        trackball.zoom_to(x,y,dx,dy)
        window.draw()
    
    def on_key_press(symbol, modifiers):
        if symbol == glumpy.key.ESCAPE:
            sys.exit()
    
    window.push_handlers(on_init,on_mouse_drag, on_mouse_scroll, on_key_press)
    window.push_handlers(atb.glumpy.Handlers(window))
    window.push_handlers(on_draw)
    window.mainloop()

def test_errors():
    # test the overall error of the fit (sum of squares of fitting params a, b, c, x0, y0, z0)
    def test_error(a,b,c,x0,y0,z0,noise,ts):
        #global pts, a, b, c, x0, y0, z0, noise, ts, npts
        abc = pylab.matrix((a, b, c))
        abc = abc/pylab.norm(abc)
        xyz0 = pylab.matrix((x0, y0, z0))
        pts = []
        for t in ts:
            pts.append(pylab.array(abc*t + xyz0)[0] + (pylab.random(3)-0.5) * noise * 2.)
        pts = pylab.array(pts)
        lineParams = fit_3d_line(pts,ts)
        success = True
        # if not res[4] in [1,2,3,4]:
        #     print ""
        #     print "Fitting Failed: %s" % res[3]
        #     print "abc = %+.2f(%+.2f) %+.2f(%+.2f) %+.2f(%+.2f)" % (a, lineParams[0], b, lineParams[1], c, lineParams[2])
        #     print "xyz = %+4.f(%+4.f) %+4.f(%+4.f) %+4.f(%+4.f)" % (x0, lineParams[3], y0, lineParams[4], z0, lineParams[5])
        #     success = False
        # else:
        #     success = True
        # calc sum of squares errror
        slopeError = pylab.mean([abs(a - lineParams[3]), abs(b - lineParams[4]), abs(c - lineParams[5])])
        originError = pylab.mean([abs(x0 - lineParams[0]), abs(y0 - lineParams[1]), abs(z0 - lineParams[2])])
        return slopeError, originError, success
    #print "%3f, %3f" % test_error(0,1,0,0,0,0,0.1,pylab.array(range(10))+10.)
    #return
    # I want to see if errors are independent
    slopeErrors = []
    originErrors = []
    originDists = []
    slopeDists = []
    nErrs = 0
    nFits = 10
    errSlopes = []
    errOrigins = []
    for i in xrange(nFits):
        # generate random origin
        origin = (pylab.random(3) - 0.5) * 2. * 1000.
        # generate random slope
        #slopes = pylab.array([0.,1.,0.])
        slopes = (pylab.random(3) - 0.5) * 2 * 10.
        slopes = slopes / pylab.norm(slopes)
        ts = pylab.array(range(10)) * 0.1
        noise = 0.01
        
        # check to make sure points are still 1 unit apart (as per ts)
        pts = []
        for t in ts:
            s = pylab.matrix(slopes)
            o = pylab.matrix(origin)
            pts.append(s * t + o)
        for i in xrange(len(pts)-1):
            p1 = pylab.array(pts[i])[0]
            p2 = pylab.array(pts[i+1])[0]
            #print p1, p2
            #if abs(pylab.dist(p1, p2) - 1.) > 0.01:
            #    print "Distance was more than 1: %f" % pylab.dist(p1,p2)
        
        sE, oE, s = test_error(slopes[0],slopes[1],slopes[2],origin[0],origin[1],origin[2],noise,ts)
        if s: # if the fitting succeeded
            slopeErrors.append(sE)
            originErrors.append(oE)
            slopeDists.append(pylab.dist(pylab.array([0.,0.,0.]), slopes))
            originDists.append(pylab.dist(pylab.array([0.,0.,0.]), origin))
        else:
            errSlopes.append(slopes)
            errOrigins.append(origin)
            nErrs += 1
    print "%i fitting attempts failed: %2f%%" % (nErrs, nErrs / float(nFits) * 100.)
    print "--Error Slopes, Origins--"
    for i in xrange(len(errSlopes)):
        print "%+.2f %+.2f %+.2f : %+4.f %+4.f %+4.f" % (errSlopes[i][0], errSlopes[i][1], errSlopes[i][2], errOrigins[i][0], errOrigins[i][1], errOrigins[i][2])
    # plot slopeError as a function of origin distance
    pylab.figure(1)
    pylab.subplot(211)
    pylab.xlabel('originDists')
    pylab.scatter(originDists, slopeErrors,c='b', label='slope')
    # plot originError as a function of origin distance
    pylab.scatter(originDists, originErrors,c='r', label='origin')
    pylab.legend()
    
    # plot slopeError as a function of slope distance(?)
    pylab.subplot(212)
    pylab.xlabel('slopeDists')
    pylab.scatter(slopeDists, slopeErrors, c='b', label='slope')
    # plot originError as a function of slope distance(?)
    pylab.scatter(slopeDists, originErrors, c='r', label='origin')
    pylab.legend()
    pylab.show()

if __name__ == '__main__':
    view()
    #test_errors()