#!/usr/bin/env python

import os
import logging

# ----- Camera Calibration Settings -----
# ordered as 'left', 'right'
leftCamID = 49712223528793951
rightCamID = 49712223528793946
gridSize = (47, 39)
#gridSize = (11,9)#(8,6)#(7,6)
#gridSize = (21,19)
gridBlockSize = 1.

leftYLimits = [190, 755]
rightYLimits = [206, 763]

# TODO sort out where this should go
calibrationDirectory = "/Users/%s/Repositories/coxlab/cncController/' \
        'electrodeController/calibrations" % os.getlogin()

leftCameraShutter = 600
rightCameraShutter = 550
