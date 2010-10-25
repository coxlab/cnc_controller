#!/usr/bin/env python

import time

import numpy

from electrodeController import cfg
from electrodeController import vector

from Foundation import *
from AppKit import *
import objc
from objc import IBAction, IBOutlet

from glZoomView import ZoomView
from ocZoomView import OCZoomView

from OpenGL.GL import *
from OpenGL.GLUT import *

class OCAtlasView (OCZoomView):
    #ocFigureIndex = objc.ivar(u"ocFigureIndex")
    controller = objc.IBOutlet()
    
    atlasImages = NSMutableDictionary.alloc().init()
    
    def awakeFromNib(self):
        self.gl_inited = False
        
        ZoomView.__init__(self)
        
        self.add_key_binding('z', 'zoom_in')
        self.add_key_binding('x', 'zoom_out')
        self.add_key_binding('c', 'increase_contrast')
        self.add_key_binding('C', 'decrease_contrast')
        self.add_key_binding('r', 'reset_contrast')
        
        self.mouseIsIn = True # make sure that the mouse is IN before passing on events
        
        # load all the images into textures
        # set the current texture
        for k in cfg.atlasSliceLocations.keys()[1:-1]:
            f = u"%s/%03.i.eps" % (cfg.atlasImagesDir, k)
            #print f
            self._.atlasImages[k] = NSImage.alloc().initWithContentsOfFile_(f)
            #print self.atlasImages[k]
        #print k
        #self.imageSize = self.atlasImages[k].size()
        #print imageSize
        #self.viewImage = NSImage.alloc().initWithSize_(imageSize)
        #self.viewImage = NSImage.alloc().initWithSize_((668,481))
        #print self.viewImage.size()
        #atlasSliceLocations.keys()
        #self._.ocFigureIndex = 106 - cfg.defaultAtlasImage#int(cfg.defaultAtlasImage.split('.')[0])
        self.sectionIndex = 106 - cfg.defaultAtlasImage#int(cfg.defaultAtlasImage.split('.')[0])
        self.pathParams = None
        #self.regenerate_view_image()
        self.set_image_from_nsimage(self.atlasImages[cfg.defaultAtlasImage])
    
    def set_image_from_nsimage(self, nsimage):
        self.openGLContext().makeCurrentContext()
        self.imageSize = (nsimage.size()[0], nsimage.size()[1])
        frame = self.frame()
        self.scale = max(frame.size.width/float(self.imageSize[0]), frame.size.height/float(self.imageSize[1]))
        # convert nsimage to string
        nsimage.lockFocus()
        self.imageData = str(NSBitmapImageRep.alloc().initWithFocusedViewRect_(((0,0),nsimage.size())).bitmapData())
        nsimage.unlockFocus()
        
        glEnable(GL_TEXTURE_2D)
        if self.imageTexture != None:
            glDeleteTextures(self.imageTexture)
        self.imageTexture = glGenTextures(1)
        
        glColor4f(1., 1., 1., 1.)
        glBindTexture(GL_TEXTURE_2D, self.imageTexture)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.imageSize[0], self.imageSize[1],
                    0, GL_RGBA, GL_UNSIGNED_BYTE, self.imageData) # RADAR GL_UNSIGNED_BYTE may be wrong
        glBindTexture(GL_TEXTURE_2D, 0)
        
        #data = image_rep.representationUsingType_properties_(NSPNGFileType, None)
        #data.writeToFile_atomically_(filepath, False) 
        # load texture from string
        #self.load_texture_from_string(str(image_rep.bitmapData()))
        print len(self.imageData), self.imageSize[0] * self.imageSize[1]*4
        self.scheduleRedisplay()
    
    @IBAction
    def saveAtlasImage_(self, sender):
        pass
    
    @IBAction
    def positionChanged_(self, sender):
        print "position changed:", sender.intValue()
        self.sectionIndex = 106 - sender.intValue()
        self.set_image_from_nsimage(self.atlasImages[self.sectionIndex])
    
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
                ##print "removing zoom there"
                #self.otherView.zooms.remove(self.otherView.zooms[i])
                #if self.otherView.selectedZoom >= i: self.otherView.selectedZoom -= 1
        else:
            self.add_zoomed_area(x/self.scale, y/self.scale)
            #self.otherView.add_zoomed_area(x/self.otherView.scale, y/self.otherView.scale)
        
        self.process_mouse(GLUT_RIGHT_BUTTON, GLUT_DOWN, x, y)
        #self.otherView.scheduleRedisplay()
        self.scheduleRedisplay()
    
    def draw_electrode(self):
        # opengl coordinates: +1 (right) +1 (up) -1(left) -1(down)
        # atlas coordinates: + (right) - (left) 0(top) -(down)
        #sectionIndex = 106 - self.ocFigureIndex
        # check if path has been measured
        if self.pathParams == None:
            return
        
        # set culling distances
        apMax = cfg.atlasSliceLocations[self.sectionIndex]
        apMin = apMax - cfg.atlasSliceThickness
        
        # draw path in red
        o = numpy.array([self.pathParams[0], self.pathParams[1], self.pathParams[2]])
        m = numpy.array([self.pathParams[3], self.pathParams[4], self.pathParams[5]])
        # test if m and n=[0, 1, 0] are parallel: dot(m,n) == 0
        n = numpy.array([0.,-1.,0.])
        d = numpy.dot(n,m)
        if d != 0.:
            # calculate intersection at ap min
            w = o - numpy.array([0., apMin, 0.])
            sMin = -numpy.dot(n,w) / d
            pMin = o + m * sMin
            # calculate intersection at ap max
            w = o - numpy.array([0., apMax, 0.])
            sMax = -numpy.dot(n,w) / d
            pMax = o + m * sMax
            # draw line
            self.draw_line(self.mm_to_canvas(self.viewImage, self.sectionIndex, pMin[0], pMin[2]),
                        self.mm_to_canvas(self.viewImage, self.sectionIndex, pMax[0], pMax[2]),NSColor.redColor(),4)
        
        # draw tip in black
        tip = o + self.controller.ocW * m
        
        self.draw_atlas_location(self.viewImage, self.sectionIndex, tip[0], tip[1], tip[2], apMin, apMax ,color=NSColor.blackColor())
        
        # draw pads in blue
        pads = []
        for dw in xrange(32):
            w = dw * 0.1 + .05 + self.controller.ocW
            pads.append(o + w * m)
        for pad in pads:
            self.draw_atlas_location(self.viewImage, self.sectionIndex, pad[0], pad[1], pad[2], apMin, apMax, color=NSColor.blueColor())
        
        # draw ref in green
        ref = o + (self.controller.ocW + 3.650) * m
        self.draw_atlas_location(self.viewImage, self.sectionIndex, ref[0], ref[1], ref[2], apMin, apMax, color=NSColor.greenColor())
    
    def drawRect_(self, frame):
        #print "in drawRect"
        if not self.canDraw():
            #print "couldn't draw"
            return
        
        if self.gl_inited == False:
            #print "gl not inited"
            self.initGL()
        
        #print "clearing"
        glClear(GL_COLOR_BUFFER_BIT)
        
        #print "getting frame"
        frame = self.frame()
        self.frame_width = frame.size.width
        self.frame_height = frame.size.height
        glViewport(0, 0, int(self.frame_width), int(self.frame_height))
        
        # draw zoom view
        #print "drawing"
        self.draw()
        #self.draw_electrode()
        
        #print "flushing"
        self.openGLContext().flushBuffer()

# class OCAtlasView (NSObject):
#     # image loaded from atlas.eps files
#     atlasImages = NSMutableDictionary.alloc().init()
#     #atlasImage = NSImage.alloc().initWithContentsOfFile_(u"%s/%s" % (cfg.atlasImagesDir, cfg.defaultAtlasImage))
#     # image containing the current electrode path/pads/etc...
#     #overlayImage = NSImage.alloc().initWithSize_(atlasImage.size())
#     # combined image (atlas+overlay) to be displayed in atlasImageView
#     viewImage = None#NSImage.alloc().initWithSize_(atlasImage.size())
#     
#     ocFigureIndex = objc.ivar(u"ocFigureIndex")
#     controller = objc.IBOutlet()
#     atlasImageView = objc.IBOutlet()
#     
#     def awakeFromNib(self):
#         for k in cfg.atlasSliceLocations.keys()[1:-1]:
#             f = u"%s/%03.i.eps" % (cfg.atlasImagesDir, k)
#             #print f
#             self._.atlasImages[k] = NSImage.alloc().initWithContentsOfFile_(f)
#             self._.atlasImages[k].setSize_((668,481))
#             #print self.atlasImages[k]
#         #print k
#         imageSize = self.atlasImages[k].size()
#         #print imageSize
#         #self.viewImage = NSImage.alloc().initWithSize_(imageSize)
#         self.viewImage = NSImage.alloc().initWithSize_((668,481))
#         print self.viewImage.size()
#         #atlasSliceLocations.keys()
#         self._.ocFigureIndex = 106 - int(cfg.defaultAtlasImage.split('.')[0])
#         self.pathParams = None
#         self.regenerate_view_image()
#     
#     def update_electrode(self):
#         # self.pathParams have changes, so
#         # update overlay image
#         # regenerate final image
#         #self.regenerate_final_image()
#         #self.positionChanged_(None)
#         self.regenerate_view_image()
#     
#     @IBAction
#     def positionChanged_(self, sender):
#         if self.ocFigureIndex == None:
#             return
#         # the position of the ap-slider and ocFigureIndex has changed
#         # TODO do I need to double check that this actually changed?
#         #print self.ocFigureIndex
#         # update atlasImage
#         #self._.atlasImage = NSImage.alloc().initWithContentsOfFile_(u"%s/%03.i.eps" % (cfg.atlasImagesDir, 106 - self.ocFigureIndex))
#         # regenerate final image
#         #self.regenerate_final_image()
#         #self.atlasImageView.setImage_(self.viewImage)
#         self.regenerate_view_image()
#         return
#         
#         # free old image ?
#         #self.atlasImage.dealloc()
#         #print self.ocFigureIndex
#         
#         s = time.time()
#         self._.atlasImage = NSImage.alloc().initWithContentsOfFile_(u"%s/%03.i.eps" % (cfg.atlasImagesDir, 106 - self.ocFigureIndex))
#         e = time.time()
#         print "loading image:", e - s
#         s = time.time()
#         self.draw_electrode()
#         e = time.time()
#         print "drawing electrode:", e - s
#         # need to call this to actually have the display update
#         s = time.time()
#         self.atlasImageView.setImage_(self.atlasImage)
#         e = time.time()
#         print "setting image:", e - s
#         #self.atlasImageView.setNeedsDisplay_(True)
#     
#     def regenerate_view_image(self):
#         if self.viewImage == None:
#             return
#         sectionIndex = 106 - self.ocFigureIndex
#         # copy current atlas image to view image
#         #self.viewImage <- self.atlasImages[sectionIndex]
#         r = self.atlasImages[sectionIndex].bestRepresentationForRect_context_hints_(((0,0),self.viewImage.size()), None, None)
#         r.setSize_((668,481))
#         #print "Tring to draw...",
#         # The fucking piece of shit crapple documentation says I shouldn't call this method... thanks.
#         #print self.viewImage.drawRepresentation_inRect_(r, ((0,0),self.viewImage.size()))
#         
#         # draw electrode
#         self.draw_electrode()
#         
#         # update atlas image view (might be a quicker way to do this)
#         #self.atlasImageView.setImage_(self.viewImage)
#         self.atlasImageView.setNeedsDisplay_(TRUE)
#     
#     # go to tip location
#     @IBAction
#     def goToTipLocation_(self, sender):
#         if self.controller.ocFramesStatus != 3:
#             return
#         
#         # find location of tip
#         tip = numpy.ones(4,dtype=numpy.float64)
#         tip[:3] = self.controller.cnc.get_tip_position_on_arm()
#         tip = self.controller.fManager.transform_point(tip, "cnc", "skull")[0]
#         
#         # find which picture contains the tip
#         for k, v in cfg.atlasSliceLocations.iteritems():
#             if tip[1] <= v and tip[1] >= (v - cfg.atlasSliceThickness):
#                 # go to this slice
#                 self._.ocFigureIndex = 106 - k
#     
#     def mm_to_canvas(self, image, sectionIndex, ml,dv):
#         # where: +ml = right, dv+ = down
#         # ml range +- 8
#         # dv range +11
#         if sectionIndex >= 103:
#             # 103 and up dv goes -1 to -12 not 0 to -11
#             dv = dv + 1.
#         
#         w = image.size().width
#         h = image.size().height
#         
#         x = ml * w/16.0 + w/2.0
#         y = h + h/11.0 * dv
#         return x,y
#     
#     def draw_line(self, fromPoint, toPoint, color=NSColor.blackColor(), width=2.0):
#         p = NSBezierPath.alloc().init()
#         p.setLineWidth_(width)
#         p.moveToPoint_(fromPoint)
#         p.lineToPoint_(toPoint)
#         color.set()
#         p.stroke()
# 
#     def draw_circle(self, center, radius, color=NSColor.blackColor()):
#         p1 = (center[0] - radius, center[1] - radius)
#         p2 = (radius * 2., radius * 2.)
#         p = NSBezierPath.bezierPathWithOvalInRect_((p1,p2))
#         color.set()
#         p.fill()
#     
#     def draw_atlas_location(self, image, sectionIndex, ml, ap, dv, apMin, apMax, radius=2.5, color=NSColor.blackColor()):
#         if ap <= apMax and ap >= apMin:
#             self.draw_circle(self.mm_to_canvas(image, sectionIndex, ml, dv), radius, color)
#     
#     # draw electrode (if pipeline is complete)
#     def draw_electrode(self):
#         sectionIndex = 106 - self.ocFigureIndex
#         #print "drawing atlas"
#         # check if path has been measured
#         if self.pathParams == None:
#             return
#         
#         # get size of canvas
#         # self.mm_to_canvas(image, sectionIndex, ml, dv)
#         
#         self.viewImage.lockFocus()
#         
#         # set culling distances
#         apMax = cfg.atlasSliceLocations[sectionIndex]
#         apMin = apMax - cfg.atlasSliceThickness        
#         
#         # drawing tests
#         #draw_line(mm_to_canvas(0.0,-1.0),mm_to_canvas(1.0,-2.0),NSColor.greenColor(),4)
#         #draw_circle(mm_to_canvas(1.0,-2.0),20,NSColor.blueColor())
#         
#         ##  TODO green for actual probe
#         #armOffset = self.controller.cnc.arm_length + self.controller.ocW
#         #armAngle = self.controller.ocB
#         
#         # draw path in red
#         o = numpy.array([self.pathParams[0], self.pathParams[1], self.pathParams[2]])
#         m = numpy.array([self.pathParams[3], self.pathParams[4], self.pathParams[5]])
#         # test if m and n=[0, 1, 0] are parallel: dot(m,n) == 0
#         n = numpy.array([0.,-1.,0.])
#         d = numpy.dot(n,m)
#         if d != 0.:
#             # calculate intersection at ap min
#             w = o - numpy.array([0., apMin, 0.])
#             sMin = -numpy.dot(n,w) / d
#             pMin = o + m * sMin
#             # calculate intersection at ap max
#             w = o - numpy.array([0., apMax, 0.])
#             sMax = -numpy.dot(n,w) / d
#             pMax = o + m * sMax
#             # draw line
#             self.draw_line(self.mm_to_canvas(self.viewImage, sectionIndex, pMin[0], pMin[2]),
#                         self.mm_to_canvas(self.viewImage, sectionIndex, pMax[0], pMax[2]),NSColor.redColor(),4)
#         
#         # draw tip in black
#         tip = o + self.controller.ocW * m
#         
#         self.draw_atlas_location(self.viewImage, sectionIndex, tip[0], tip[1], tip[2], apMin, apMax ,color=NSColor.blackColor())
#         #draw_circle(mm_to_canvas(tip[0],tip[2]),5,NSColor.blackColor())
#         
#         # draw pads in blue
#         pads = []
#         for dw in xrange(32):
#             w = dw * 0.1 + .05 + self.controller.ocW
#             pads.append(o + w * m)
#         for pad in pads:
#             self.draw_atlas_location(self.viewImage, sectionIndex, pad[0], pad[1], pad[2], apMin, apMax, color=NSColor.blueColor())
#             #draw_circle(mm_to_canvas(pad[0],pad[2]),5,NSColor.blueColor())
#         
#         # draw ref in green
#         ref = o + (self.controller.ocW + 3.650) * m
#         self.draw_atlas_location(self.viewImage, sectionIndex, ref[0], ref[1], ref[2], apMin, apMax, color=NSColor.greenColor())
#         #draw_circle(mm_to_canvas(ref[0],ref[2]),5,NSColor.greenColor())
#         
#         # get electrode tip location in black
#         #tip = numpy.ones(4,dtype=numpy.float64)
#         #tip[:3] = self.controller.cnc.get_tip_position_on_arm()
#         #tip = self.controller.fManager.transform_point(tip, "cnc", "skull")[0]
#         #  small black circle for tip
#         #if tip[1] <= apMax and tip[1] >= apMin:
#         #    draw_circle(mm_to_canvas(tip[0],tip[2]),10,NSColor.blackColor())
#         
#         #  small red circles for each pad location
#         #for padOffset in cfg.electrodePadOffsets:
#         #    pad = numpy.ones(4,dtype=numpy.float64)
#         #    pad[:3] = self.controller.cnc.get_position_on_arm(armAngle, armOffset + padOffset)
#         #    pad = self.controller.fManager.transform_point(tip, "cnc", "skull")[0]
#         #    if pad[1] <= apMax and pad[1] >=apMin:
#         #        draw_circle(mm_to_canvas(pad[0],pad[2]),10,NSColor.redColor())
#             
#         
#         #  small blue circle for ref pad
#         #ref = numpy.ones(4,dtype=numpy.float64)
#         #ref[:3] = self.controller.cnc.get_position_on_arm(armAngle, armOffset + cfg.electrodeRefOffset)
#         #ref = self.controller.fManager.transform_point(ref, "cnc", "skull")[0]
#         #if ref[1] < apMax and ref[1] >= apMin:
#         #    draw_circle(mm_to_canvas(ref[0],ref[2]),10,NSColor.blueColor())
#         
#         self.viewImage.unlockFocus()
#     
#     # TODO ability to 'log' position
#     @IBAction
#     def saveAtlasImage_(self, sender):
#         panel = NSSavePanel.savePanel()
#         panel.setCanChooseDirectories_(NO)
#         panel.setCanChooseFiles_(YES)
#         panel.setAllowsMultipleSelection_(NO)
#         panel.setRequiredFileType_('png')
#         panel.setAllowsOtherFileTypes_(YES)
#         
#         def url_to_string(url):
#             return str(url)[16:]
#         
#         panel.setTitle_("Save atlas image (png) as...")
#         retValue = panel.runModal()
#         logDir = ""
#         if retValue:
#             filepath = url_to_string(panel.URLs()[0])
#         else:
#             print "Log directory selection canceled"
#             return
#         
#         ## save as pdf (image doesn't appear to stay a vector graphic after drawing)
#         #data = self.atlasImageView.dataWithPDFInsideRect_(self.atlasImageView.bounds())
#         #data.writeToFile_atomically_("/Users/graham/Desktop/cnc_snapshot.pdf", False)
#         
#         # save as png
#         self.viewImage.lockFocus()
#         image_rep = NSBitmapImageRep.alloc().initWithFocusedViewRect_(((0,0),self.viewImage.size()))
#         self.viewImage.unlockFocus()
#         data = image_rep.representationUsingType_properties_(NSPNGFileType, None)
#         data.writeToFile_atomically_(filepath, False) 