#!/usr/bin/env python

import os, sys

import numpy
import pylab

import filecamera
import camera
import conversions

global dc1394Available
dc1394Available = False
try:
    import dc1394camera
    dc1394Available = True
except:
    dc1394Available = False

def test_stereo_localization(camIDs, gridSize, gridBlockSize, calibrationDirectory='calibrations', frameDirectory=None):
    print "Create",
    if frameDirectory != None:
        print "FileCameraPair"
        cp = FileCameraPair(camIDs, frameDirectory)
        for c in cp.cameras:
            c.frameIndex = 3
    else:
        print "CameraPair"
        cp = CameraPair(camIDs)
    print "Connect"
    cp.connect()
    print "Capture"
    im1, im2 = cp.capture()
    print "Loading calibration",
    cp.load_calibrations(calibrationDirectory)
    print cp.cameras[0].calibrated, cp.cameras[1].calibrated

    print "Capture localization image"
    pylab.ion()
    success = False
    while not success:
        ims, success = cp.capture_localization_images(gridSize)
        pylab.figure()
        pylab.subplot(121)
        pylab.imshow(numpy.array(conversions.CVtoNumPy(ims[0][0])))
        pylab.gray()
        pylab.subplot(122)
        pylab.imshow(numpy.array(conversions.CVtoNumPy(ims[1][0])))
        pylab.gray()
        if not success:
            print "Both cameras did not see the grid"
            if poll_user("Try Again?", "y", "n", 0) == 1:
                print "Quitting localization"
                sys.exit(1)

    print "Locate"
    cp.locate(gridSize, gridBlockSize)

    if not all([c.located for c in cp.cameras]):
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

def test_camera_pair(camIDs, gridSize, gridBlockSize, calibrationDirectory='calibrations', frameDirectory=None):
    print "Create"
    if frameDirectory != None:
        print "FileCameraPair"
        cp = FileCameraPair(camIDs, frameDirectory)
    else:
        print "CameraPair"
        cp = CameraPair(camIDs)

    print "Connect"
    cp.connect()

    print "Capture"
    im1, im2 = cp.capture()

    print "Loading calibration",
    cp.load_calibrations(calibrationDirectory)
    print cp.cameras[0].calibrated, cp.cameras[1].calibrated

    print "Capture localization image"
    success = False
    while not success:
        ims, success = cp.capture_localization_images(gridSize)
        if not success:
            print "Both cameras did not see the grid"
            if poll_user("Try Again?", "y", "n", 0) == 1:
                print "Quitting localization"
                sys.exit(1)

    print "Locate"
    cp.locate(gridSize, gridBlockSize)

    #print ims[0][0].width, ims[0][0].height #1280 x 960

    if not all([c.located for c in cp.cameras]):
        print "Something wasn't located correctly"
        sys.exit(1)

    from mpl_toolkits.mplot3d import Axes3D

    f = pylab.figure(1)
    a = Axes3D(f)
    cpos = []
    for c in cp.cameras:
        p = c.get_position()
        cpos.append(p)
        # a.scatter([p[0]],[p[1]],[p[2]],c='b')
    lcorners = cp.cameras[0].localizationCorners
    rcorners = cp.cameras[1].localizationCorners
    pts = []
    for (l,r) in zip(lcorners,rcorners):
        p = cp.get_3d_position((l,r))
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
    i1 = pylab.array(conversions.CVtoNumPy(ims[0][0])/255.)
    pylab.imshow(i1)
    pylab.gray()
    pylab.subplot(122)
    i2 = pylab.array(conversions.CVtoNumPy(ims[1][0])/255.)
    pylab.imshow(i2)
    pylab.gray()
    pylab.show()

    #print "Save calibrations/localization"
    #cp.save_calibrations(calibrationDirectory)

def test_single_camera(camID, gridSize, gridBlockSize, calibrationDirectory='calibrations'):
    print "Create"
    cam = CalibratedCamera(camID)
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
    while len(cam.calibrationImages) < 7:
        if poll_user("Capture next image?", "y", "n", 0):
            print "Quitting calibration"
            sys.exit(1)
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
        raise IOError, "User provided unknown response: %s" % response

if __name__ == "__main__":
    # gridSize = (8,5)
    # gridBlockSize = 2.822
    # gridSize = (8,5)
    # gridBlockSize = 3.5277777777
    # gridSize = (8,5)
    # gridBlockSize = 1.27
    # gridSize = (8,6)
    # gridBlockSize = 1.
    gridSize = (8,6)
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
    if test[0] == 'l':
        test_single_camera(49712223528793951, gridSize, gridBlockSize) # left
    elif test[0] == 'r':
        test_single_camera(49712223528793946, gridSize, gridBlockSize) # right
    elif test[0] == 'p':
        test_camera_pair((49712223528793951, 49712223528793946), gridSize, gridBlockSize, frameDirectory=frameDir)
    elif test[0] == 's':
        test_stereo_localization((49712223528793951, 49712223528793946), gridSize, gridBlockSize, frameDirectory=frameDir)
    elif test[0] == 'f':
        if test[1] == 'l':
            test_file_camera(49712223528793951, frameDir, gridSize, gridBlockSize)
        elif test[1] == 'r':
            test_file_camera(49712223528793946, frameDir, gridSize, gridBlockSize)
        else:
            print "unknown camera"
    else:
        test_camera_pair((49712223528793951, 49712223528793946), gridSize, gridBlockSize)