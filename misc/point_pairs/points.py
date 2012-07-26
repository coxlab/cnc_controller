#!/usr/bin/env python

#from numpy import *
#from numpy.linalg import inv
#
#import vector

# what about the src Image?

class Point2D:
    def __init__(self, x=0., y=0.):
        self.x = x
        self.y = y

class Point3D(Point2D):
    def __init__(self, x=0., y=0., z=0.):
        Point2D.__init__(self,x,y)
        
        self.z = z

class PointPair(Point3D):
    def __init__(self, x=0., y=0., z=0., left=None, right=None):
        Point3d.__init__(self,x,y,z)
        
        self.left = left if left is not None else Point2D()
        self.right = right if right is not None else Point2D()