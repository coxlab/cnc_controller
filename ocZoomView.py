#!/usr/bin/env python

from Foundation import *
from AppKit import *
import objc
from objc import IBAction, IBOutlet

#import pylab, numpy

from OpenGL.GL import *
from OpenGL.GLUT import *

from glZoomView import ZoomView

class OCZoomView(NSOpenGLView, ZoomView):
    otherView = objc.IBOutlet()
    
    def awakeFromNib(self):
        self.gl_inited = False
        
        ZoomView.__init__(self)
        
        self.add_key_binding('z', 'zoom_in')
        self.add_key_binding('x', 'zoom_out')
        self.add_key_binding('c', 'increase_contrast')
        self.add_key_binding('C', 'decrease_contrast')
        self.add_key_binding('r', 'reset_contrast')
        
        self.mouseIsIn = True # make sure that the mouse is IN before passing on events
    
    def set_image_from_numpy(self, image):
        self.imageSize = (image.shape[1], image.shape[0])
        frame = self.frame()
        self.scale = max(frame.size.width/float(self.imageSize[0]), frame.size.height/float(self.imageSize[1]))
        self.load_texture_from_string(image.tostring())
        self.scheduleRedisplay()
    
    def set_image_from_cv(self, image):
        #pylab.ion()
        #pylab.figure()
        #a = numpy.fromstring(image.tostring(),numpy.uint8)
        #a = a.reshape((1040,1392))
        #pylab.imshow(a[:100,:100])
        #pylab.gray()
        # need to set:
        # - self.imageSize
        self.imageSize = (image.width, image.height)
        # - self.scale
        frame = self.frame()
        self.scale = max(frame.size.width/float(self.imageSize[0]), frame.size.height/float(self.imageSize[1]))
        # - self.imageTexture
        self.load_texture_from_string(image.tostring()) # "raw", "rgb", 0, -1
        self.scheduleRedisplay()
    
    @IBAction
    def showHelp_(self, sender):
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Camera Tab Help")
        alert.setInformativeText_("Right Click = add Zoom Area\nLeft Drag = move Zoom Area\nShift+Right Click = delete Zoom Area\nScroll = Zoom in/out")
        alert.setAlertStyle_(NSInformationalAlertStyle)
        alert.runModal()
    
    # ---------- Key events -------------
    
    def acceptsFirstResponder(self):
        return YES
    
    def becomeFirstResponder(self):
        return YES
    
    def resignFirstResponder(self):
        return YES
    
    def keyDown_(self, event):
        x, y = self.oc_to_gl(self.convertPoint_fromView_(event.locationInWindow(), None))
        #print event.characters(), x, y
        self.process_normal_keys(event.characters(), x, y)
        self.scheduleRedisplay()
        return
    
    #def performKeyEquivalent_(self, event):
    #    print event
    #    return YES
    
    # ----------- Mouse events -----------
    
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
        
        if event.modifierFlags() & NSShiftKeyMask:
            #print "trying to find zoom to delete"
            d, i = self.find_closest_zoom_distance(x/self.scale, y/self.scale)
            #print "attempting to delete:", i, "at", d
            if i != -1:
                #print "removing zoom here"
                self.zooms.remove(self.zooms[i])
                if self.selectedZoom >= i: self.selectedZoom -= 1
                #print "removing zoom there"
                self.otherView.zooms.remove(self.otherView.zooms[i])
                if self.otherView.selectedZoom >= i: self.otherView.selectedZoom -= 1
        else:
            self.add_zoomed_area(x/self.scale, y/self.scale)
            self.otherView.add_zoomed_area(x/self.otherView.scale, y/self.otherView.scale)
        
        self.process_mouse(GLUT_RIGHT_BUTTON, GLUT_DOWN, x, y)
        self.otherView.scheduleRedisplay()
        self.scheduleRedisplay()
    
    def rightMouseDragged_(self, event):
        pass
    
    def scrollWheel_(self, event):
        x,y = self.oc_to_gl(self.convertPoint_fromView_(event.locationInWindow(), None))
        
        #self.selectedZoom = self.find_closest_zoom_index(x/self.scale, y/self.scale)
        
        dZoom = event.deltaY()
        if dZoom > 0:
            newZoom = self.zooms[self.selectedZoom]['z'] * 1.1
        elif dZoom < 0:
            newZoom = self.zooms[self.selectedZoom]['z'] * 0.9
        else:
            newZoom = self.zooms[self.selectedZoom]['z']
        #newZoom = self.zooms[self.selectedZoom]['z'] * (1.0 + dZoom)
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