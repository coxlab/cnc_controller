#!/usr/bin/env python

from numpy import *
from numpy.linalg import inv

import vector

import cfg

# !!!! 3 points on arc, to define plane of rotation and length of arm

# manage a stack of coordinate frames with transformation matrices
# relating each level in the stack to the next

# manage conversion from cnc(x,y,z,w,b) to skull(dv, ml, ap, angle) via:
#   cnc (x,y,z,w,b)
#   camera (x,y,z, angle)
#   tricorner (x,y,z, angle)
#   skull (x,y,z, angle)

# I need a calibration routine to measure the alignment of rotation (b) stage
# with the cameras
#  so I can
# calculate all shaft locations within the cnc frame (assuming stage aligned)
# and then perform the necessary coordinate transforms
# -= procedure
#  1. measure cam -> tricorner matrix
#  2. measure cnc tip in tricorner frame (point 1, in tc frame)
#  3. move w stage, measure tip (point 2, in tc frame)
#  4. move b stage, measure tip (point 3, in tc frame)
#  5. calculate rigid transform (cnc->tricorner)

# I need to know the geometry of the probe & the arm
# (can I measure this? possibly not)
# w (fine z) alters radius of probe arm rotation

# so I need these functions
#  -update_cnc_frame(x,y,z,w,b) (new axis values)
#       updates internal position & shaft etc.
#  -measure_cnc_to_tc_matrix()
#       accepts:
#           np1, np2, np3 (cnc coords)
#           tp1, tp2, tp3 (tricorner coords, as seen from camera)
#       see procedure above (brief: use w & b to get 3 points,
#           calc rigid transform)
#  -get_position_in_skull
#       returns point at tip and top of shaft
#        (possibly quaternion for rotation)
#  -calculate_camera_to_tc_matrix(cp1,cp2,cp3,tp1,tp2,tp3)
#       accepts points as seen from camera, and known tricorner positions
#       returns transformation matrix (cam-to-tc)

# ====================
#    implementation
# ====================


class FrameManager:
    def __init__(self, frameNames):
        self.frameNames = frameNames
        self.frameStack = []  # fill this with None at first
        for i in xrange(len(self.frameNames) - 1):
            self.frameStack.append(None)
        self.points = []

    def add_transformation_matrix(self, fromFrame, toFrame, tMatrix):
        fromIndex = self.frameNames.index(fromFrame)
        toIndex = self.frameNames.index(toFrame)
        if toIndex - fromIndex != 1:
            print self.frameStack
            print self.frameNames
            print self.frameNames.index(fromFrame), \
                    self.frameNames.index(toFrame)
            raise ValueError('Invalid from and to frames(%s, %s)' \
                    % (fromFrame, toFrame))
        elif toIndex > fromIndex:
            self.frameStack[fromIndex] = tMatrix
        else:
            self.frameStack[toIndex] = inv(tMatrix)
        cfg.framesLog.info('Adding Frame %s to %s' % (fromFrame, toFrame))
        cfg.framesLog.info(str(array(tMatrix)))

    def test_route(self, fromFrame, toFrame):
        fromIndex = self.frameNames.index(fromFrame)
        toIndex = self.frameNames.index(toFrame)
        return self._test_route_with_indices(fromIndex, toIndex)

    def _test_route_with_indices(self, fromIndex, toIndex):
        if fromIndex == toIndex:
            return True
        elif fromIndex < toIndex:
            if self.frameStack[fromIndex] != None:
                return self._test_route_with_indices(fromIndex + 1, toIndex)
            else:
                return False
        else:
            if self.frameStack[toIndex] != None:
                return self._test_route_with_indices(toIndex + 1, fromIndex)
            else:
                return False

    def get_transformation_matrix(self, fromFrame, toFrame):
        """If no route is found between the two, an exception will be raised"""
        fromIndex = self.frameNames.index(fromFrame)
        toIndex = self.frameNames.index(toFrame)
        #return get_transformation_matrix(self.frameStack, fromIndex, toIndex)
        return self._get_transformation_matrix_with_indices(fromIndex, toIndex)

    def transform_point(self, point, fromFrame, toFrame):
        return array(array(point) * self.get_transformation_matrix(\
                fromFrame, toFrame))

    def _get_transformation_matrix_with_indices(self, fromIndex, toIndex):
        direction = toIndex - fromIndex
        if direction == 0:
            return matrix(identity(4, dtype=float64))
        elif direction == 1:
            return self.frameStack[fromIndex]
        elif direction == -1:
            return inv(self.frameStack[toIndex])
        elif direction > 1:
            return self.frameStack[fromIndex] * \
                    self._get_transformation_matrix_with_indices(\
                    fromIndex + 1, toIndex)
        else:
            return inv(self.frameStack[fromIndex - 1]) * \
                    self._get_transformation_matrix_with_indices(\
                    fromIndex - 1, toIndex)

    # ------------------------------------
    # --------- Point management ---------
    # ------------------------------------

    def add_point(self, frame, x, y, z, **kwargs):
        newPoint = {}
        newPoint['frame'] = frame
        newPoint['x'] = x
        newPoint['y'] = y
        newPoint['z'] = z
        for k, v in kwargs.iteritems():
            newPoint[k] = v
        self.points.append(newPoint)

    def get_points_in_frame(self, frame):
        r = []
        for p in self.points:
            if p['frame'] == frame:
                r.append(p)
        return r


def test_frame_manager():
    fm = FrameManager(['skull', 'tc', 'camera', 'cnc'])

    def test_routes():
        print '\t',
        for f in fm.frameNames:
            print '%s\t' % f,
        print
        for f in fm.frameNames:
            print '%s\t' % f,
            for tf in fm.frameNames:
                print '%s\t' % fm.test_route(f, tf),
            print

    print "Testing routes:"
    test_routes()
    print

    tR = 10.
    rR = 6.28
    randomTransforms = True
    if randomTransforms:
        m = vector.transform_to_matrix(tR * (random.rand() - 0.5), tR * \
                (random.rand() - 0.5), tR * (random.rand() - 0.5), rR * \
                (random.rand() - 0.5), rR * (random.rand() - 0.5), rR * \
                (random.rand() - 0.5))
    else:
        m = vector.transform_to_matrix(tR, tR, tR, rR, rR, rR)
    fm.add_transformation_matrix('skull', 'tc', m)
    test_routes()
    print

    if randomTransforms:
        m = vector.transform_to_matrix(tR * (random.rand() - 0.5), \
                tR * (random.rand() - 0.5), tR * (random.rand() - 0.5), \
                rR * (random.rand() - 0.5), rR * (random.rand() - 0.5), \
                rR * (random.rand() - 0.5))
    else:
        m = vector.transform_to_matrix(tR, tR, tR, rR, rR, rR)
    fm.add_transformation_matrix('tc', 'camera', m)
    test_routes()
    print
    
    if randomTransforms:
        m = vector.transform_to_matrix(tR*(random.rand()-0.5), tR*(random.rand()-0.5), tR*(random.rand()-0.5),
                                    rR*(random.rand()-0.5), rR*(random.rand()-0.5), rR*(random.rand()-0.5))
    else:
        m = vector.transform_to_matrix(tR, tR, tR, rR, rR, rR)
    fm.add_transformation_matrix('camera','cnc',m)
    test_routes(); print
    
    print "FrameStack"
    for f in fm.frameStack:
        print f
    print
    
    startingPoint = matrix([ [10*(random.rand()-0.5), 10*(random.rand()-0.5), 10*(random.rand()-0.5), 1.] ])
    points = {}
    points['skull'] = startingPoint
    point = startingPoint
    for i in xrange(len(fm.frameStack)):
        point = point * fm.frameStack[i]
        points[fm.frameNames[i+1]] = point
    
    print "Points"
    for k,v in points.iteritems():
        print k,'\t',v
    print
    
    print "Calculation Error"
    print '\t',
    for f in fm.frameNames:
        print '%s\t' % f,
    print
    
    errMatrix = True
    singleTransforms = False
    
    for s in fm.frameNames:
        if errMatrix: print '%s\t' % s,
        for e in fm.frameNames:
            tPoint = points[e]
            #M = fm.get_transformation_matrix(s,e)
            cPoint = fm.transform_point(points[s],s,e)#points[s] * M
            sse = sum(array(tPoint - cPoint)**2)
            if singleTransforms:
                print '--from %s to %s' % (s, e)
                print 'Matrix:'
                print M
                print 'tPoint:',array(tPoint)
                print 'cPoint:',array(cPoint)
                print 'sse:   ',sse
            if errMatrix: print '%.4f\t' % sse,
        if errMatrix: print
    
    print
    print "Checking: s-e = inv(e-s)"
    print '\t',
    for f in fm.frameNames:
        print '%s\t' % f,
    print
    
    for s in fm.frameNames:
        print '%s\t' % s,
        for e in fm.frameNames:
            #sPoint = points[s]
            #ePoint = points[s] * fm.get_transformation_matrix(s,e)
            #rPoint = points[e] * fm.get_transformation_matrix(e,s)
            #sse = sum(array(ePoint - rPoint)**2)
            sem = fm.get_transformation_matrix(s,e)
            esm = fm.get_transformation_matrix(e,s)
            sse = sum((sem*esm - identity(4))**2)
            print '%.4f\t' % sse,
        print
    
    print
    print "Reverse projections"
    print '\t',
    for f in fm.frameNames:
        print '%s\t' % f,
    print
    
    for s in fm.frameNames:
        print '%s\t' % s,
        for e in fm.frameNames:
            ePoint = fm.transform_point(points[s],s,e)
            rPoint = fm.transform_point(ePoint,e,s)
            # sPoint = points[s]
            # ePoint = points[s] * fm.get_transformation_matrix(s,e)
            # rPoint = points[e] * fm.get_transformation_matrix(e,s)
            sse = sum(array(points[s] - rPoint)**2)
            print '%.4f\t' % sse,
        print

def test_frame_translation():
    testFrameNames = []
    testFrameStack = []
    
    testFrameNames.append('home')
    
    testFrameStack.append(vector.transform_to_matrix(tx=1.))
    testFrameNames.append('x')
    
    testFrameStack.append(vector.transform_to_matrix(ty=1.))
    testFrameNames.append('y')
    
    testFrameStack.append(vector.transform_to_matrix(tz=1.))
    testFrameNames.append('z')
    
    startingPoint = matrix([ [10*(random.rand()-0.5), 10*(random.rand()-0.5), 10*(random.rand()-0.5), 1.] ])
    #print "at home:"
    #print startingPoint
    points = {}
    points['home'] = startingPoint
    point = startingPoint
    for i in xrange(len(testFrameStack)):
        point = point * testFrameStack[i]
        points[testFrameNames[i+1]] = point
        #print "at %s:" % testFrameNames[i+1]
        #print point
    print points
    
    # testing frame translation
    for s in xrange(len(testFrameNames)):
        for e in xrange(len(testFrameNames)-s):
            e += s
            if s - e == 0:
                continue
            # if abs(s-e) > 1:
            #     continue
            print "going from %s to %s:" % (testFrameNames[s], testFrameNames[e])
            A = get_transformation_matrix(testFrameStack, s, e)
            #print A
            endPoint = points[testFrameNames[s]] * A
            print "SSError: ", sum(array(endPoint - points[testFrameNames[e]])**2)
            # TODO print point in fromFrame, calculate toFrame, measure error
            print
            print "going from %s to %s:" % (testFrameNames[e], testFrameNames[s])
            A = get_transformation_matrix(testFrameStack, e, s)
            #print A
            startPoint = points[testFrameNames[e]] * A
            print "SSError: ", sum(array(startPoint - points[testFrameNames[s]])**2)
            # TODO print point in fromFrame, calculate toFrame, measure error

if __name__ == "__main__":
    #test_frame_translation()
    test_frame_manager()
