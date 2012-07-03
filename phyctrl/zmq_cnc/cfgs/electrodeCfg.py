#!/usr/bin/env python

import os

import numpy

electrodeMesh = "/Users/%s/Repositories/coxlab/cncController/' \
        'media/a_10.obj" % os.getlogin()
electrodeTexture = None
electrodePadSpacing = 0.100  # mm
electrodeFirstPad = 0.050  # mm from tip to first pad
electrodeRefSpacing = 0.5  # mm from last pad to reference

electrodePadOffsets = -1. * (numpy.arange(32) * electrodePadSpacing \
        + electrodeFirstPad)
electrodeRefOffset = -1. * (electrodeFirstPad + electrodePadSpacing * 31 \
        + electrodeRefSpacing)

## positions relative to the tip
#electrodePadPositions = []
## first pad
#electrodePadPositions.append([0., 0., -electrodeFirstPad, 1.])
#for i in xrange(31):
#    prevPad = electrodePadPositions[i]
#    prevPad[2] = prevPad[2] - electrodePadSpacing
#    electrodePadPositions.append(prevPad)#
#
#del prevPad

#electrodePadPositions = numpy.array(electrodePadPositions)

#electrodeRefPosition = numpy.array([0., 0., -(electrodeFirstPad + \
#        electrodePadSpacing*31 + electrodeRefSpacing), 1.])
