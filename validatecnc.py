#!/usr/bin/env python

import os, sys, time

from pylab import *
from mpl_toolkits.mplot3d import Axes3D

from electrodeController import cnc, camera
from electrodeController.camera.conversions import CVtoNumPy

leftCamID = 49712223528793951
rightCamID = 49712223528793946
gridSize = (47,39)#(11,9)
markerSize = (11,9) # size of grid used on end of cnc
gridBlockSize = 1.
cncAddress = "169.254.0.9"
cncPort = 8003
cncAxes = {'x': 1, 'y': 2, 'z': 3}
#calibrationDirectory = "/Users/%s/Repositories/coxlab/cncController/electrodeController/calibrations" % os.getlogin()
calibrationDirectory = "validation_calibrations"

# connect to cnc
global linearAxes
linearAxes = cnc.axes.Axes(cncAddress, cncPort, cncAxes)

# connect to cameras
global cams
cams = camera.stereocamera.StereoCamera(leftCamID, rightCamID)
#cams.connect()
cams.load_calibrations(calibrationDirectory)

# plotting
ion()
# 3d
global ax
ax = Axes3D(figure(1))
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')

# image Display
global imageDisplay
imageDisplay = 2
figure(imageDisplay)
subplot(121)
subplot(122)

def backlash():
    global cams, linearAxes
    
    print "Which axis would you like to test?"
    axis = raw_input("x,y,z?>>")
    if not axis in ('x','y','z'):
        print "Invalid axis:", axis
        return True
    
    print "What increment would you like to test?"
    inc = raw_input(">> ")
    try:
        inc = float(inc)
    except:
        print "Invalid increment:", inc
        return True
    
    print "How many steps per movement?"
    NSteps = raw_input(">> ")
    try:
        NSteps = int(NSteps)
    except:
        print "Invalid number of steps:", NSteps
        return True
    
    print "How many movements would you like to make?"
    NMoves = raw_input(">> ")
    try:
        NMoves = int(NMoves)
    except:
        print "Invalid number of movements:", NMoves
        return True
    
    print "Press Enter to begin movement (or q to quit)"
    i = raw_input()
    if i == 'q':
        print "Quitting"
        return True
    
    positions = []
    imgs, pts, success = cams.locate_grid(markerSize)
    prevPoint = zeros(3)
    if success:
        pt = mean(array(pts),0)
        positions.append(pt)
        prevPoint = pt
    else:
        print "Failed to find grid"
    
    for m in xrange(NMoves):
        for s in xrange(NSteps):
            linearAxes.move_relative(inc, axis)
            while ord(linearAxes.get_controller_status()[0]) & 0x07:
                time.sleep(0.1)
            time.sleep(0.5)
            imgs, pts, success = cams.locate_grid(markerSize)
            if success:
                pt = mean(array(pts),0)
                dist = sum((pt - prevPoint)**2.)**.5
                print "Dist: %.2f Inc: %.2f Err: %.2f" % (dist, abs(inc), abs(inc)-dist) 
                positions.append(pt)
                prevPoint = pt
            else:
                print "Failed to find grid"
        inc *= -1.
    
    print "Saving position data"
    savetxt("bl_%s_%i_%i_%.3f" % (axis, NMoves, NSteps, inc), positions)

def minimal_incremental_movement():
    global cams, linearAxes
    
    # print "Capture localization image (using large grid)"
    #     lr, rr = cams.capture_localization_images(gridSize)
    #     if not (lr[1] and rr[1]):
    #         print "Localization failed"
    #         return True
    
    print "Which axis would you like to test?"
    axis = raw_input("x,y,z?>>")
    if not axis in ('x','y','z'):
        print "Invalid axis:", axis
        return True
    
    print "What increment would you like to test?"
    inc = raw_input(">> ")
    try:
        inc = float(inc)
    except:
        print "Invalid increment:", inc
        return True
    
    print "How many movements would you like to make?"
    NSteps = raw_input(">> ")
    try:
        NSteps = int(NSteps)
    except:
        print "Invalid number of movements:", NSteps
        return True
    
    print "Press Enter to begin movement (or q to quit)"
    i = raw_input()
    if i == 'q':
        print "Quitting"
        return True
    
    positions = []
    imgs, pts, success = cams.locate_grid(markerSize)
    prevPoint = zeros(3)
    if success:
        pt = mean(array(pts),0)
        positions.append(pt)
        prevPoint = pt
    else:
        print "Failed to find grid"
    for i in xrange(NSteps):
        linearAxes.move_relative(inc, axis)
        while ord(linearAxes.get_controller_status()[0]) & 0x07:
            time.sleep(0.1)
        time.sleep(0.5)
        imgs, pts, success = cams.locate_grid(markerSize)
        if success:
            pt = mean(array(pts),0)
            dist = sum((pt - prevPoint)**2.)**.5
            print "Dist: %.2f Inc: %.2f Err: %.2f" % (dist, abs(inc), abs(inc)-dist) 
            positions.append(pt)
            prevPoint = pt
        else:
            print "Failed to find grid"
    
    for i in xrange(NSteps):
        linearAxes.move_relative(-inc,axis)
        while ord(linearAxes.get_controller_status()[0]) & 0x07:
            time.sleep(0.1)
        time.sleep(0.5)
        imgs, pts, success = cams.locate_grid(markerSize)
        if success:
            pt = mean(array(pts),0)
            dist = sum((pt - prevPoint)**2.)**.5
            print "Dist: %.2f Inc: %.2f Err: %.2f" % (dist, abs(inc), abs(inc)-dist) 
            positions.append(pt)
            prevPoint = pt
        else:
            print "Failed to find grid"
    
    print "Saving position data"
    savetxt("mim_%s_%i_%.3f" % (axis, NSteps, inc), positions)
    
    return True

def locate_cameras():
    global cams
    # locate cameras
    lr, rr = cams.capture_localization_images(gridSize)
    li = cams.leftCamera.undistort_image(lr[0])
    ri = cams.rightCamera.undistort_image(rr[0])
    #update_image_display(lr[0],rr[0])
    update_image_display(li,ri)
    if lr[1] and rr[1]:
        cams.locate(gridSize, gridBlockSize)
        print "Localization was successful"
    else:
        print "Localization failed"
    return True

def update_image_display(li, ri):
    global imageDisplay
    figure(imageDisplay)
    subplot(121)
    imshow(CVtoNumPy(li))
    gray()
    subplot(122)
    imshow(CVtoNumPy(ri))
    gray()

def add_points(pts):
    global ax
    pts = array(pts)
    ax.scatter(pts[:,0],pts[:,1],pts[:,2])

def find_grid():
    global cams
    imgs, pts, success = cams.locate_grid(gridSize)
    li = cams.leftCamera.undistort_image(imgs[0])
    ri = cams.rightCamera.undistort_image(imgs[1])
    update_image_display(li,ri)
    #update_image_display(*imgs)
    if success:
        add_points(pts)
        print "Grid found!"
    else:
        print "No grid was found"
    return True

global joystickOn
joystickOn = False
def toggle_joystick():    
    global joystickOn
    global linearAxes
    if joystickOn:
        print "Disabling joystick"
        linearAxes.disable_joystick()
        joystickOn = False
    else:
        print "Enabling joystick"
        linearAxes.enable_joystick()
        joystickOn = True
    return True

def save_calibration():
    global cams
    cams.save_calibrations('validation_calibrations')
    return True

def quit_loop():
    return False

# ============ Command - Action Dictionary ===========

actions = {'f': find_grid,
            'j': toggle_joystick,
            'l': locate_cameras,
            'm': minimal_incremental_movement,
            's': save_calibration,
            'q': quit_loop}

# ============ Main loop stuff ===================

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

# locate_cameras()
# if all((cams.get_located())):
#     find_grid()

# enter interaction loop
keepGoing = True
while keepGoing:
    print_menu()
    i = get_input()
    keepGoing = process_input(i)

# disconnect
cams.disconnect()
del cams
del linearAxes
