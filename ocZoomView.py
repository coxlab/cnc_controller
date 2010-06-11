#!/usr/bin/env python

from Foundation import *
from AppKit import *
import objc
from objc import IBAction, IBOutlet


from OpenGL.GL import *
from OpenGL.GLUT import *
from zoomView import ZoomView

class OCZoomView(NSOpenGLView, ZoomView):
    otherView = objc.IBOutlet()
    
    def awakeFromNib(self):
        self.gl_inited = False
        ZoomView.__init__(self)
        self.mouseIsIn = True # make sure that the mouse is IN before passing on events
    
    def set_image_from_cv(self, image):
        # need to set:
        # - self.imageSize
        self.imageSize = (image.width, image.height)
        # - self.scale
        frame = self.frame()
        self.scale = max(frame.size.width/float(self.imageSize[0]), frame.size.height/float(self.imageSize[1]))
        # - self.imageTexture
        self.load_texture_from_string(image.tostring())
        self.scheduleRedisplay()
    
    def mouseDown_(self, event):
        x,y = self.oc_to_gl(self.convertPoint_fromView_(event.locationInWindow(), None))
        self.process_mouse(GLUT_LEFT_BUTTON, GLUT_DOWN, x, y)
        #self.scheduleRedisplay()
    
    def mouseUp_(self, event):
        x,y = self.oc_to_gl(self.convertPoint_fromView_(event.locationInWindow(), None))
        self.process_mouse(GLUT_LEFT_BUTTON, GLUT_UP, x, y)
        self.scheduleRedisplay()
    
    def mouseDragged_(self, event):
        x,y = self.oc_to_gl(self.convertPoint_fromView_(event.locationInWindow(), None))
        self.process_active_mouse_motion(x, y)
        self.scheduleRedisplay()
    
    def rightMouseDown_(self, event):
        x,y = self.oc_to_gl(self.convertPoint_fromView_(event.locationInWindow(), None))
        self.process_mouse(GLUT_RIGHT_BUTTON, GLUT_DOWN, x, y)
        #self.scheduleRedisplay()
    
    def rightMouseUp_(self, event):
        x,y = self.oc_to_gl(self.convertPoint_fromView_(event.locationInWindow(), None))
        self.add_zoomed_area(x/self.scale, y/self.scale)
        self.otherView.add_zoomed_area(x/self.otherView.scale, y/self.otherView.scale)
        self.process_mouse(GLUT_RIGHT_BUTTON, GLUT_DOWN, x, y)
        self.otherView.scheduleRedisplay()
        self.scheduleRedisplay()
    
    def rightMouseDragged_(self, event):
        pass
    
    def scrollWheel_(self, event):
        x,y = self.oc_to_gl(self.convertPoint_fromView_(event.locationInWindow(), None))
        self.selectedZoom = self.find_closest_zoom_index(x, y)
        
        dZoom = event.deltaY()
        newZoom = self.zooms[self.selectedZoom]['z'] * (1.0 + dZoom)
        if newZoom < 1.:
            newZoom = 1.
        elif newZoom > 100.:
            newZoom = 100.
        self.zooms[self.selectedZoom]['z'] = newZoom
        
        self.scheduleRedisplay()
    
    def oc_to_gl(self, pos):
        h = self.frame().size.height
        return pos.x, pos.y*-1 + h
    
    def initGL(self):
        glEnable(GL_BLEND)
        glEnable(GL_TEXTURE_2D)
        glDisable(GL_LIGHTING)
        glPixelStorei(GL_UNPACK_ALIGNMENT,1)
        self.gl_inited = True
    
    def scheduleRedisplay(self):
        self.setNeedsDisplay_(True)
    
    def drawRect_(self, frame):
        if not self.canDraw():
            return
        
        if self.gl_inited == False:
            self.initGL()
        
        glClear(GL_COLOR_BUFFER_BIT)
        
        frame = self.frame()
        self.frame_width = frame.size.width
        self.frame_height = frame.size.height
        glViewport(0, 0, int(self.frame_width), int(self.frame_height))
        
        # draw zoom view
        self.draw()
        
        self.openGLContext().flushBuffer()