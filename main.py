#import modules required by application

import numpy

import objc
import Foundation
import AppKit

from PyObjCTools import AppHelper

from ocController import *
from ocZoomView import *
#from ocCenteringSlider import *
from ocMeshView import *
from ocAtlasView import *

#print "Python file is open and running, passing control to AppKit"
# import the child class of NSObject that provides the bridge between
# objc and python

# OLD
#from CNCController import *
#from ImageBridge import *
#from AtlasViewer import *
#from MeshViewer import *

# pass control to AppKit and run events (linked to MainMenu.nib)
AppHelper.runEventLoop()
