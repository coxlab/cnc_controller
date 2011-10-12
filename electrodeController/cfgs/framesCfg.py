#!/usr/bin/env python

import logging, os

import numpy

# on seat, seen from camera
#tcRegPoints = numpy.array([[-6.5,3.0,0.0,1.],
#                            [0.,0.0,0.0,1.],
#                            [6.5,3.0,0.0,1.]])

tcRegPoints = []
for x in xrange(9):
    for y in xrange(5):
        tcRegPoints.append([x,y,0,1.])
tcRegPoints = numpy.array(tcRegPoints)

leftTCRegSeedPoints = [[643.27451781, 522.57654614],
                        [771.47429952, 536.68860298],
                        [877.61847028, 517.71243038]]

rightTCRegSeedPoints = [[703.82119604, 578.75227713],
                        [802.02238616, 594.22537199],
                        [928.36786805, 578.5496978]]

# tcRegPoints = numpy.array([[-6.5,6.9,-2.5,1.],
#                             [0.,9.9,-2.5,1.],
#                             [6.5,6.9,-2.5,1.]])

#tcRegPoints = numpy.array([[6.50, 14.54, -5.0, 1.0],
#                            [0.00, 17.54, -5.0, 1.0],
#                            [-6.50, 14.54, -5.0, 1.0]])