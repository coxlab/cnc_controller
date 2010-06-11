#!/usr/bin/env python

from pylab import *

import vector

# !!!! 3 points on arc, to define plane of rotation and length of arm

# manage a stack of coordinate frames with transformation matrices relating each level in the stack to the next

# manage conversion from cnc(x,y,z,w,b) to skull(dv, ml, ap, angle) via:
#   cnc (x,y,z,w,b)
#   camera (x,y,z, angle)
#   tricorner (x,y,z, angle)
#   skull (x,y,z, angle)

# TODO I need a calibration routine to measure the alignment of rotation (b) stage
# with the cameras
#  so I can
# calculate all shaft locations within the cnc frame (assuming stage aligned) and then
# perform the necessary coordinate transforms
# -= procedure
#  1. measure cam -> tricorner matrix
#  2. measure cnc tip in tricorner frame (point 1, in tc frame)
#  3. move w stage, measure tip (point 2, in tc frame)
#  4. move b stage, measure tip (point 3, in tc frame)
#  5. calculate rigid transform (cnc->tricorner)

# TODO I need to know the geometry of the probe & the arm (can I measure this? possibly not)
# TODO w (fine z) alters radius of probe arm rotation

# so I need these functions
#  -update_cnc_frame(x,y,z,w,b) (new axis values)
#       updates internal position & shaft etc.
#  -measure_cnc_to_tc_matrix()
#       accepts:
#           np1, np2, np3 (cnc coords)
#           tp1, tp2, tp3 (tricorner coords, as seen from camera)
#       see procedure above (brief: use w & b to get 3 points, calc rigid transform)
#  -get_position_in_skull
#       returns point at tip and top of shaft (possibly quaternion for rotation)
#  -calculate_camera_to_tc_matrix(cp1,cp2,cp3,tp1,tp2,tp3)
#       accepts points as seen from camera, and known tricorner positions
#       returns transformation matrix (cam-to-tc)

# ====================
#    implementation
# ====================

# class Transform:
#     def __init__(self, fromFrame, toFrame, tMatrix):
#         self.fromFrame = fromFrame
#         self.toFrame = toFrame
#         self.tMatrix = tMatrix
# 
# class FrameManager:
#     def __init__(self):
#         self.transforms = []
#     
#     def get_transform_matrix(self, fromFrame, toFrame):
#         # check if a single transform works
#         t = self.get_single_transform(fromFrame, toFrame)
#         if t != None:
#             return t.tMatrix.copy()
#         
#         # if not, build the transform
#         t = self.get_transform_from(fromFrame)
#         if t == None:
#             raise Exception('no route found')
#         tMatrix = t.tMatrix.copy()
#         currentFrame = t.toFrame
#         
#         while currentFrame != toFrame:
#             t = self.get_next_transform(t)
#             if t == None:
#                 raise Exception('no route found')
#             tMatrix = t.tMatrix * tMatrix
#             currentFrame = t.toFrame
#         return tMatrix
#     
#     def get_next_transform(self, transform):
#         ret = None
#         for t in self.transforms:
#             if t.fromFrame == transform.toFrame and t.toFrame != transform.fromFrame:
#                 if ret != None:
#                     raise Exception('two possible routes')
#                 else:
#                     ret = t
#         return ret
#     
#     def get_transform_from(self, fromFrame):
#         ret = None
#         for t in self.transforms:
#             if t.fromFrame == fromFrame:
#                 if ret != None:
#                     raise Exception('two possible routes')
#                 else:
#                     ret = t
#         return ret
#     
#     def get_single_transform(self, fromFrame, toFrame):
#         for t in self.transforms:
#             if (t.fromFrame == fromFrame) and (t.toFrame == toFrame):
#                 return t
#         return None
#     
#     def add_transform(self, fromFrame, toFrame, tMatrix, andInverse=True):
#         t = self.get_single_transform(fromFrame, toFrame)
#         if (t != None):
#             # transform already exists, just update it
#             t.tMatrix = tMatrix
#         else:
#             self.transforms.append(Transform(fromFrame,toFrame,tMatrix))
#         
#         if andInverse:
#             self.add_transform(toFrame, fromFrame, inv(tMatrix), andInverse=False)
#     
#     # def get_start_frame(self):
#     #     toFrames = [t.toFrame for t in self.transforms]
#     #     fromFrames = [t.fromFrame for t in self.transforms]
#     #     # fromFrame that is not in toFrames
#     #     startFrame = None
#     #     for f in fromFrames:
#     #         if f in toFrames:
#     #             continue
#     #         else:
#     #             if startFrame != None:
#     #                 # two start frames found!!
#     #                 raise ValueError("Two start frames were found (%s, %s)" % (startFrame, f))
#     #             else:
#     #                 startFrame = f
#     #     if startFrame == None:
#     #         raise ValueError("No start frame was found")
#     #     return startFrame
#     
#     # def build_transforms(self):
#     #     for t in self.transforms:
#     #         print "checking:", t
#     #         # check if reverse exists
#     #         if self.get_single_transform(t.toFrame, t.fromFrame) == None:
#     #             print "\tno reverse found"
#     #             # if not, create it
#     #             self.add_transform(t.toFrame, t.fromFrame, inv(t.tMatrix), rebuild=False)
#     #         # # check if there is a transfrom can be extended
#     #         # # in other words...
#     #         # # check if the toFrame of this transform is the fromFrame of another transform
#     #         # # also, make sure this isn't a loop
#     #         # for t2 in self.transforms:
#     #         #     if t.toFrame == t2.fromFrame and t.fromFrame != t2.toFrame:
#     #         #         print "\textending"
#     #         #         self.add_transform_rebuild_on_new(t.fromFrame, t2.toFrame, t2.tMatrix * t.tMatrix) # and rebuild to get the reverse
#     
#     # def get_transform_from_frame(self, frame):
#     #     for t in self.transforms:
#     #         if t.fromFrame == frame:
#     #             return t
#     #     raise ValueError("No transform found from frame: %s" % frame)
#     
#     # def order_transforms(self):
#     #     fromFrame = self.get_start_frame()
#     #     sortedTransforms = []
#     #     while len(sortedTransforms) < len(self.transforms):
#     #         sortedTransforms.append(self.get_transform_from_frame(fromFrame))
#     #         fromFrame = sortedTransforms[-1].toFrame
#     #     self.transforms = sortedTransforms
#     
#     def print_transforms(self):
#         print "Transforms in:", str(self)
#         for t in self.transforms:
#             print "From: %s To: %s" % (t.fromFrame, t.toFrame)
#             print array(t.tMatrix) # things look better as arrays

class FrameManager:
    def __init__(self, frameNames):
        self.frameNames = frameNames
        self.frameStack = [] # fill this with None at first
        for i in xrange(len(self.frameNames)-1):
            self.frameStack.append(None)
    
    def add_transformation_matrix(self, fromFrame, toFrame, tMatrix):
        fromIndex = self.frameNames.index(fromFrame)
        toIndex = self.frameNames.index(toFrame)
        if toIndex - fromIndex != 1:
            raise ValueError('Invalid from and to frames(%s, %s)' % (fromFrame, toFrame))
        elif toIndex > fromIndex:
            self.frameStack[fromIndex] = tMatrix
        else:
            self.frameStack[toIndex] = inv(tMatrix)
    
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
        return point * self.get_transformation_matrix(fromFrame, toFrame)
    
    def _get_transformation_matrix_with_indices(self, fromIndex, toIndex):
        direction = toIndex - fromIndex
        if direction == 0:
            return matrix(identity(4, dtype=float64))
        elif direction == 1:
            return self.frameStack[fromIndex]
        elif direction == -1:
            return inv(self.frameStack[toIndex])
        elif direction > 1:
            return self._get_transformation_matrix_with_indices(fromIndex+1, toIndex) * self.frameStack[fromIndex]
        else:
            return inv(self.frameStack[fromIndex-1]) * self._get_transformation_matrix_with_indices(fromIndex-1, toIndex)

# use a list ('stack') of frames, moving from one to the next
def get_transformation_matrix(frameStack, fromFrameIndex, toFrameIndex):
    """
    frameStack = list of transformation matrices (of length N-1 where N is the number of frames)
    """
    #print fromFrameIndex, toFrameIndex
    direction = toFrameIndex - fromFrameIndex
    #A = matrix(identity(4,dtype=float64))
    if direction == 0:
        return matrix(identity(4, dtype=float64))
    if direction == 1:
        return frameStack[fromFrameIndex] # moving up stack, use stored matrix
    elif direction == -1:
        return inv(frameStack[toFrameIndex]) # moving down stack, use inverse
    elif direction > 1:
        # trying to move up more than one step, use recursion?
        return get_transformation_matrix(frameStack, fromFrameIndex+1, toFrameIndex) * frameStack[fromFrameIndex]
        #raise Exception('trying to move more than one step')
    elif direction < -1:
        # trying to move down more than one step, use recursion?
        return inv(frameStack[fromFrameIndex-1]) * get_transformation_matrix(frameStack, fromFrameIndex-1, toFrameIndex)
        #raise Exception('trying to move more than one step')

# def test_frame_manager():
#     fm = FrameManager()
#     fm.add_transform('skull','tricorner',vector.transform_to_matrix(tx=1.))
#     fm.add_transform('tricorner','camera',vector.transform_to_matrix(ty=1.))
#     fm.add_transform('camera','cnc',vector.transform_to_matrix(tz=1.))
#     
#     skullPoint = matrix([ [10*(rand()-0.5), 10*(rand()-0.5), 10*(rand()-0.5), 1.] ])
#     
#     frames = ['tricorner', 'camera', 'cnc']
#     for f in frames:
#         print "From skull to %s" % f
#         tPoint = skullPoint * fm.get_transform_matrix('skull',f)
#         cPoint = tPoint * fm.get_transform_matrix(f,'skull')
#         print "\ts-t:", array(skullPoint - tPoint)
#         print "\tSSE:", sum(array(skullPoint - cPoint)**2)

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
    
    test_routes(); print
    
    m = vector.transform_to_matrix(tx=1.)
    fm.add_transformation_matrix('skull','tc',m)
    test_routes(); print
    
    m = vector.transform_to_matrix(ty=1.)
    fm.add_transformation_matrix('tc','camera',m)
    test_routes(); print
    
    m = vector.transform_to_matrix(tz=1.)
    fm.add_transformation_matrix('camera','cnc',m)
    test_routes(); print
    
    print "FrameStack"
    for f in fm.frameStack:
        print f
    print
    
    startingPoint = matrix([ [10*(rand()-0.5), 10*(rand()-0.5), 10*(rand()-0.5), 1.] ])
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
            M = fm.get_transformation_matrix(s,e)
            cPoint = points[s] * M
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
    
    startingPoint = matrix([ [10*(rand()-0.5), 10*(rand()-0.5), 10*(rand()-0.5), 1.] ])
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