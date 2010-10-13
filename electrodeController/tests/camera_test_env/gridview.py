#!/usr/bin/env python

import os, sys

from PIL import Image

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import atb
from ctypes import *

import cv
import pylab

from bjg.glObj import loadTexture

# sys.path hack
import sys
sys.path.append('../..')
from camera import stereocamera, stringcamera, conversions

def quit(*args, **kwargs):
    sys.exit()

global sCam
sCam = None

global texId
texId = None

global commands
commands = []

def flatten_list(x):
    """flatten(sequence) -> list

    Returns a single, flat list which contains all elements retrieved
    from the sequence and all recursively contained sub-sequences
    (iterables).

    Examples:
    >>> [1, 2, [3,4], (5,6)]
    [1, 2, [3, 4], (5, 6)]
    >>> flatten([[[1,2,3], (42,None)], [4,5], [6], 7, MyVector(8,9,10)])
    [1, 2, 3, 42, None, 4, 5, 6, 7, 8, 9, 10]"""

    result = []
    for el in x:
        #if isinstance(el, (list, tuple)):
        if hasattr(el, "__iter__") and not isinstance(el, basestring):
            result.extend(flatten_list(el))
        else:
            result.append(el)
    return result

#===== Camera functions ======
def test_points():
    xs = pylab.arange(-7,7.1,3.5)
    ys = [0]#pylab.arange(-6,6.1,3)
    zs = [0]#pylab.arange(-10,10.1,5)
    print "#lx  ly  rx  ry   mx   my   mz    x    y    z"
    for z in zs:
        for y in ys:
            for x in xs:
                pointX.value, pointY.value, pointZ.value = x, y, z
                s, l = find_point()
                #s = False
                if s:
                    print "%i %i %i %i %+.2f %+.2f %+.2f %+.2f %+.2f %+.2f" % (l[0], l[1], l[2], l[3], l[4], l[5], l[6], x, y, z)

def find_point():
    global sCam
    x, y, w, h = glGetIntegerv(GL_VIEWPORT)
    # hide grid
    gridZ.value = cameraZ.value * 10.
    # capture images
    cameraX.value = -camX.value
    cameraY.value = camY.value
    cameraZ.value = camZ.value
    b = capture_scene()
    sCam.leftCamera.set_string_buffer(b, (h, w, 3), pylab.uint8)
    cameraX.value = camX.value
    cameraY.value = camY.value
    cameraZ.value = camZ.value
    b = capture_scene()
    sCam.rightCamera.set_string_buffer(b, (h, w, 3), pylab.uint8)
    lim, rim = sCam.capture()
    lim = conversions.CVtoNumPy(lim)
    rim = conversions.CVtoNumPy(rim)
    # try to find point
    #print lim.max(), rim.max()
    if lim.max() < 200 or rim.max() < 200:
        # point not visible
        return False, None
    ly, lx = divmod(lim.argmax(), w)
    ry, rx = divmod(rim.argmax(), w)
    x, y, z = sCam.get_3d_position((lx,ly),(rx,ry))
    #print x, y, z
    return True, (lx, ly, rx, ry, x, y, z)

def find_grid():
    global sCam
    x, y, w, h = glGetIntegerv(GL_VIEWPORT)
    # render left
    cameraX.value = -camX.value
    cameraY.value = camY.value
    cameraZ.value = camZ.value
    b = capture_scene()
    sCam.leftCamera.set_string_buffer(b, (h, w, 3), pylab.uint8)
    lim, lPts, s = sCam.leftCamera.capture_grid_image((8,6))
    if not s:
        return
    # render right
    cameraX.value = camX.value
    cameraY.value = camY.value
    cameraZ.value = camZ.value
    b = capture_scene()
    sCam.rightCamera.set_string_buffer(b, (h, w, 3), pylab.uint8)
    rim, rPts, s = sCam.rightCamera.capture_grid_image((8,6))
    if not s:
        return
    # calculate 3d and measure error
    errs = []
    x0 = None
    ps = []
    pps = []
    for i in xrange(len(lPts)):
        l = lPts[i]
        r = rPts[i]
        p = pylab.array(sCam.get_3d_position(l,r))
        ps.append(p)
        pp = pylab.array((divmod(i,7)[1] + gridX.value, -divmod(i,7)[0] + gridY.value, gridZ.value))
        pps.append(pp)
    #print max(errs)
    ps = pylab.array(ps)
    pps = pylab.array(pps)
    pc = ps.mean(0)
    ppc = pps.mean(0)
    print pc, ppc

def calibrate():
    global sCam
    print "# Calibrating...",
    poses = [ [[3., 1.5, 0.], [0., 0., 0.]], # x y z ax ay az
                [[3.,-1.5, 0.], [0., 0., 0.]],
                [[-3.,-1.5, 0.], [0., 0., 0.]],
                [[-3., 1.5, 0.], [0., 0., 0.]],
                [[4., 0., 0.], [0., -60., 0.]],
                [[4., 0., 0.], [0., 60., 0.]],
                [[-4., 0., 0.], [0., -60., 0.]],
                [[-4., 0., 0.], [0., 60., 0.]],
                [[0., 3., 0.], [60., 0., 0.]],
                [[0., 3., 0.], [-60., 0., 0.]],
                [[0., -3., 0.], [-60., 0., 0.]],
                [[0., -3., 0.], [60., 0., 0.]],
                [[0., 0., 10.], [0., 0., 0.]],
                [[0., 0., -10.], [0., 0., 0.]],
                [[0., 0.,  10.], [60., 0., 0.]],
                [[0., 0.,  10.], [-60., 0., 0.]],
                [[0., 0.,  -10.], [60., 0., 0.]],
                [[0., 0.,  -10.], [-60., 0., 0.]],
                [[0., 0.,  10.], [0., 60., 0.]],
                [[0., 0.,  10.], [0., -60., 0.]],
                [[0., 0.,  -10.], [0., 60., 0.]],
                [[0., 0.,  -10.], [0., -60., 0.]],
                [[0., 0., 5.], [0., 0., 0.]],
                [[0., 0., -5.], [0., 0., 0.]],
                [[0., 0.,  5.], [60., 0., 0.]],
                [[0., 0.,  5.], [-60., 0., 0.]],
                [[0., 0.,  -5.], [60., 0., 0.]],
                [[0., 0.,  -5.], [-60., 0., 0.]],
                [[0., 0.,  5.], [0., 60., 0.]],
                [[0., 0.,  5.], [0., -60., 0.]],
                [[0., 0.,  -5.], [0., 60., 0.]],
                [[0., 0.,  -5.], [0., -60., 0.]]]
    nPoses = 22
    print "(%i)" % nPoses,#len(poses),
    # capture calibration images
    for pose in poses[:nPoses]:
        gridX.value, gridY.value, gridZ.value = pose[0]
        gridAX.value, gridAY.value, gridAZ.value = pose[1]
        capture_calibration_image()
        print len(sCam.leftCamera.calibrationImages),
    
    errs = sCam.calibrate((8,6),1.)
    print "calibrated"
    
    # return grid to center
    gridX.value, gridY.value, gridZ.value = [0., 0., 0.]
    gridAX.value, gridAY.value, gridAZ.value = [0., 0., 0.]
    
    # save calibration
    if not os.path.exists('calibrations'): os.makedirs('calibrations')
    sCam.save_calibrations('calibrations/')

def locate():
    global sCam
    
    # # setup localization
    # gridX.value, gridY.value, gridZ.value = [0., 0., 0.]
    # gridAX.value, gridAY.value, gridAZ.value = [0., 0., 0.]
    
    # capture localization images
    x, y, w, h = glGetIntegerv(GL_VIEWPORT)
    # move camera 0
    cameraX.value = -camX.value
    cameraY.value = camY.value
    cameraZ.value = camZ.value
    b = capture_scene()
    sCam.leftCamera.set_string_buffer(b, (h, w, 3), pylab.uint8)
    
    # move camera 1
    cameraX.value = camX.value
    cameraY.value = camY.value
    cameraZ.value = camZ.value
    b = capture_scene()
    sCam.rightCamera.set_string_buffer(b, (h, w, 3), pylab.uint8)
    
    ims, s = sCam.capture_localization_images((8,6))
    if s:
        blockSize = 1.
        sCam.locate((8,6), blockSize)
        # calculate distance between cameras
        ps = sCam.get_camera_positions()
        c1 = pylab.array(ps[0])
        c2 = pylab.array(ps[1])
        print "# Distance between cameras: %+.2f (%+.2f)" % ((sum((c1 - c2)**2))**0.5, camX.value*2.)
        # calculate error in localization of corners (distance between corners)
        errs = []
        for i in xrange(len(sCam.leftCamera.localizationCorners)):
            l = sCam.leftCamera.localizationCorners[i]
            r = sCam.rightCamera.localizationCorners[i]
            p = pylab.array(sCam.get_3d_position(l,r))
            pp = pylab.array((divmod(i,7)[1] * blockSize, -divmod(i,7)[0] * blockSize, 0.))
            err = (sum((p - pp)**2))**0.5
            errs.append(err)
        print "# Max Error: %+.2f" % max(errs)
    if not os.path.exists('calibrations'): os.makedirs('calibrations')
    sCam.save_calibrations('calibrations/')


def take_pictures():
    global sCam
    
    # # setup localization
    # gridX.value, gridY.value, gridZ.value = [0., 0., 0.]
    # gridAX.value, gridAY.value, gridAZ.value = [0., 0., 0.]
    
    # capture localization images
    x, y, w, h = glGetIntegerv(GL_VIEWPORT)
    # move camera 0
    cameraX.value = -camX.value
    cameraY.value = camY.value
    cameraZ.value = camZ.value
    b = capture_scene()
    sCam.leftCamera.set_string_buffer(b, (h, w, 3), pylab.uint8)
    
    # move camera 1
    cameraX.value = camX.value
    cameraY.value = camY.value
    cameraZ.value = camZ.value
    b = capture_scene()
    sCam.rightCamera.set_string_buffer(b, (h, w, 3), pylab.uint8)
    
    #ims, s = sCam.capture_localization_images((8,6))
    ims = sCam.capture()
    for i in xrange(len(ims)):
        cv.SaveImage("%i.png" % i, ims[i])

def capture_calibration_image():
    x, y, w, h = glGetIntegerv(GL_VIEWPORT)
    b = capture_scene()
    global sCam
    sCam.leftCamera.set_string_buffer(b, (h, w, 3), pylab.uint8) # numpy is flipped (hence the h, w; not w,h)
    sCam.rightCamera.set_string_buffer(b, (h, w, 3), pylab.uint8) # numpy is flipped (hence the h, w; not w,h)
    #im = Image.fromstring('RGB', (w,h), b)
    #im.save('foo.png')
    im, s = sCam.capture_calibration_images((8,6))
    # print "Found grid?:", s
    # if len(sCam.calibrationImages) > 0:
    #     err = sCam.calibrate((8,6), 1.)
    #     
    #     # # setup fake projection
    #     # glMatrixMode(GL_PROJECTION)
    #     # glPushMatrix()
    #     # glLoadIdentity()
    #     # x, y, w, h = glGetIntegerv(GL_VIEWPORT)
    #     # gluPerspective(15.1,w/float(h),0.1,1000.0)
    #     # pMatrix = glGetFloatv(GL_PROJECTION_MATRIX)
    #     # glPopMatrix()
    #     # print pMatrix
    #     # print conversions.CVtoNumPy(sCam.camMatrix)
    #     
    #     print "\tMax Calibration Error:", max(flatten_list(err))
    #     im, s = sCam.capture_localization_image((8,6))
    #     print "\tLocalized?:", s
    #     if s:
    #         sCam.locate((8,6), 1.)
    #         cx, cy, cz = sCam.get_position()
    #         print "\t\tLocation: %+.2f %+.2f %+.2f" % (cx, cy, cz)
    #         ex = cx - cameraX.value
    #         ey = cy - cameraY.value
    #         ez = cz - cameraZ.value
    #         print "\t\tLocation Error: %+.2f %+.2f %+.2f" % (ex, ey, ez)
    #         dErr = (ex**2 + ey**2 + ez**2) ** 0.5
    #         print "\t\tDistance Error: %+.2f" % dErr
# ---------------------------

def draw_point():
    glPushMatrix()
    glColor(1.,1.,1.,1.)
    glTranslate(pointX.value, pointY.value, pointZ.value)
    glBegin(GL_POINTS)
    glVertex3f(0.,0.,0.)
    glEnd()
    glPopMatrix()

def draw_grid():
    global texId
    if texId == None:
        texId = loadTexture('grid_9x7.png')
    glEnable(GL_TEXTURE_2D)
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glBindTexture(GL_TEXTURE_2D, texId)
    glPushMatrix()
    glColor(1.,1.,1.,1.)
    glTranslatef(gridX.value, gridY.value, gridZ.value)
    glRotate(gridAX.value, 1, 0, 0)
    glRotate(gridAY.value, 0, 1, 0)
    glRotate(gridAZ.value, 0, 0, 1)
    glBegin(GL_QUADS)
    glTexCoord2f(0.,0.)
    glVertex3f(-5.5,4.5,0.)
    glTexCoord2f(1.,0.)
    glVertex3f(5.5,4.5,0.)
    glTexCoord2f(1.,1.)
    glVertex3f(5.5,-4.5,0.)
    glTexCoord2f(0.,1.)
    glVertex3f(-5.5,-4.5,0.)
    glEnd()
    glBindTexture(GL_TEXTURE_2D, 0)
    glPopMatrix()

def on_reshape(width, height):
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, width, 0, height, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    atb.TwWindowSize(width,height)
    global commands
    for c in commands:
        # print c
        if c == 'c':
            calibrate()
        elif c == 'l':
            locate()
        elif c == 'g':
            find_grid()
        elif c == 'p':
            #find_point()
            take_pictures()
        elif c == 't':
            test_points()
        elif c == 's':
            save_scene()
        elif c in ('q', 'e'):
            quit()
    # if len(commands) > 0:
    #     glutIdleFunc(on_idle)

def save_scene(filename='foo.png'):
    x, y, w, h = glGetIntegerv(GL_VIEWPORT)
    im = Image.fromstring('RGB', (w,h), capture_scene())
    im.save(filename)

def capture_scene():
    render_scene()
    x, y, w, h = glGetIntegerv(GL_VIEWPORT)
    pixelData = glReadPixels(0,0,w,h,GL_RGB,GL_UNSIGNED_BYTE)
    return pixelData
    # #im = Image.new('RGB', (w,h))
    # im = Image.fromstring('RGB', (w,h), pixelData)
    # im.save('foo.png')

def render_scene():
    glClearColor(0.5,0.5,0.5,1.0)
    glClear(GL_COLOR_BUFFER_BIT)# | GL_DEPTH_BUFFER_BIT)
    
    # setup eye view
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    x, y, w, h = glGetIntegerv(GL_VIEWPORT)
    gluPerspective(15.1,w/float(h),0.1,1000.0)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    gluLookAt(cameraX.value, cameraY.value, cameraZ.value, 0,0,0, 0,1,0)
    
    draw_point()
    draw_grid()
    
    # destroy eye view
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

def on_draw():
    render_scene()
    atb.TwDraw()
    # global commands
    # if len(commands) > 0:
    #     glutIdleFunc(on_idle)
    glutSwapBuffers()

def on_motion(x,y):
    atb.TwEventMouseMotionGLUT(x,y)
    bar.update()
    glutPostRedisplay()

def on_mouse(button, state, x, y):
    atb.TwEventMouseButtonGLUT(button,state,x,y)
    glutPostRedisplay()

def on_keyboard(code, x, y):
    atb.TwEventKeyboardGLUT(code,x,y)
    glutPostRedisplay()

def on_special(code, x, y):
    atb.TwEventSpecialGLUT(code,x,y)
    glutPostRedisplay()

# def on_idle():
#     x, y, w, h = glGetIntegerv(GL_VIEWPORT)
#     if w < 2:
#         print 'idling'
#         return # window is not yet ready
#     #print x, y, w, h
#     global commands
#     if len(commands) == 0:
#         glutIdleFunc(None)
#     else:
#         c = commands.pop(0)
#         print c
#         if c == 'c':
#             calibrate()
#         elif c == 'l':
#             locate()
#         elif c == 'g':
#             find_grid()
#         elif c == 'p':
#             find_point()
#         elif c == 't':
#             test_points()
#         elif c == 's':
#             save_scene()
#         elif c in ('q', 'e'):
#             quit()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        commands = list(sys.argv[1])
    #global sCam
    #sCam = stringcamera.StringCamera(0)
    sCam = stereocamera.StereoCamera(0,1, stringcamera.StringCamera)
    
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    # actual camera dims 1392 x 1040
    glutInitWindowSize(800,600)
    glutCreateWindow(sys.argv[0])
    atb.init()
    
    gridX = c_float(0.)
    gridY = c_float(0.)
    gridZ = c_float(0.)
    gridAX = c_float(0.)
    gridAY = c_float(0.)
    gridAZ = c_float(0.)
    #gridRotation = (c_float*4)(1., 1., 0., 0.) # quaternion
    
    cameraX = c_float(0.)
    cameraY = c_float(0.)
    cameraZ = c_float(40.)
    #cameraRotation = (c_float*4)(1., 1., 0., 0.) # quaternion
    
    camX = c_float(8.)
    camY = c_float(4.)
    camZ = c_float(40.)
    
    pointX = c_float(0.)
    pointY = c_float(0.)
    pointZ = c_float(0.)
    
    bar = atb.Bar(name="Controls", label='Controls', help="Scene atb",
                  position=(10, 10), size=(200, 460))
    
    bar.add_var("Grid/gX", gridX, step=0.5)
    bar.add_var("Grid/gY", gridY, step=0.5)
    bar.add_var("Grid/gZ", gridZ, step=0.5)
    #bar.add_var("Grid/gRotation", gridRotation, vtype=atb.TW_TYPE_QUAT4F)
    bar.add_var("Grid/gAX", gridAX, step=0.5)
    bar.add_var("Grid/gAY", gridAY, step=0.5)
    bar.add_var("Grid/gAZ", gridAZ, step=0.5)
    
    bar.add_var("Point/pX", pointX, step=0.5)
    bar.add_var("Point/pY", pointY, step=0.5)
    bar.add_var("Point/pZ", pointZ, step=0.5)
    
    bar.add_var("Camera/cX", cameraX, step=0.5)
    bar.add_var("Camera/cY", cameraY, step=0.5)
    bar.add_var("Camera/cZ", cameraZ, step=0.5)
    bar.add_var("Camera/camX", camX, step=0.5)
    bar.add_var("Camera/camY", camY, step=0.5)
    bar.add_var("Camera/camZ", camZ, step=0.5)
    #bar.add_var("Camera/cRotation", cameraRotation, vtype=atb.TW_TYPE_QUAT4F)
    
    # bar.add_var("Light/State", lighted)
    # bar.add_var("Light/Position", position, vtype=atb.TW_TYPE_QUAT4F)
    # bar.add_var("Light/Diffuse", diffuse)
    # bar.add_var("Light/Ambient", ambient)
    # bar.add_var("Light/Specular", specular)
    
    # Shape = atb.enum("Shape", {'Cube':0, 'Torus':1, 'Teapot':2})
    # bar.add_var("Object/Shape", shape, vtype=Shape)
    # bar.add_var("Object/Fill", fill)
    # bar.add_var("Object/Color", color)
    bar.add_separator("")
    bar.add_button("Calibrate", calibrate, key='c', help='calibrate the cameras')
    bar.add_button("Locate", locate, key='l', help='locate the cameras')
    bar.add_button("Find Grid", find_grid, key='g', help='find grid in image')
    #bar.add_button("Find Point", find_point, key='p', help='find point in image')
    bar.add_button("Test Points", test_points, key='t', help='test finding lots of points')
    #bar.add_button("GrabCalImg", capture_calibration_image, key='g', help='grab a calibration image')
    bar.add_button("SaveScene", save_scene, key="s", help="Save view of scene")
    bar.add_button("TakePictures", take_pictures, key='p', help='capture pictures from cameras')
    bar.add_separator("")
    bar.add_button("Quit", quit, key="ESCAPE", help="Quit application")
    
    #glEnable (GL_BLEND)
    #glEnable (GL_COLOR_MATERIAL)
    #glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    #glBlendFunc (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    glutMouseFunc(on_mouse)
    glutReshapeFunc(on_reshape)
    glutDisplayFunc(on_draw)
    glutPassiveMotionFunc(on_motion)
    glutMotionFunc(on_motion)
    glutKeyboardFunc(on_keyboard)
    glutSpecialFunc(on_special)
    #glutIdleFunc(on_idle)
    glutMainLoop()
