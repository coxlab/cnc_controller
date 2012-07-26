#!/usr/bin/env python

from numpy import *
from numpy.linalg import inv

import vector

import cfg

import points

class FrameManager:
    def __init__(self, frameNames):
        self.frameNames = frameNames
        self.frameStack = [] # fill this with None at first
        for i in xrange(len(self.frameNames)-1):
            self.frameStack.append(None)
        self.points = {}
        for frame in frameNames:
            self.points[frame] = []
    
    def add_transformation_matrix(self, fromFrame, toFrame, tMatrix):
        fromIndex = self.frameNames.index(fromFrame)
        toIndex = self.frameNames.index(toFrame)
        if toIndex - fromIndex != 1:
            print self.frameStack
            print self.frameNames
            print self.frameNames.index(fromFrame), self.frameNames.index(toFrame)
            raise ValueError('Invalid from and to frames(%s, %s)' % (fromFrame, toFrame))
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
                return self._test_route_with_indices(fromIndex+1, toIndex)
            else:
                return False
        else:
            if self.frameStack[toIndex] != None:
                return self._test_route_with_indices(toIndex+1, fromIndex)
            else:
                return False
    
    def get_transformation_matrix(self, fromFrame, toFrame):
        """If no route is found between the two, an exception will be raised"""
        fromIndex = self.frameNames.index(fromFrame)
        toIndex = self.frameNames.index(toFrame)
        #return get_transformation_matrix(self.frameStack, fromIndex, toIndex)
        return self._get_transformation_matrix_with_indices(fromIndex, toIndex)
    
    def transform_point(self, point, fromFrame, toFrame):
        return array(array(point) * self.get_transformation_matrix(fromFrame, toFrame))
    
    def _get_transformation_matrix_with_indices(self, fromIndex, toIndex):
        direction = toIndex - fromIndex
        if direction == 0:
            return matrix(identity(4, dtype=float64))
        elif direction == 1:
            return self.frameStack[fromIndex]
        elif direction == -1:
            return inv(self.frameStack[toIndex])
        elif direction > 1:
            return self.frameStack[fromIndex] * self._get_transformation_matrix_with_indices(fromIndex+1, toIndex)
        else:
            return inv(self.frameStack[fromIndex-1]) * self._get_transformation_matrix_with_indices(fromIndex-1, toIndex)
    
    # ------------------------------------
    # --------- Point management ---------
    # ------------------------------------
    
    def add_point(self, frame, point=None, **kwargs):
        if 'point' is not None:
            # add this point to the
            self.points[frame].append(point)
        elif 'z' in kwargs: # this is a 3d point
            if 'left' in kwargs and 'right' in kwargs:
                # this is a point pair
                self.points[frame].append(points.PointPair(**kwargs))
            else:
                self.points[frame].append(points.Point3D(**kwargs))
        else: # 2d point
            self.points[frame].append(points.Point2D(**kwargs))
    
    def try_to_connect_frames(self,fromFrame,toFrame,method=''):
        if self.test_route(fromFrame, toFrame): return True # frames are already connected
        
        if method in ['','rigid']:
            if len(self.points[fromFrame]) < 3 or len(self.points[toFrame]) < 3:
                return False # not enough points
            fromPts = ones((3,4))
            toPts = ones((3,4))
            for i in xrange(3):
                fromPts[i,0] = self.points[fromFrame][i].x
                fromPts[i,1] = self.points[fromFrame][i].y
                fromPts[i,2] = self.points[fromFrame][i].z
                toPts[i,0] = self.points[toFrame][i].x
                toPts[i,1] = self.points[toFrame][i].y
                toPts[i,2] = self.points[toFrame][i].z
            M = vector.fit_rigid_transform(fromPts, toPts)
            self.add_transformation_matrix(fromFrame,toFrame,M)
            return True
        else:
            raise Exception, "Unknown fit method(%s)" % method


# ------------------------------------
# ----------- Unit Tests -------------
# ------------------------------------

def test_frame_manager():
    fm = FrameManager(['skull','tc','camera','cnc'])
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
    test_routes(); print
    
    tR = 10.
    rR = 6.28
    randomTransforms = True
    if randomTransforms:
        m = vector.transform_to_matrix(tR*(random.rand()-0.5), tR*(random.rand()-0.5), tR*(random.rand()-0.5),
                                    rR*(random.rand()-0.5), rR*(random.rand()-0.5), rR*(random.rand()-0.5))
    else:
        m = vector.transform_to_matrix(tR, tR, tR, rR, rR, rR)
    fm.add_transformation_matrix('skull','tc',m)
    test_routes(); print
    
    if randomTransforms:
        m = vector.transform_to_matrix(tR*(random.rand()-0.5), tR*(random.rand()-0.5), tR*(random.rand()-0.5),
                                    rR*(random.rand()-0.5), rR*(random.rand()-0.5), rR*(random.rand()-0.5))
    else:
        m = vector.transform_to_matrix(tR, tR, tR, rR, rR, rR)
    fm.add_transformation_matrix('tc','camera',m)
    test_routes(); print
    
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

def test_frame_mapping():
    fm = FrameManager(['o','t'])
    
    # make random transformation matrix
    T = vector.transform_to_matrix(10*(random.rand()-0.5),10*(random.rand()-0.5),10*(random.rand()-0.5),
                                    10*(random.rand()-0.5),10*(random.rand()-0.5),10*(random.rand()-0.5))
    
    # make original points
    oPts = []
    oPts.append(points.Point3D(1,0,0))
    oPts.append(points.Point3D(0,1,0))
    oPts.append(points.Point3D(0,0,1))
    
    # transform points to random frame
    oPtsM = ones((3,4))
    for i in xrange(3):
        oPtsM[i,0] = oPts[i].x
        oPtsM[i,1] = oPts[i].y
        oPtsM[i,2] = oPts[i].z
    
    tPtsM = vector.apply_matrix_to_points(T, oPtsM)
    tPts = []
    for i in xrange(3):
        tPts.append(points.Point3D(tPtsM[i,0],tPtsM[i,1],tPtsM[i,2]))
    
    # add points to frame manager
    for o in oPts:
        fm.add_point('o',o)
    for t in tPts:
        fm.add_point('t',t)
    
    # try to fit points
    if fm.try_to_connect_frames('o','t'):
        print "Frames fit!"
    else:
        raise Exception, "These frames should have fit"
    
    # test fit
    C = fm.get_transformation_matrix('o','t')
    print T,C
    sse = sum((T - C)**2)
    print "SSError in fit:", sse
    if sse > 0.001: raise Exception, "Fitting error too high"
    

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
    test_frame_mapping()