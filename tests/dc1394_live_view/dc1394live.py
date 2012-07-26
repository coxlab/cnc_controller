#!/usr/bin/env python

import sys, time

from OpenGL.GLUT import *
from OpenGL.GL import *
from pylab import *
import pydc1394

from bjg import glZoomView

global dc13994
dc1394 = pydc1394.DC1394Library()

def close_dc1394():
    global dc1394
    dc1394.close()
    del dc1394

def configure_cam(cam):
    cam.trigger.on = False
    cam.exposure.on = False
    cam.shutter.mode = 'manual'
    cam.shutter.val = 100.
    # cam.framerate.mode = 'manual'
    # cam.framerate.val = 0.5
    # cam.exposure.mode = 'manual'
    # cam.exposure.val = 1.
    # cam.shutter.mode = 'manual'
    # cam.shutter.val = 1000
    cam.mode.roi = ((1392, 1040), (0, 0), 'Y8', -3)

# construct camera
cams = dc1394.enumerate_cameras()
camID = cams[0]['guid']
global cam
cam = pydc1394.Camera(dc1394, camID)
cam.mode = [m for m in cam.modes if m.name == 'FORMAT7_0'][0] # select from available modes
#cam.mode.color_coding = 'Y8'
cam.mode.roi = ((1392, 1040), (0, 0), 'Y8', -3) # i don't think I can set packet size (-3) during capture

# notes for iidc spec:
# - exposure (does nothing? other than auto/manual)
# - gamma
# - shutter (determines how long the iris is open)
# - gain
# - trigger (for external triggering, i think 3 is internal, requires 1 param that sets multiple cycle period (>=1))
# - trigger_delay (for external triggering)
# - framerate (not applicable for FORMAT7 turn 'off'?)
# brightness, exposure, gamma, shutter, gain, trigger, trigger_delay, framerate

# order of operations
#   1. set mode
#   2. set framerate (? for FORMAT7?)
#   3. set shutter

for feature in cam.features:
    f = cam.__getattribute__(feature)
    print "%s:" % feature
    print " Value:", f.val
    print " On?  :", f.on
    print " OnOff:", f.can_be_disabled
    print " Mode :", f.mode
    print " Modes:", f.pos_modes
    if feature != 'trigger':
        print " Range:", f.range
    print

configure_cam(cam)
cam.start(interactive=True)
# #configure_cam(cam)
# #i = cam.current_image.reshape((1040,1392)) # blocking
# i = cam.current_image
# if i.dtype != 'uint8':
#     i = (i * 2.**-8.).astype('uint8') # ways to speed this up?

# construct zoom view
glutInit(sys.argv)
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
glutInitWindowSize(696,520)
glutCreateWindow('dc1394live')
glClearColor(0., 0., 0., 1.)
global view
view = glZoomView.ZoomView()
view.imageSize = (1392, 1040)
view.scale = .5

# glut callbacks
def display():
    global view
    #glClear(GL_COLOR_BUFFER_BIT)
    view.draw()
    glutSwapBuffers()
glutDisplayFunc(display)

global frameID
frameID = 0

def idle():
    global cam, frameID, view
    print "grabbing image",
    s = time.time()
    #i = cam.current_image.reshape((1040,1392)) # blocking
    cam._new_image.acquire()
    #cam._new_image.wait()
    i = cam._current_img
    if i == None:
        cam._new_image.release()
        time.sleep(0.01)
        return
    print i._id,
    if i._id == frameID:
        cam._new_image.release()
        time.sleep(0.01)
        return
    frameID = i._id
    print time.time() - s
    
    # if i.dtype != 'uint8':
    #     print "converting and loading",
    #     s = time.time()
    #     view.load_texture_from_string((i * 2.**-8.).astype('uint8').tostring())
    #     print time.time() - s
    # else:
    
    print "loading into opengl",
    s = time.time()
    view.load_texture_from_string(i.tostring())
    print time.time() - s
    
    cam._new_image.release()
    
    glutPostRedisplay()
glutIdleFunc(idle)

def process_normal_keys(key, x, y):
    global cam
    if key == 's':
        glutIdleFunc(None)
        glutPostRedisplay()
    elif key == 'S':
        glutIdleFunc(idle)
    elif key == 'i':
        print "saving image",
        s = time.time()
        cam._new_image.acquire()
        imsave('/Users/graham/Desktop/foo.png', cam.current_image, cmap=cm.gray)
        cam._new_image.release()
        print time.time() - s
    elif key in ('q','Q'):
        cam.stop()
        del cam
        close_dc1394()
        sys.exit(0)
    view.process_normal_keys(key, x, y)
glutKeyboardFunc(process_normal_keys)

def process_active_mouse_motion(x, y):
    view.process_active_mouse_motion(x,y)
    glutPostRedisplay()
glutMotionFunc(process_active_mouse_motion)

def process_mouse_entry(state):
    view.process_mouse_entry(state)
    #glutPostRedisplay()
glutEntryFunc(process_mouse_entry)

def process_mouse(button, state, x, y):
    view.process_mouse(button, state, x, y)
    glutPostRedisplay()
glutMouseFunc(process_mouse)

shutterValues = arange(cam.shutter.range[0], 2000, 100)#cam.shutter.range[1], 100)
def process_menu(value):
    if value == -1:
        return value
    global cam
    cam.shutter.val = shutterValues[value]
    cam.mode.roi = ((1392, 1040), (0, 0), 'Y8', -3)
    return value
glutCreateMenu(process_menu)
glutAddMenuEntry("-- Exposure Settings --", -1)
for i in xrange(len(shutterValues)):
    glutAddMenuEntry("%.3f" % shutterValues[i], i)
glutAttachMenu(GLUT_RIGHT_BUTTON)


glutMainLoop()