#
#  main.py
#  EyeTracker
#
#  Created by David Cox on 11/13/08.
#  Copyright Harvard University 2008. All rights reserved.
#

#import modules required by application

import objc
import Foundation
import AppKit

from PyObjCTools import AppHelper

from ocController import *
from ocZoomView import *
from ocCenteringSlider import *

#print "Python file is open and running, passing control to AppKit"
# import the child class of NSObject that provides the bridge between objc and python

# OLD
#from CNCController import *
#from ImageBridge import *
#from AtlasViewer import *
#from MeshViewer import *

# pass control to AppKit and run events (linked to MainMenu.nib)
AppHelper.runEventLoop()
