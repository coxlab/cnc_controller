#!/usr/bin/env python

import os, sys

from pylab import *
from mpl_toolkits.mplot3d import Axes3D

from electrodeController import cnc, camera

leftCamID = 49712223528793951
rightCamID = 49712223528793946
gridSize = (11,9)
gridBlockSize = 1.
cncAddress = "169.254.0.9"
cncPort = 8003
cncAxes = {'x': 1, 'y': 2, 'z': 3}
calibrationDirectory = "/Users/%s/Repositories/coxlab/cncController/electrodeController/calibrations" % os.getlogin()

# connect to cnc
linearAxes = cnc.axes.Axes(cncAddress, cncPort, cncAxes)

# connect to cameras
cams = camera.stereocamera.StereoCamera(leftCamID, rightCamID)
cams.connect()
cams.load_calibration(calibrationDirectory)

# plotting
ion()
# 3d
ax = Axes3D(figure(1))
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')

# image Display
imageDisplay = 2
figure(imageDisplay)
subplot(121)
subplot(122)

def locate_cameras():
    # locate cameras
    lr, rr = cams.capture_localization_images(gridSize)
    if lr[1] and rr[1]:
        print "Localization was successful"
    else:
        print "Localization failed"
    return True

def update_image_display(li, ri):
    figure(imageDisplay)
    subplot(121)
    imshow(li)
    gray()
    subplot(122)
    imshow(ri)
    gray()

def add_points(pts):
    pts = array(pts)
    ax.scatter(pts[:,0],pts[:,1],pts[:,2])

def find_grid():
    li, ri, pts, success = cams.locate_grid(gridSize)
    update_image_display(li, ri)
    if success:
        add_points(pts)
        print "Grid found!"
    else:
        print "No grid was found"
    return True

joystickOn = False
def toggle_joystick():
    if joystickOn:
        print "Enabling joystick"
        cnc.enable_joystick()
        joystickOn = True
    else:
        print "Disabling joystick"
        cnc.disable_joystick()
        joystickOn = False
    return True

def quit_loop():
    return False

actions = {'f': find_grid,
            'j': toggle_joystick,
            'l': locate_cameras,
            'q': quit_loop}

def print_menu():
    print "Please enter a selection (letter):"
    for k, v in actions.iteritems():
        print '\t%s: %s' % (k, v.__name__)
    print "------------"

def get_input():
    try:
        i = raw_input(">>")
    except EOFError as e:
        print "Break detected, quitting:", e
        i = 'q'
    except Exception as e:
        print "Error retrieving input:", e
        i = ''
    return i

def process_input(i):
    if i == None:
        print "Received input of None!"
        return True
    i = i.strip()
    if len(i) == 0:
        print "Empty input received"
        return True
    i = i[0]
    if i in actions.keys():
        return actions[i]()
    else:
        print "Unknown input: %s" % (i)
        return True

# enter interaction loop
keepGoing = True
while keepGoing:
    print_menu()
    i = get_input()
    keepGoing = process_input(i)

# disconnect
cams.disconnect()
linearAxes.disconnect()
del cams
del linearAxes