#!/usr/bin/env python

import os
import logging

# ----- Camera Calibration Settings -----
# ordered as 'left', 'right'
leftCamID = 49712223528793951
rightCamID = 49712223528793946
gridSize = (47,39)#(11,9)#(8,6)#(7,6)
gridBlockSize = 1.

# TODO sort out where this should go
calibrationDirectory = "/Users/%s/Repositories/coxlab/cncController/electrodeController/calibrations" % os.getlogin()