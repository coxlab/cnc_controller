#!/usr/bin/env python

import logging, os, time

# the first time this is imported, the module is created,
# subsequent calls to import (I think) just link to the already loaded, and potentially modified module
# so...
# there is only 1 global cfg and that is IT
 
from bjgcfg import *
assign_cfg_module(__name__)

useManualImageProcessor = True
fakeCNC = True
fakeCameras = True
#fakeFramesDir = '/Users/%s/Repositories/coxlab/cncController/fakeFrames' % os.getlogin()
fakeFramesDir = '/Users/%s/Repositories/coxlab/cncController/inLogs/1279205629/camera' % os.getlogin()

cfgDir = '/Users/%s/Repositories/coxlab/cncController/electrodeController/cfgs' % os.getlogin()
externalCfgs = ['atlasCfg.py', 'cameraCfg.py', 'cncCfg.py', 'framesCfg.py', 'electrodeCfg.py']

# import custom configuration file, which will overwrite default values
if os.path.exists('%s/%s' % (cfgDir, 'customCfg.py')):
    load_external_cfg('%s/%s' % (cfgDir, 'customCfg.py'))

# load all external configuration files
for e in externalCfgs:
    eCfg = '%s/%s' % (cfgDir, e)
    if os.path.exists(eCfg):
        load_external_cfg(eCfg)
    else:
        raise Exception ('%s does not exist' % eCfg)


# setup logging
# TODO I can't timestamp this at the moment because I don't know how to pass
# logDir to the external cfgs
logDir = '/Users/%s/Repositories/coxlab/cncController/logs/%i' % (os.getlogin(), time.time())
if not os.path.exists(logDir): os.makedirs(logDir)
# create instance of root logger
# TODO I also don't know how to pass this on :(
logLevel = logging.DEBUG
logging.basicConfig(level=logLevel, filename='%s/root.log' % logDir)
log = logging.root


cameraLogDir = '%s/camera' % logDir
#cameraLogDir = '/Users/%s/Repositories/coxlab/cncController/logs/camera/' % os.getlogin()
if not os.path.exists(cameraLogDir): os.makedirs(cameraLogDir)

cameraLog = logging.getLogger('camera')
cameraLog.setLevel(logLevel)
cameraLog.addHandler(logging.FileHandler('%s/camera.log' % cameraLogDir))


cncLogDir = '%s/cnc' % logDir
#cncLogDir = '/Users/%s/Repositories/coxlab/cncController/logs/cnc/' % os.getlogin()
if not os.path.exists(cncLogDir): os.makedirs(cncLogDir)

cncLog = logging.getLogger('cnc')
cncLog.setLevel(logLevel)
cncLog.addHandler(logging.FileHandler('%s/cnc.log' % cncLogDir))


framesLogDir = '%s/frames' % logDir
#framesLogDir = '/Users/%s/Repositories/coxlab/cncController/logs/frames/' % os.getlogin()
if not os.path.exists(framesLogDir): os.makedirs(framesLogDir)

framesLog = logging.getLogger('frames')
framesLog.setLevel(logLevel)
framesLog.addHandler(logging.FileHandler('%s/frames.log' % framesLogDir))