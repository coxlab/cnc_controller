#!/usr/bin/env python

from Foundation import *
from AppKit import *
import objc
from objc import IBAction, IBOutlet

from OpenGL.GL import *

import cameraPair


class ImageBridge (NSObject):
    # need outlets to the 2 opengl views
    # initialization
    leftImageView = objc.IBOutlet()
    rightImageView = objc.IBOutlet()
    
    def awakeFromNib(self):
        # create camera pair
        self.cameras = cameraPair.CameraPair()
    
    @IBAction
    def connectToCameras_(self, sender):
        self.cameras.connect()
    
    @IBAction
    def loadCalibration_(self, sender):
        #TODO add this to the configuration file
        self.cameras.load_calibration('/Users/graham/Repositories/coxlab/cncController/stereoCalibration')
        self.cameras.compute_rectify_matricies((1280,960))
    
    @IBAction
    def captureFrames_(self, sender):
        im1, im2 = self.cameras.capture()
        self._.leftImageView.update_image(im1)
        self._.rightImageView.update_image(im2)

class CVImageViewer (NSOpenGLView):
    def awakeFromNib(self):
        self.gl_inited = False
        self.image = None
    
    def update_image(self, image):
        self.image = image
        self.scheduleRedisplay()
    
    def draw_image(self):
        texture = glGenTextures(1)
        
        glColor4f(1.,1.,1.,1.)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE8, self.image.width, self.image.height,
                    0, GL_LUMINANCE, GL_UNSIGNED_BYTE, self.image.tostring())
        glBindTexture(GL_TEXTURE_2D, texture)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0) 
        glVertex3f(-1., 1.,  0.0) # Bottom Left
        glTexCoord2f(1.0, 0.0)
        glVertex3f( 1., 1.,  0.0) # Bottom Right
        glTexCoord2f(1., 1.)
        glVertex3f( 1.0,  -1.0,  0.0) # Top Right
        glTexCoord2f(0.0, 1.0)
        glVertex3f(-1.0,  -1.0,  0.0) # Top Left
        glEnd()
        glBindTexture(GL_TEXTURE_2D, 0)
        
        glDeleteTextures(texture)
        
    def initGL(self):
        glEnable(GL_BLEND)
        glEnable(GL_TEXTURE_2D)
        glDisable(GL_LIGHTING)
        #glBlendFunc(GL_ONE, GL_ZERO)
        #glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        #glBlendFunc(GL_ONE_MINUS_DST_ALPHA, GL_DST_ALPHA)
        glPixelStorei(GL_UNPACK_ALIGNMENT,1)
        #self.gl_inited = True
    
    def scheduleRedisplay(self):
        """Call to force redisplay of the opengl view"""
        self.setNeedsDisplay_(True)
    
    def drawRect_(self, frame):
        """Display function"""
        if self.gl_inited == False:
            self.initGL()
            pass
        
        frame = self.frame()
        self.frame_width = frame.size.width
        self.frame_height = frame.size.height
        
        glViewport(0, 0, int(self.frame_width), int(self.frame_height))
        #glOrtho(0, 1., 0, 1.,-1.,1.)
    
        glClear(GL_COLOR_BUFFER_BIT)
        if(not self.image):
            print "No image"
            self.openGLContext().flushBuffer()
            return
        
        self.draw_image()
        self.openGLContext().flushBuffer()