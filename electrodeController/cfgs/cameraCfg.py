#!/usr/bin/env python

import os

# ----- Camera Calibration Settings -----
# ordered as 'left', 'right'
camIDs = [49712223528793951, 49712223528793946]
gridSize = (8,5)
gridBlockSize = 1.27

# TODO sort out where this should go
calibrationDirectory = "/Users/%s/Repositories/coxlab/cncController/electrodeController/calibrations" % os.getlogin()