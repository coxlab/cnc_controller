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
leftFakeFramesDir = '/Users/%s/Repositories/coxlab/cncController/inLogs/1285709674/camera/0' % os.getlogin()
rightFakeFramesDir = '/Users/%s/Repositories/coxlab/cncController/inLogs/1285709674/camera/1' % os.getlogin()

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

# this is really ugly and should be fixed
global loggingStarted, logDir, log, cameraLogDir, cameraLog, cncLogDir, cncLog, framesLogDir, framesLog
loggingStarted = False

# make logs but don't connect them yet
logDir = '/Users/%s/Repositories/coxlab/cncController/logs/%i' % (os.getlogin(), time.time())
log = logging.root
cameraLogDir = '%s/camera' % logDir
cameraLog = logging.getLogger('camera')
cncLogDir = '%s/cnc' % logDir
cncLog = logging.getLogger('cnc')
framesLogDir = '%s/frames' % logDir
framesLog = logging.getLogger('frames')

def start_logging():
    global loggingStarted
    if loggingStarted == True:
        return
    global logDir, log, cameraLogDir, cameraLog, cncLogDir, cncLog, framesLogDir, framesLog
    # setup logging
    # TODO I can't timestamp this at the moment because I don't know how to pass
    # logDir to the external cfgs
    if not os.path.exists(logDir): os.makedirs(logDir)
    # create instance of root logger
    # TODO I also don't know how to pass this on :(
    logLevel = logging.DEBUG
    logging.basicConfig(level=logLevel, filename='%s/root.log' % logDir)
    # log = logging.root


    
    #cameraLogDir = '/Users/%s/Repositories/coxlab/cncController/logs/camera/' % os.getlogin()
    if not os.path.exists(cameraLogDir): os.makedirs(cameraLogDir)
    if not os.path.exists(cameraLogDir+'/0'): os.makedirs(cameraLogDir+'/0')
    if not os.path.exists(cameraLogDir+'/1'): os.makedirs(cameraLogDir+'/1')


    # cameraLog = logging.getLogger('camera')
    cameraLog.setLevel(logLevel)
    cameraLog.addHandler(logging.FileHandler('%s/camera.log' % cameraLogDir))


    
    #cncLogDir = '/Users/%s/Repositories/coxlab/cncController/logs/cnc/' % os.getlogin()
    if not os.path.exists(cncLogDir): os.makedirs(cncLogDir)

    # cncLog = logging.getLogger('cnc')
    cncLog.setLevel(logLevel)
    cncLog.addHandler(logging.FileHandler('%s/cnc.log' % cncLogDir))
    
    
    #framesLogDir = '/Users/%s/Repositories/coxlab/cncController/logs/frames/' % os.getlogin()
    if not os.path.exists(framesLogDir): os.makedirs(framesLogDir)

    # framesLog = logging.getLogger('frames')
    framesLog.setLevel(logLevel)
    framesLog.addHandler(logging.FileHandler('%s/frames.log' % framesLogDir))
    
    loggingStarted = True