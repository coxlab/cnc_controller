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
    parentWindow = objc.IBOutlet()
    
    def awakeFromNib(self):
        self.gl_inited = False
        self.image = None
        self.zoomedX = 0.5
        self.zoomedY = 0.5
        self.zoom = 1.
        #self.parentWindow.setAcceptsMouseMovedEvents_(True)
        #self.acceptsFirstResponder()
        #self.becomeFirstResponder()
    
    #def mouseEntered_(self, event):
    #    print event
    
    #def mouseExited_(self, event):
    #    print event
    
    def scrollWheel_(self, event):
        dZoom = event.deltaY()
        if dZoom > 0:
            # zoom in
            print "zoom in:", dZoom
            self.zoom *= dZoom+1.
        elif dZoom < 0:
            # zoom out
            print "zoom out:", dZoom
            self.zoom /= abs(dZoom)+1
        if self.zoom < 1.0:
            self.zoom = 1.0
        if self.zoom > 100.:
            self.zoom = 100.
        self.scheduleRedisplay()
    
    def mouseDown_(self, event):
        pass
    
    def mouseUp_(self, event):
        pass
    
    def mouseDragged_(self, event):
        dx = event.deltaX() / (self.frame_width * self.zoom)
        dy = -event.deltaY() / (self.frame_height * self.zoom)
        self.zoomedX += dx
        self.zoomedY += dy
        print self.zoomedX, self.zoomedY
        self.scheduleRedisplay()
    
    def rightMouseDown_(self, event):
        pass
    
    def rightMouseUp_(self, event):
        pass
    
    def rightMouseDragged_(self, event):
        pass
    
    #def mouseMoved_(self, event):
    #    print event
    
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
    
    def draw_zoomed_image(self):
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
        
        
        # zoomed coords: 0,0 = bottom left, 1,1 = top right
        # texture coords: 0,0 = bottom left, 1,1 = top right
        # opengl coords: -1,-1 = bottom left, 1,1 = top right 
        zhw = 0.3 # zoom window half width
        #self.zoom = 10.
        def to_gl(x,y):
            return x*2.-1., y*2.-1.
        
        glBegin(GL_QUADS)
        # bottom left
        glTexCoord2f(self.zoomedX - zhw/self.zoom, 1 - self.zoomedY + zhw/self.zoom)
        gx,gy = to_gl(self.zoomedX-zhw, self.zoomedY-zhw)
        glVertex3f(gx, gy, 0.)
        
        # bottom right
        glTexCoord2f(self.zoomedX + zhw/self.zoom, 1 - self.zoomedY + zhw/self.zoom)
        gx,gy = to_gl(self.zoomedX+zhw, self.zoomedY-zhw)
        glVertex3f(gx, gy, 0.)
        
        # top right
        glTexCoord2f(self.zoomedX + zhw/self.zoom, 1 - self.zoomedY - zhw/self.zoom)
        gx,gy = to_gl(self.zoomedX+zhw, self.zoomedY+zhw)
        glVertex3f(gx, gy, 0.)
        
        # top left
        glTexCoord2f(self.zoomedX - zhw/self.zoom, 1 - self.zoomedY - zhw/self.zoom)
        gx,gy = to_gl(self.zoomedX-zhw, self.zoomedY+zhw)
        glVertex3f(gx, gy, 0.)
        glEnd()
        glBindTexture(GL_TEXTURE_2D, 0)
        
        glDeleteTextures(texture)
        
        glColor4f(1., 0., 0., 0.5)
        glBegin(GL_LINES)
        
        glVertex2f(*to_gl(self.zoomedX, self.zoomedY-zhw))
        glVertex2f(*to_gl(self.zoomedX, self.zoomedY+zhw))
        
        glVertex2f(*to_gl(self.zoomedX-zhw, self.zoomedY))
        glVertex2f(*to_gl(self.zoomedX+zhw, self.zoomedY))
        glEnd()
        
        
        
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
        if not self.canDraw():
            print "cannot draw: self.canDraw() == False"
            #self.openGLContext().flushBuffer()
            return
            
        if self.gl_inited == False:
            self.initGL()
            pass
        
        frame = self.frame()
        self.frame_width = frame.size.width
        self.frame_height = frame.size.height
        
        glViewport(0, 0, int(self.frame_width), int(self.frame_height))
        #glOrtho(0, 1., 0, 1.,-1.,1.)
    
        glClear(GL_COLOR_BUFFER_BIT)
        if(self.image == None):
            print "No image"
            self.openGLContext().flushBuffer()
            return
        
        self.draw_image()
        self.draw_zoomed_image()
        self.openGLContext().flushBuffer()