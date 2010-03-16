#!/usr/bin/env python

# ====== What is this? =======
# This 'configuration file' is actually just a python script.
# The idea is that any arbitrary processing can be performed inside this file,
# as compared to static configuration files (xml, ini, etc).
#
# ====== How do I use this? =======
# if this file is named cfg.py, then:
#  import cfg
# Done.
# In general (and for other modules too) it's not always safe to call:
#  from cfg import *
#
# ====== How do I read configuration values? ======
# It's probably not a good idea to assume that a configuration value
# does NOT exist. So, if you want to read cfg.foo, try this:
#  if 'foo' in dir(cfg):
#    myFoo = cfg.foo
#  else:
#    myFoo = 'default value'
# or as a one-liner
#  myFoo = cfg.foo if ('foo' in dir(cfg)) else 'default value'
#
# ====== What if I want to use this cfg file to read a different file? =======
# You could use something like this:
#  from otherCfg import *
# But be careful! This can overwrite values that you've already defined.
# For example, if otherCfg contains:
#  foo = 'bar2'
# And you read it in as follows:
#  foo = 'bar'
#  from otherCfg import *
# Then cfg.foo will equal 'bar2' NOT 'bar'
#
# ====== What is a good way to use this? ======
# Setup one file (cfg.py) with defaults, and one (customCfg.py) with
# custom setting. The default config file (cfg.py) should look like this:
#  foo = 'bar'
#  # ...exaustive definition of defaults...
#  try:
#    from customCfg import *
#  except:
#    print "No custom configuration found"
# This way the values in the custom file will overwrite the defaults.


# ----- Camera Calibration Settings -----
gridSize = (8,5)
gridBlockSize = 2.73

# TODO sort out where this should go
#calibrationDirectory = "stereoCalibration"


# ----- ImageBridge Settings ------
zoomColors = [(1., 0., 0., 0.5),
            (0., 1., 0., 0.5),
            (0., 0., 1., 0.5),
            (1., 1., 0., 0.5),
            (1., 0., 1., 0.5),
            (0., 1., 1., 0.5)]
zoomColorNames = ['r', 'g', 'b', 'y', 'm', 't']
zoomHalfWidth = 0.2


# ----- CNC settings ------
cncLinearAxesIP = "169.254.0.9"
cncLinearAxesPort = 8003
cncHeadAxesIP = "169.254.0.9"
cncHeadAxesPort = 8004

serialConnectionTimeout = 4.0

xStep = 1.27
yStep = 1.27
zStep = 1.27

bStep = 1.0
wStep = 1.0

xPosLimit = 12.70
xNegLimit = -12.70
yPosLimit = 12.70
yNegLimit = -12.70
zPosLimit = 12.70
zNegLimit = -12.70


# import custom configuration file, which will overwrite default values
#appPath = '/Users/graham/Repositories/coxlab/cncController/build/Debug/cncController.app'
#resourcePath = '%s/Contents/Resources' % appPath

try:
    from customCfg import *
except:
    print "No custom configuration (customCfg.py) found"
