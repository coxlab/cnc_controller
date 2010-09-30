#!/usr/bin/env python

import logging, os

import numpy

# on seat, seen from camera
tcRegPoints = numpy.array([[-6.5,3.0,0.0,1.],
                            [0.,0.0,0.0,1.],
                            [6.5,3.0,0.0,1.]])
                            
# tcRegPoints = numpy.array([[-6.5,6.9,-2.5,1.],
#                             [0.,9.9,-2.5,1.],
#                             [6.5,6.9,-2.5,1.]])

#tcRegPoints = numpy.array([[6.50, 14.54, -5.0, 1.0],
#                            [0.00, 17.54, -5.0, 1.0],
#                            [-6.50, 14.54, -5.0, 1.0]])