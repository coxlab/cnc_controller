#!/usr/bin/env python

import logging
log = logging.getLogger(__name__)

import conversions, filecamera, stereocamera
__all__ = ['conversions', 'filecamera', 'stereocamera']

# try to load dc1394camera
# this will fail if python cannot find pydc1394
try:
    import dc1394camera
    __all__.append('dc1394camera')
except:
    log.warning('could not load dc1394camera')