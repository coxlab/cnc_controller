#!/usr/bin/env python

# based heavily on OpenGLContext.quaternion

import numpy

# function I need:
# -matrix
# -fromEuler
# -__mul__ (two quaternions)

def normalize(a):
    if type(a) != numpy.ndarray:
        a = numpy.array(a)
    length = numpy.sqrt(numpy.sum(a**2))
    return a/length

def fromXYZR(x, y, z, r):
    x,y,z = normalize((x,y,z))
    return Quaternion([numpy.cos(r/2.0), x*(numpy.sin(r/2.0)), y*(numpy.sin(r/2.0)), z*(numpy.sin(r/2.0))])

def fromEuler(x=0, y=0, z=0):
    if x:
        base = fromXYZR(1,0,0,x)
        if y:
            base = base * fromXYZR(0,1,0,y)
        if z:
            base = base * fromXYZR(0,0,1,z)
        return base
    elif y:
        base = fromXYZR(0,1,0,y)
        if z:
            base = base * fromXYZR(0,0,1,z)
        return base
    else:
        return fromXYZR(0,0,1,z)

class Quaternion:
    def __init__(self, elements=[1,0,0,0]):
        #normalize the quaternion
        # elements = numpy.array(elements)
        # length = numpy.sqrt(numpy.sum(elements**2))
        # if length != 1:
        #     elements /= length
        self.internal = normalize(elements)
    def __mul__(self, other):
        if hasattr(other, 'internal'):
            w1,x1,y1,z1 = self.internal
            w2,x2,y2,z2 = other.internal
            
            w = w1*w2 - x1*x2 - y1*y2 - z1*z2
            x = w1*x2 + x1*w2 + y1*z2 - z1*y2
            y = w1*y2 + y1*w2 + z1*x2 - x1*z2
            z = w1*z2 + z1*w2 + x1*y2 - y1*x2
            return self.__class__([w,x,y,z])
        else:
            return numpy.dot(self.matrix(), other)
    def matrix(self):
        w,x,y,z = self.internal
        return numpy.array([
            [ 1-2*y*y-2*z*z, 2*x*y+2*w*z, 2*x*z-2*w*y, 0],
            [ 2*x*y-2*w*z, 1-2*x*x-2*z*z, 2*y*z+2*w*x, 0],
            [ 2*x*z+2*w*y, 2*y*z-2*w*x, 1-2*x*x-2*y*y, 0],
            [0,0,0,1]],dtype=numpy.float64)
    def __getitem__(self, x):
        return self.internal[x]
    def __len__(self):
        return len(self.internal)
    def __repr__(self):
        return """<%s WXYZ=%s>""" % (self.__class__.__name__, list(self.internal))
    