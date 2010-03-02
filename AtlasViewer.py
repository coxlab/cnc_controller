#!/usr/bin/env python

from Foundation import *
from AppKit import *
import objc
from objc import IBAction, IBOutlet

from OpenGL.GL import *
import PIL.Image

import cameraPair


class AtlasViewer (NSOpenGLView):
    def awakeFromNib(self):
        # gl_inited is also touched by objc
        self.gl_inited = False
        self.image = None
    
    def load_image(self, filename):
        self.image = PIL.Image.open(filename)
        if self.image.mode != 'RGB':
            self.image = self.image.convert('RGB')  
        self.scheduleRedisplay()
    
    def draw_image(self):
        texture = glGenTextures(1)
        
        glColor4f(1.,1.,1.,1.)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, self.image.size[0], self.image.size[1],
                    0, GL_RGB, GL_UNSIGNED_BYTE, self.image.tostring())
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
            self.load_image("/Users/graham/man/ratBrainAtlas/section_images/png/012.png")
            self.openGLContext().flushBuffer()
            return
        
        self.draw_image()
        self.openGLContext().flushBuffer()