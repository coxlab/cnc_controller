#!/usr/bin/env python
"""
data to plot:
    xx = number
    ss = string
    
    camera location
        INFO:camera:Cameras Located Successfully
        INFO:camera:\tID\t\tX:\tY\tZ
        INFO:camera:\txx\txx\txx\txx
    
    matrix (find good way to show it)
        
        INFO:frames:Adding Frame ss to ss
    
    frame registration points:
        tcFrame -> camera
        camera -> cnc
        
        INFO:frames:Registering {cameras/cnc} with points in (ss, ss):
        INFO:frames:[[ xx xx xx xx]
            [ xx xx xx xx]
            [ xx xx xx xx]
            [ xx xx xx xx]]
    
    resulting points:
        INFO:root:ML:xx AP:xx DV:xx
        INFO:cnc:X:xx Y:xx Z:xx B:xx W:xx
"""

import os, re, sys

from pylab import *
from mpl_toolkits.mplot3d import Axes3D

from electrodeController import frameManager

def get_camera_locations(logFile):
    """
    camera location
        INFO:camera:Cameras Located Successfully
        INFO:camera:\tID\t\tX:\tY\tZ
        INFO:camera:\txx\txx\txx\txx"""
    logFile.seek(0)
    locations = {}
    
    for l in logFile:
        if re.match(r'INFO:camera:\t[0-9]',l):
            items = l.split()
            locations[items[1]] = (float(items[2]), float(items[3]), float(items[4]))
    
    return locations

def read_array(lines):
    items = []
    for l in lines:
        s = len(l) - l[::-1].find('[') # should have -1 but see later
        e = l.find(']')
        if s < 0 or e < 0 or e <= s:
            raise IOError("read_array cannot process line: %s" % l)
        items.append([float(i) for i in l[s:e].split()]) # don't add 1 because I didn't subtract it earlier
    return array(items)

def get_matrices(logFile):
    """
    matrix (find good way to show it)
        
        INFO:frames:Adding Frame ss to ss"""
    logFile.seek(0)
    matrices = {}
    
    l = logFile.readline()
    while l != '':
        if re.match(r'INFO:frames:Adding Frame', l):
            # get to and from
            fromFrame = l.split()[2]
            toFrame = l.split()[4]
            label = '%s to %s' % (fromFrame, toFrame)
            
            # get matrix
            tMatrix = read_array([logFile.readline() for i in xrange(4)])
            matrices[label] = tMatrix
        l = logFile.readline()
    
    return matrices

def get_frame_registration_points(logFile):
    """
    frame registration points:
        tcFrame -> camera
        camera -> cnc
        
        INFO:frames:Registering {cameras/cnc} with points in (ss, ss):
        INFO:frames:[[ xx xx xx xx]
            [ xx xx xx xx]
            [ xx xx xx xx]
            [ xx xx xx xx]]"""
    logFile.seek(0)
    points = {}
    
    l = logFile.readline()
    while l != '':
        if re.match(r'INFO:frames:Registering', l):
            frameName = l.split()[1]
            
            oPoints = read_array([logFile.readline() for i in xrange(3)])
            tPoints = read_array([logFile.readline() for i in xrange(3)])
            points[frameName] = [oPoints, tPoints]
        l = logFile.readline()
    
    return points

def get_arm_length(logFile):
    """
    resulting armLength:
        INFO:cnc:Found arm length: 71.567896"""
    logFile.seek(0)
    armLength = None
    l = logFile.readline()
    while l != '':
        if re.match(r'INFO:cnc:Found arm length:', l):
            armLength = float(l.split(':')[-1])
        l = logFile.readline()
    return armLength

def get_cnc_positions(logFile):
    """
    resulting points:
        INFO:root:ML:xx AP:xx DV:xx
        INFO:cnc:X:xx Y:xx Z:xx B:xx W:xx"""
    logFile.seek(0)
    positions = []
    l = logFile.readline()
    while l != '':
        if re.match(r'INFO:cnc:X:', l):
            items = l.split()
            x = float(items[0].split(':')[-1])
            y = float(items[1].split(':')[-1])
            z = float(items[2].split(':')[-1])
            b = float(items[2].split(':')[-1])
            w = float(items[2].split(':')[-1])
            positions.append([x,y,z,b,w])
        l = logFile.readline()
    return positions

def get_skull_positions(logFile):
    """
    resulting points:
        INFO:root:ML:xx AP:xx DV:xx
        INFO:cnc:X:xx Y:xx Z:xx B:xx W:xx"""
    logFile.seek(0)
    positions = []
    l = logFile.readline()
    while l != '':
        if re.match(r'INFO:root:ML:', l):
            items = l.split()
            ml = float(items[0].split(':')[-1])
            ap = float(items[1].split(':')[-1])
            dv = float(items[2].split(':')[-1])
            positions.append([ml,ap,dv,1.0])
        l = logFile.readline()
    return array(positions)

def parse_log_dir(logDir):
    pass

if __name__ == '__main__':
    # TODO fetch this from command line
    logDir = sys.argv[1]
    
    # open the main log file (only once)
    f = open('%s/root.log' % logDir, 'r')
    
    colors = ['b', 'r', 'g', 'y', 'k', 'm']
    
    # get the calculated locations of the two cameras
    locations = get_camera_locations(f)
    # ax = Axes3D(figure())
    # #ax.set_label('Camera Locations')
    # for (i,l) in enumerate(locations.values()):
    #     ax.scatter([l[0]],[l[1]],[l[2]],c=colors[i])
    
    
    # get the calculated transformation matrices between frames
    matrices = get_matrices(f)
    # find good way to show matrices
    
    armLength = get_arm_length(f)
    if armLength is not None:
        print "Arm length: %.3f mm" % armLength
    
    # get the registration points used to calculate the transformations
    points = get_frame_registration_points(f)
    # for (l,p) in points.iteritems():
    #     ax = Axes3D(figure())
    #     #ax.set_label(l)
    #     for (i,s) in enumerate(p):
    #         ax.scatter(s[:,0],s[:,1],s[:,2],c=colors[i])
    
    # get tip locaiton in skull frame
    sTipPoints = get_skull_positions(f)
    
    # construct frame manager from data
    fm = frameManager.FrameManager(['skull','tricorner','camera','cnc'])
    for (n,m) in matrices.iteritems():
        fromFrame = n.split()[0]
        toFrame = n.split()[2]
        #if toFrame == 'cnc':
        #    m = inv(m)
        fm.add_transformation_matrix(fromFrame, toFrame, matrix(m))
    
    tcPoints, cTcPoints = points['cameras']
    cTipPoints, tipPoints = points['cnc']
    # tcPoints : tricorner refs : in tricorner frame
    # cTcPoints : tricorner refs : in camera frame
    # cTipPoints : tip locations : in camera frame
    # tipPoints : tip locations in cnc frame
    
    # plot things in camera frame
    ax = Axes3D(figure())
    camLocs = ones((2,4),dtype=float64)
    camLocs[:,:3] = array(locations.values())
    #camLocs[:,:3] = array([locations.values()[0],locations.values()[1]])
    print "Distance between cameras: %.3f mm" % sqrt(sum((camLocs[0] - camLocs[1])**2))
    
    def plot_points_in_frame(plotAxes, points, frameMan, fromFrame, toFrame, **kwargs):
        points = array(frameMan.transform_point(points,fromFrame,toFrame))
        ax.scatter(points[:,0],points[:,1],points[:,2],**kwargs)
    
    plotFrame = 'skull'
    
    plot_points_in_frame(ax, sTipPoints, fm, 'skull', plotFrame, c=colors[0], s=100, marker='d')
    
    plot_points_in_frame(ax, camLocs, fm, 'camera', plotFrame, c=colors[0], s=100, marker='o')
    
    plot_points_in_frame(ax, tcPoints, fm, 'tricorner', plotFrame, c=colors[0], s=100, marker='^')
    plot_points_in_frame(ax, cTcPoints, fm, 'camera', plotFrame, c=colors[1], s=100, marker='^')
    
    plot_points_in_frame(ax, tipPoints, fm, 'cnc', plotFrame, c=colors[0], s=100, marker='s')
    plot_points_in_frame(ax, cTipPoints, fm, 'camera', plotFrame, c=colors[1], s=100, marker='s')
    
    # plot all matrices
    def plot_matrix(m, l1, l2):
        print "Translation:", m[3]
        ax = Axes3D(figure())
        points = array([[0,0,0,1],
                [1,0,0,1],
                [0,1,0,1],
                [0,0,1,1]])
        def plot_pts(ax, pts, l):
            ax.plot([pts[0][0],pts[1][0]],[pts[0][1],pts[1][1]],[pts[0][2],pts[1][2]], c='r')
            ax.plot([pts[0][0],pts[2][0]],[pts[0][1],pts[2][1]],[pts[0][2],pts[2][2]], c='g')
            ax.plot([pts[0][0],pts[3][0]],[pts[0][1],pts[3][1]],[pts[0][2],pts[3][2]], c='b')
            ax.text3D(pts[0][0],pts[0][1],pts[0][2],l)
        plot_pts(ax, points, l1)
        plot_pts(ax, array(points * matrix(m)), l2)
        # scale axes
        # scale axes 1:1
        ox, oy, oz = ax.get_xlim3d().copy(), ax.get_ylim3d().copy(), ax.get_zlim3d().copy()
        rmax = max((abs(diff(ox)), abs(diff(oy)), abs(diff(oz))))
        ox = (ox - mean(ox))/abs(diff(ox)) * rmax + mean(ox)
        oy = (oy - mean(oy))/abs(diff(oy)) * rmax + mean(oy)
        oz = (oz - mean(oz))/abs(diff(oz)) * rmax + mean(oz)
        ax.set_xlim3d([ox[0],ox[1]])
        ax.set_ylim3d([oy[0],oy[1]])
        ax.set_zlim3d([oz[0],oz[1]])
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_zlabel('z')
        
    
    plot_matrix(fm.get_transformation_matrix('skull','tricorner'),'skull','tricorner')
    plot_matrix(fm.get_transformation_matrix('tricorner','camera'),'tricorner','camera')
    plot_matrix(fm.get_transformation_matrix('camera','cnc'),'camera','cnc')
    
    # plot tcPoints as seen from camera
    
    
    # tcToCMatrix = matrices['tricorner to camera']
    #     pTcPoints = array(matrix(cTcPoints) * inv(matrix(tcToCMatrix))) # predict backwards
    #     ax.scatter(tcPoints[:,0],tcPoints[:,1],tcPoints[:,2],c=colors[0],s=100,marker='^')
    #     ax.scatter(cTcPoints[:,0],cTcPoints[:,1],cTcPoints[:,2],c=colors[1],s=100,marker='^')
    #     ax.scatter(pTcPoints[:,0],pTcPoints[:,1],pTcPoints[:,2],c=colors[2],s=100,marker='^')
    
    # # plot cncPoints as seen from camera
    # cToNMatrix = matrices['camera to cnc']
    # pCPoints = array(matrix(cncPoints))
    
    show()