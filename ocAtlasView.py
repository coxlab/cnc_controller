#!/usr/bin/env python


import numpy

from electrodeController import cfg

from Foundation import *
from AppKit import *
import objc

from glZoomView import ZoomView
from ocZoomView import OCZoomView

from OpenGL.GL import *
from OpenGL.GLUT import *


class OCAtlasView (OCZoomView):
    #ocFigureIndex = objc.ivar(u"ocFigureIndex")
    controller = objc.IBOutlet()
    atlasImages = NSMutableDictionary.alloc().init()
    #ocTipOffset = objc.ivar(u"ocTipOffset")

    def awakeFromNib(self):
        self.gl_inited = False

        ZoomView.__init__(self)

        self.add_key_binding('z', 'zoom_in')
        self.add_key_binding('x', 'zoom_out')
        self.add_key_binding('c', 'increase_contrast')
        self.add_key_binding('C', 'decrease_contrast')
        self.add_key_binding('r', 'reset_contrast')

        # make sure that the mouse is IN before passing on events
        self.mouseIsIn = True

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
        self.sectionIndex = cfg.defaultAtlasImage
        self.pathParams = None
        #self.regenerate_view_image()
        self.set_image_from_nsimage(self.atlasImages[cfg.defaultAtlasImage])

    def set_image_from_nsimage(self, nsimage):
        self.openGLContext().makeCurrentContext()
        self.imageSize = (nsimage.size()[0], nsimage.size()[1])
        frame = self.frame()
        self.scale = max(frame.size.width / float(self.imageSize[0]), \
                frame.size.height / float(self.imageSize[1]))
        # convert nsimage to string
        nsimage.lockFocus()
        nsimage.setBackgroundColor_(NSColor.whiteColor())
        self.imageData = str( \
                NSBitmapImageRep.alloc().initWithFocusedViewRect_(((0, 0), \
                nsimage.size())).bitmapData())
        nsimage.unlockFocus()

        glEnable(GL_TEXTURE_2D)
        if self.imageTexture != None:
            glDeleteTextures(self.imageTexture)
        self.imageTexture = glGenTextures(1)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(1., 1., 1., 1.)
        glBindTexture(GL_TEXTURE_2D, self.imageTexture)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.imageSize[0], \
                self.imageSize[1], 0, GL_RGBA, GL_UNSIGNED_BYTE, \
                self.imageData)  # RADAR GL_UNSIGNED_BYTE may be wrong
        glBindTexture(GL_TEXTURE_2D, 0)

        # load texture from stringf
        #self.load_texture_from_string(str(image_rep.bitmapData()))
        print len(self.imageData), self.imageSize[0] * self.imageSize[1] * 4
        self.scheduleRedisplay()

    @objc.IBAction
    def saveAtlasImage_(self, sender):
        pass

    @objc.IBAction
    def positionChanged_(self, sender):
        #print "position changed:", sender.intValue()
        self.sectionIndex = 106 - sender.intValue()
        self.set_image_from_nsimage(self.atlasImages[self.sectionIndex])

    def rightMouseUp_(self, event):
        x, y = self.oc_to_gl( \
                self.convertPoint_fromView_(event.locationInWindow(), None))

        if event.modifierFlags() & NSShiftKeyMask:
            #print "trying to find zoom to delete"
            d, i = self.find_closest_zoom_distance( \
                    x / self.scale, y / self.scale)
            #print "attempting to delete:", i, "at", d
            if i != -1:
                #print "removing zoom here"
                self.zooms.remove(self.zooms[i])
                if self.selectedZoom >= i:
                    self.selectedZoom -= 1
                ##print "removing zoom there"
        else:
            self.add_zoomed_area(x / self.scale, y / self.scale)

        self.process_mouse(GLUT_RIGHT_BUTTON, GLUT_DOWN, x, y)
        #self.otherView.scheduleRedisplay()
        self.scheduleRedisplay()

    def mm_to_canvas(self, x, y):
        if self.sectionIndex >= 103:
            y = y + 1.
        return x / 8., y / 5.5 + 1.

    def draw_electrode(self):
        # opengl coordinates: +1 (right) +1 (up) -1(left) -1(down)
        # atlas coordinates: + (right) - (left) 0(top) -(down)
        #sectionIndex = 106 - self.ocFigureIndex
        # check if path has been measured
        #print "pathParams in draw_electrode", self.pathParams
        if self.pathParams == None:
            #print "not drawing electrode"
            return
        #print "drawing electrode"

        # set culling distances
        apMax = cfg.atlasSliceLocations[self.sectionIndex]
        apMin = apMax - cfg.atlasSliceThickness

        # draw path in red
        o = numpy.array([self.pathParams[0], self.pathParams[1], \
                self.pathParams[2]])
        m = numpy.array([self.pathParams[3], self.pathParams[4], \
                self.pathParams[5]])
        # test if m and n=[0, 1, 0] are parallel: dot(m,n) == 0
        n = numpy.array([0., -1., 0.])
        d = numpy.dot(n, m)
        if d != 0.:
            # calculate intersection at ap min
            w = o - numpy.array([0., apMin, 0.])
            sMin = -numpy.dot(n, w) / d
            pMin = o + m * sMin
            # calculate intersection at ap max
            w = o - numpy.array([0., apMax, 0.])
            sMax = -numpy.dot(n, w) / d
            pMax = o + m * sMax
            print "atlas view line min and max t:", sMin, sMax
            if sMin < sMax:
                if sMin < -50.:
                    if sMax < -50.:
                        # don't draw
                        pass
                    else:
                        # cap sMin
                        sMin = -50.
                        pMin = o + m * sMin
                        glColor(1., 0., 0., 1.)
                        glLineWidth(2.)
                        glBegin(GL_LINES)
                        glVertex2f(*self.mm_to_canvas(pMin[0], pMin[2]))
                        glVertex2f(*self.mm_to_canvas(pMax[0], pMax[2]))
                        glEnd()
                else:
                    # draw
                    glColor(1., 0., 0., 1.)
                    glLineWidth(2.)
                    glBegin(GL_LINES)
                    glVertex2f(*self.mm_to_canvas(pMin[0], pMin[2]))
                    glVertex2f(*self.mm_to_canvas(pMax[0], pMax[2]))
                    glEnd()
            elif sMax < sMin:
                if sMax < -50.:
                    if sMin < -50.:
                        # don't draw
                        pass
                    else:
                        # cap sMax
                        sMax = -50.
                        pMax = o + m * sMax
                        glColor(1., 0., 0., 1.)
                        glLineWidth(2.)
                        glBegin(GL_LINES)
                        glVertex2f(*self.mm_to_canvas(pMin[0], pMin[2]))
                        glVertex2f(*self.mm_to_canvas(pMax[0], pMax[2]))
                        glEnd()
                else:
                    # draw
                    glColor(1., 0., 0., 1.)
                    glLineWidth(2.)
                    glBegin(GL_LINES)
                    glVertex2f(*self.mm_to_canvas(pMin[0], pMin[2]))
                    glVertex2f(*self.mm_to_canvas(pMax[0], pMax[2]))
                    glEnd()
            # draw line

        # draw tip in black
        tip = o + self.controller.ocW * m

        if tip[1] <= apMax and tip[1] >= apMin:
            glColor(0., 0., 0., 1.)
            glPointSize(5)
            glBegin(GL_POINTS)
            glVertex2f(*self.mm_to_canvas(tip[0], tip[2]))
            glEnd()

        # draw pads in blue
        pads = []
        for dw in xrange(32):
            w = dw * 0.1 + .05 + self.controller.ocW + \
                    self.controller.ocTipOffset
            pads.append(o + w * m)
        for pad in pads:
            if pad[1] <= apMax and pad[1] >= apMin:
                glColor(0., 0., 1., 1.)
                glPointSize(5)
                glBegin(GL_POINTS)
                glVertex2f(*self.mm_to_canvas(pad[0], pad[2]))
                glEnd()

        # draw ref in green
        ref = o + (self.controller.ocW + 3.650 + \
                self.controller.ocTipOffset) * m
        if ref[1] <= apMax and ref[1] >= apMin:
            glColor(0., 1., 0., 1.)
            glPointSize(5)
            glBegin(GL_POINTS)
            glVertex2f(*self.mm_to_canvas(ref[0], ref[2]))
            glEnd()

    def drawRect_(self, frame):
        #print "in drawRect", self.pathParams
        if not self.canDraw():
            #print "couldn't draw"
            return

        if self.gl_inited == False:
            #print "gl not inited"
            self.initGL()

        #print "clearing"
        glClearColor(1., 1., 1., 1.)
        glClear(GL_COLOR_BUFFER_BIT)

        #print "getting frame"
        frame = self.frame()
        self.frame_width = frame.size.width
        self.frame_height = frame.size.height
        glViewport(0, 0, int(self.frame_width), int(self.frame_height))

        # draw zoom view
        #print "drawing"
        self.draw()
        self.draw_electrode()

        #print "flushing"
        self.openGLContext().flushBuffer()
