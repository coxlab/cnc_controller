#!/usr/bin/env python

import os, sys

import numpy
import pylab

import filecamera
import camera
import conversions
import stereocamera

global dc1394Available
dc1394Available = False
try:
    import dc1394camera
    dc1394Available = True
except:
    dc1394Available = False

def test_stereo_localization_repeatability(camIDs, gridSize, gridBlockSize, calibrationDirectory='../calibrations', frameDirectory=None):
    print "Create",
    if frameDirectory != None:
        print "FileCameraPair"
        cp = FileCameraPair(camIDs[0], camIDs[1], frameDirectory)
    else:
        print "CameraPair"
        cp = stereocamera.StereoCamera(camIDs[0], camIDs[1])
    print "Connect"
    #cp.connect()
    print "Capture"
    im1, im2 = cp.capture()
    print "Loading calibration",
    cp.load_calibrations(calibrationDirectory)
    #print cp.cameras[0].calibrated, cp.cameras[1].calibrated

    print "Capture localization image"
    pylab.ion()
    success = False
    while not success:
        lr, rr = cp.capture_localization_images(gridSize)
        pylab.figure()
        pylab.subplot(121)
        pylab.imshow(numpy.array(conversions.CVtoNumPy(lr[0])))
        pylab.gray()
        pylab.subplot(122)
        pylab.imshow(numpy.array(conversions.CVtoNumPy(rr[0])))
        pylab.gray()
        if not (lr[1] and rr[1]):
            print "Both cameras did not see the grid"
            if poll_user("Try Again?", "y", "n", 0) == 1:
                print "Quitting localization"
                sys.exit(1)
        else:
            success = True

    print "Locate"
    cp.locate(gridSize, gridBlockSize)

    if not all(cp.get_located()):
        print "Something wasn't located correctly"
        sys.exit(1)

    keep_capturing = True
    ptColors = ['b','g','r','c','m','y','k'] # no 'w' white
    ptIndex = 0

    from mpl_toolkits.mplot3d import Axes3D

    lax = Axes3D(pylab.figure())
    rax = Axes3D(pylab.figure())
    pylab.ion()
    
    def plot_localization(ax, cam, color):
        # just position for now
        p = cam.get_position()
        ax.scatter([p[0]],[p[1]],[p[2]],c=color)
        # scale axes 1:1
        ox, oy, oz = ax.get_xlim3d().copy(), ax.get_ylim3d().copy(), ax.get_zlim3d().copy()
        rmax = max((abs(pylab.diff(ox)), abs(pylab.diff(oy)), abs(pylab.diff(oz))))
        ox = (ox - pylab.mean(ox))/abs(pylab.diff(ox)) * rmax + pylab.mean(ox)
        oy = (oy - pylab.mean(oy))/abs(pylab.diff(oy)) * rmax + pylab.mean(oy)
        oz = (oz - pylab.mean(oz))/abs(pylab.diff(oz)) * rmax + pylab.mean(oz)
        ax.set_xlim3d([ox[0],ox[1]])
        ax.set_ylim3d([oy[0],oy[1]])
        ax.set_zlim3d([oz[0],oz[1]])
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_zlabel('z')
    
    def print_position_stats(ps):
        print "Position:"
        print "\tMean:", numpy.mean(ps,0)
        print "\tStd :", numpy.std(ps,0)
    
    groupIndex = 0
    
    lPositions = []
    rPositions = []
    while keep_capturing:
        if poll_user("Relocate Cameras?", "y", "n", 0) == 1:
            keep_capturing = False
            continue
        N = raw_input("How many times?")
        try:
            N = int(N)
        except:
            print "I didn't understand", N
            continue
        
        for i in xrange(N):
            lr, rr = cp.capture_localization_images(gridSize)
            if not (lr[1] and rr[1]):
                print "Could not find grid"
                continue
            
            cp.locate(gridSize, gridBlockSize)
            if not all(cp.get_located()):
                print "Localization failed"
                continue
            
            # plot
            plot_localization(lax, cp.leftCamera, ptColors[groupIndex])
            plot_localization(rax, cp.rightCamera, ptColors[groupIndex])
            
            # accumulate
            lPositions.append(cp.leftCamera.get_position())
            rPositions.append(cp.rightCamera.get_position())
            
            # stats
            print "Left:"
            print_position_stats(numpy.array(lPositions))
            print
            print "Right:"
            print_position_stats(numpy.array(rPositions))
        
        groupIndex = (groupIndex + 1) % len(ptColors)
    cp.disconnect()
    del cp

def test_stereo_localization(camIDs, gridSize, gridBlockSize, calibrationDirectory='../calibrations', frameDirectory=None):
    print "Create",
    if frameDirectory != None:
        print "FileCameraPair"
        cp = FileCameraPair(camIDs[0], camIDs[1], frameDirectory)
    else:
        print "CameraPair"
        cp = stereocamera.StereoCamera(camIDs[0], camIDs[1])
    print "Connect"
    #cp.connect()
    print "Capture"
    im1, im2 = cp.capture()
    print "Loading calibration",
    cp.load_calibrations(calibrationDirectory)
    #print cp.cameras[0].calibrated, cp.cameras[1].calibrated

    print "Capture localization image"
    pylab.ion()
    success = False
    while not success:
        lr, rr = cp.capture_localization_images(gridSize)
        pylab.figure()
        pylab.subplot(121)
        pylab.imshow(numpy.array(conversions.CVtoNumPy(lr[0])))
        pylab.gray()
        pylab.subplot(122)
        pylab.imshow(numpy.array(conversions.CVtoNumPy(rr[0])))
        pylab.gray()
        if not (lr[1] and rr[1]):
            print "Both cameras did not see the grid"
            if poll_user("Try Again?", "y", "n", 0) == 1:
                print "Quitting localization"
                sys.exit(1)
        else:
            success = True

    print "Locate"
    cp.locate(gridSize, gridBlockSize)

    if not all(cp.get_located()):
        print "Something wasn't located correctly"
        sys.exit(1)

    keep_capturing = True
    ptColors = ['b','g','r','c','m','y','k'] # no 'w' white
    ptIndex = 0

    from mpl_toolkits.mplot3d import Axes3D

    ax = Axes3D(pylab.figure())
    pylab.ion()

    while keep_capturing:
        if poll_user("Capture and locate grid points?", "y", "n", 0) == 1:
            keep_capturing = False
            continue

        ims, corners, success = cp.locate_grid(gridSize)
        if not success:
            print "Could not find grid"
            continue

        for c in corners:
            ax.scatter([c[0]],[c[1]],[c[2]],c=ptColors[divmod(ptIndex,len(ptColors))[1]])
            # scale axes 1:1
            ox, oy, oz = ax.get_xlim3d().copy(), ax.get_ylim3d().copy(), ax.get_zlim3d().copy()
            rmax = max((abs(pylab.diff(ox)), abs(pylab.diff(oy)), abs(pylab.diff(oz))))
            ox = (ox - pylab.mean(ox))/abs(pylab.diff(ox)) * rmax + pylab.mean(ox)
            oy = (oy - pylab.mean(oy))/abs(pylab.diff(oy)) * rmax + pylab.mean(oy)
            oz = (oz - pylab.mean(oz))/abs(pylab.diff(oz)) * rmax + pylab.mean(oz)
            ax.set_xlim3d([ox[0],ox[1]])
            ax.set_ylim3d([oy[0],oy[1]])
            ax.set_zlim3d([oz[0],oz[1]])
            ax.set_xlabel('x')
            ax.set_ylabel('y')
            ax.set_zlabel('z')
        ptIndex += 1
        pylab.figure()
        pylab.subplot(121)
        pylab.imshow(numpy.array(conversions.CVtoNumPy(ims[0])))
        pylab.gray()
        pylab.subplot(122)
        pylab.imshow(numpy.array(conversions.CVtoNumPy(ims[1])))
        pylab.gray()
    
    cp.disconnect()
    del cp

def test_camera_pair(camIDs, gridSize, gridBlockSize, calibrationDirectory='../calibrations', frameDirectory=None):
    print "Create"
    if frameDirectory != None:
        print "FileCameraPair"
        cp = FileCameraPair(camIDs[0], camIDs[1], frameDirectory)
    else:
        print "CameraPair"
        cp = stereocamera.StereoCamera(camIDs[0], camIDs[1])
        cp.leftCamera.set_shutter(800)
        cp.rightCamera.set_shutter(800)
        #cp = CameraPair(camIDs[0],camIDs[1])

    print "Connect"
    #cp.connect()

    print "Capture"
    im1, im2 = cp.capture()

    print "Loading calibration"
    cp.load_calibrations(calibrationDirectory)
    #print cp.cameras[0].calibrated, cp.cameras[1].calibrated

    print "Capture localization image"
    success = False
    while not success:
        l, r = cp.capture_localization_images(gridSize)
        lim = l[0]
        rim = r[0]
        success = l[1] and r[1]
        print "Captured localization image:", success
        if not success:
            print "Both cameras did not see the grid"
            if poll_user("Try Again?", "y", "n", 0) == 1:
                print "Quitting localization"
                sys.exit(1)

    print "Locate"
    cp.locate(gridSize, gridBlockSize)

    #print ims[0][0].width, ims[0][0].height #1280 x 960

    if not all(cp.get_located()):
        print "Something wasn't located correctly"
        sys.exit(1)

    from mpl_toolkits.mplot3d import Axes3D

    f = pylab.figure(1)
    a = Axes3D(f)
    cpos = []
    #for c in cp.cameras:
    #    p = c.get_position()
    for p in cp.get_camera_positions():
        cpos.append(p)
        # a.scatter([p[0]],[p[1]],[p[2]],c='b')
    lcorners = cp.leftCamera.localizationCorners
    rcorners = cp.rightCamera.localizationCorners
    pts = []
    for (l,r) in zip(lcorners,rcorners):
        p = cp.get_3d_position(l,r)
        pts.append(p)
        a.scatter([p[0]],[p[1]],[p[2]],c='r')

    a.set_xlim3d([-5,20])
    a.set_ylim3d([-5,20])
    a.set_zlim3d([-5,20])

    pylab.savetxt('%s/gridPts' % calibrationDirectory, pylab.array(pts))
    pylab.savetxt('%s/camPos' % calibrationDirectory, pylab.array(cpos))

    measuredDists = pylab.sqrt(pylab.sum(pylab.array(pts)**2,1))
    y, x = divmod(pylab.arange(gridSize[0]*gridSize[1]),gridSize[0])
    actualPos = pylab.transpose(pylab.vstack((x,y))) * gridBlockSize
    actualDists = pylab.sqrt(pylab.sum(actualPos**2,1))
    distErrors = abs(measuredDists - actualDists)

    pylab.figure(2)
    pylab.hist(distErrors)
    print "Max Abs(Error):", distErrors.max()

    def dist_grid(a):
        a = pylab.array(a)
        r = pylab.zeros((len(a),len(a)))
        for i in xrange(len(a)):
            r[i,:] = pylab.sqrt(pylab.sum((a-a[i])**2,1))
        return r

    aGrid = dist_grid(actualPos)
    mGrid = dist_grid(pts)
    eGrid = abs(mGrid-aGrid)
    pylab.figure(3)
    pylab.subplot(221)
    pylab.imshow(mGrid,interpolation='nearest',origin='lower')
    pylab.title('Measured')
    pylab.colorbar()
    pylab.subplot(222)
    pylab.imshow(aGrid,interpolation='nearest',origin='lower')
    pylab.title('Actual')
    pylab.colorbar()
    pylab.subplot(223)
    pylab.imshow(abs(mGrid-aGrid),interpolation='nearest',origin='lower')
    pylab.title('Error')
    pylab.colorbar()
    pylab.subplot(224)
    pylab.imshow(abs(aGrid/mGrid - 1.),interpolation='nearest',origin='lower')
    pylab.title('Ratio')
    pylab.colorbar()

    pylab.figure(4)
    pylab.subplot(121)
    i1 = pylab.array(conversions.CVtoNumPy(lim[0])/255.)
    pylab.imshow(i1)
    pylab.gray()
    pylab.subplot(122)
    i2 = pylab.array(conversions.CVtoNumPy(rim[0])/255.)
    pylab.imshow(i2)
    pylab.gray()
    pylab.show()

    #print "Save calibrations/localization"
    cp.save_calibrations(calibrationDirectory)
    cp.disconnect()
    del cp

def test_single_camera(camID, gridSize, gridBlockSize, calibrationDirectory='../calibrations'):
    if dc1394Available == False:
        print "dc1394 not found"
        sys.exit(1)
    print "Create"
    cam = dc1394camera.DC1394Camera(camID)
    print "Connect"
    cam.connect()
    # test capture
    print "Capture"
    pylab.ion()
    pylab.figure()
    im = cam.capture()
    pylab.imshow(conversions.CVtoNumPy(im))
    pylab.gray()
    print "Calibrate"
    #while len(cam.calibrationImages) < 7:
    while True:
        if poll_user("Capture next image?", "y", "n", 0):
            print "Quitting calibration"
            #sys.exit(1)
            break
        else:
            im, s = cam.capture_calibration_image(gridSize)
            pylab.imshow(conversions.CVtoNumPy(im))
            if not s:
                print "Grid not found"
            else:
                print "Found grid %i" % len(cam.calibrationImages)
    
    cam.calibrate(gridSize, gridBlockSize)
    
    if poll_user("Would you like to locate the camera?", "y", "n", 0) == 0:
        success = False
        while not success:
            im, success = cam.capture_localization_image(gridSize)
            if not success:
                print "Grid not found"
                if poll_user("Try Again?", "y", "n", 0) == 1:
                    print "Quitting localization"
                    sys.exit(1)
        cam.locate(gridSize, gridBlockSize)
    
    print "Save calibration"
    cam.save_calibration(calibrationDirectory)
    cam.disconnect()
    del cam

def test_file_camera(camID, frameDir):
    print "Create"
    c = filecamera.FileCamera(camID)#,frameDirectory)
    fileList = ["%s/%s" % (frameDir, f) for f in os.listdir(frameDir)]
    c.set_file_list(fileList)
    print "Connect"
    c.connect()
    print "Capture"
    im = c.capture()
    print im
    pylab.figure()
    nim = numpy.array(conversions.CVtoNumPy(im))
    print nim
    pylab.imshow(nim)
    pylab.show()

def clean_bus(camIDs, loop=True):
    if dc1394Available == False:
        print "dc1394 not found"
        sys.exit(1)
    if not type(camIDs) in (tuple, list):
        camIDs = [camIDs,]
    for camID in camIDs:
        cam = dc1394camera.DC1394Camera(camID)
        cam.disconnect()
        del cam
    if loop:
        clean_bus(camIDs, False)

def poll_user(question, choice1, choice2, default=0):
    if default:
        print "%s %s/[%s]" % (question, choice1, choice2)
    else:
        print "%s [%s]/%s" % (question, choice1, choice2)
    response = raw_input()
    if response == '':
        return default
    elif response == choice1:
        return 0
    elif response == choice2:
        return 1
    else:
        return default

if __name__ == "__main__":
    # gridSize = (8,5)
    # gridBlockSize = 2.822
    # gridSize = (8,5)
    # gridBlockSize = 3.5277777777
    # gridSize = (8,5)
    # gridBlockSize = 1.27
    # gridSize = (8,6)
    # gridBlockSize = 1.
    # gridSize = (7,6)
    # gridBlockSize = 4.
    gridSize = (47,39)
    gridBlockSize = 1.
    
    #left = 49712223528793951
    #right = 49712223528793946
    
    if len(sys.argv) > 1:
        test = sys.argv[1].lower()
        if len(sys.argv) > 2:
            frameDir = sys.argv[2]
            print "Reading frames from %s" % frameDir
        else:
            frameDir = None
    if test[0] == 'c':
        clean_bus((49712223528793951, 49712223528793946))
    elif test[0] == 'l':
        test_single_camera(49712223528793951, gridSize, gridBlockSize) # left
    elif test[0] == 'r':
        test_single_camera(49712223528793946, gridSize, gridBlockSize) # right
    elif test[0] == 'p':  # use this for calibration (2012-09-17)
        test_camera_pair((49712223528793951, 49712223528793946), gridSize, gridBlockSize, frameDirectory=frameDir)
    elif test[0] == 's':
        if test[1] == 'l':
            test_stereo_localization((49712223528793951, 49712223528793946), gridSize, gridBlockSize, frameDirectory=frameDir)
        elif test[1] == 'r':
            test_stereo_localization_repeatability((49712223528793951, 49712223528793946), gridSize, gridBlockSize, frameDirectory=frameDir)
        else:
            print "unknown stereo test"
    elif test[0] == 'f':
        if test[1] == 'l':
            test_file_camera(49712223528793951, frameDir, gridSize, gridBlockSize)
        elif test[1] == 'r':
            test_file_camera(49712223528793946, frameDir, gridSize, gridBlockSize)
        else:
            print "unknown camera"
    else:
        test_camera_pair((49712223528793951, 49712223528793946), gridSize, gridBlockSize)