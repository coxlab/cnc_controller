#!/usr/bin/env python

import os

# the first time this is imported, the module is created,
# subsequent calls to import (I think) just link to the already loaded, and potentially modified module
# so...
# there is only 1 global cfg and that is IT

from bjgcfg import *
assign_cfg_module(__name__)

useManualImageProcessor = True
fakeCNC = True
fakeCameras = True
fakeFramesDir = '/Users/%s/Repositories/coxlab/cncController/fakeFrames' % os.getlogin()

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