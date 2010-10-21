#!/usr/bin/env python

import numpy

from electrodeController import cfg
from electrodeController import vector

from Foundation import *
from AppKit import *
import objc
from objc import IBAction, IBOutlet

class OCAtlasView (NSObject):
    atlasImage = NSImage.alloc().initWithContentsOfFile_(u"%s/%s" % (cfg.atlasImagesDir, cfg.defaultAtlasImage))
    ocFigureIndex = objc.ivar(u"ocFigureIndex")
    controller = objc.IBOutlet()
    atlasImageView = objc.IBOutlet()
    
    def awakeFromNib(self):
        self._.ocFigureIndex = 106 - int(cfg.defaultAtlasImage.split('.')[0])
        self.pathParams = None
        pass
    
    def updateView(self):
        #self.atlasImageView.setNeedsDisplay_(True)
        self.positionChanged_(None)
    
    @IBAction
    def positionChanged_(self, sender):
        if self.ocFigureIndex == None:
            return
        # free old image ?
        #self.atlasImage.dealloc()
        #print self.ocFigureIndex
        
        self._.atlasImage = NSImage.alloc().initWithContentsOfFile_(u"%s/%03.i.eps" % (cfg.atlasImagesDir, 106 - self.ocFigureIndex))
        self.draw_electrode()
        # need to call this to actually have the display update
        self.atlasImageView.setImage_(self.atlasImage)
        #self.atlasImageView.setNeedsDisplay_(True)
    
    # go to tip location
    @IBAction
    def goToTipLocation_(self, sender):
        if self.controller.ocFramesStatus != 3:
            return
        
        # find location of tip
        tip = numpy.ones(4,dtype=numpy.float64)
        tip[:3] = self.controller.cnc.get_tip_position_on_arm()
        tip = self.controller.fManager.transform_point(tip, "cnc", "skull")[0]
        
        # find which picture contains the tip
        for k, v in cfg.atlasSliceLocations.iteritems():
            if tip[1] <= v and tip[1] >= (v - cfg.atlasSliceThickness):
                # go to this slice
                self._.ocFigureIndex = 106 - k
    
    # draw electrode (if pipeline is complete)
    def draw_electrode(self):
        sectionIndex = 106 - self.ocFigureIndex
        #print "drawing atlas"
        # check if path has been measured
        if self.pathParams == None:
            return
        
        # get size of canvas
        def mm_to_canvas(ml,dv):
            # where: +ml = right, dv+ = down
            # ml range +- 8
            # dv range +11
            if sectionIndex >= 103:
                # 103 and up dv goes -1 to -12 not 0 to -11
                dv = dv + 1.
            
            w = self.atlasImage.size().width
            h = self.atlasImage.size().height
            
            x = ml * w/16.0 + w/2.0
            y = h + h/11.0 * dv
            return x,y
        
        self._.atlasImage.lockFocus()
        
        def draw_line(fromPoint,toPoint, color=NSColor.blackColor(), width=2.0):
            p = NSBezierPath.alloc().init()
            p.setLineWidth_(width)
            p.moveToPoint_(fromPoint)
            p.lineToPoint_(toPoint)
            color.set()
            p.stroke()
        
        def draw_circle(center, radius, color=NSColor.blackColor()):
            p1 = (center[0] - radius, center[1] - radius)
            p2 = (radius * 2., radius * 2.)
            p = NSBezierPath.bezierPathWithOvalInRect_((p1,p2))
            color.set()
            p.fill()
        
        
        # set culling distances
        apMax = cfg.atlasSliceLocations[sectionIndex]
        apMin = apMax - cfg.atlasSliceThickness        
        
        
        def draw_atlas_location(ml, ap, dv, radius=2.5, color=NSColor.blackColor()):
            if ap <= apMax and ap >= apMin:
                draw_circle(mm_to_canvas(ml, dv), radius, color)
        
        # drawing tests
        #draw_line(mm_to_canvas(0.0,-1.0),mm_to_canvas(1.0,-2.0),NSColor.greenColor(),4)
        #draw_circle(mm_to_canvas(1.0,-2.0),20,NSColor.blueColor())
        
        ##  TODO green for actual probe
        #armOffset = self.controller.cnc.arm_length + self.controller.ocW
        #armAngle = self.controller.ocB
        
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
            draw_line(mm_to_canvas(pMin[0],pMin[2]),mm_to_canvas(pMax[0],pMax[2]),NSColor.redColor(),4)
        
        # draw tip in black
        tip = o + self.controller.ocW * m
        draw_atlas_location(tip[0],tip[1],tip[2],color=NSColor.blackColor())
        #draw_circle(mm_to_canvas(tip[0],tip[2]),5,NSColor.blackColor())
        
        # draw pads in blue
        pads = []
        for dw in xrange(32):
            w = dw * 0.1 + .05 + self.controller.ocW
            pads.append(o + w * m)
        for pad in pads:
            draw_atlas_location(pad[0],pad[1],pad[2],color=NSColor.blueColor())
            #draw_circle(mm_to_canvas(pad[0],pad[2]),5,NSColor.blueColor())
        
        # draw ref in green
        ref = o + (self.controller.ocW + 3.650) * m
        draw_atlas_location(ref[0],ref[1],ref[2],color=NSColor.greenColor())
        #draw_circle(mm_to_canvas(ref[0],ref[2]),5,NSColor.greenColor())
        
        # get electrode tip location in black
        #tip = numpy.ones(4,dtype=numpy.float64)
        #tip[:3] = self.controller.cnc.get_tip_position_on_arm()
        #tip = self.controller.fManager.transform_point(tip, "cnc", "skull")[0]
        #  small black circle for tip
        #if tip[1] <= apMax and tip[1] >= apMin:
        #    draw_circle(mm_to_canvas(tip[0],tip[2]),10,NSColor.blackColor())
        
        #  small red circles for each pad location
        #for padOffset in cfg.electrodePadOffsets:
        #    pad = numpy.ones(4,dtype=numpy.float64)
        #    pad[:3] = self.controller.cnc.get_position_on_arm(armAngle, armOffset + padOffset)
        #    pad = self.controller.fManager.transform_point(tip, "cnc", "skull")[0]
        #    if pad[1] <= apMax and pad[1] >=apMin:
        #        draw_circle(mm_to_canvas(pad[0],pad[2]),10,NSColor.redColor())
            
        
        #  small blue circle for ref pad
        #ref = numpy.ones(4,dtype=numpy.float64)
        #ref[:3] = self.controller.cnc.get_position_on_arm(armAngle, armOffset + cfg.electrodeRefOffset)
        #ref = self.controller.fManager.transform_point(ref, "cnc", "skull")[0]
        #if ref[1] < apMax and ref[1] >= apMin:
        #    draw_circle(mm_to_canvas(ref[0],ref[2]),10,NSColor.blueColor())
        
        self._.atlasImage.unlockFocus()
    
    # TODO ability to 'log' position
    @IBAction
    def saveAtlasImage_(self, sender):
        panel = NSSavePanel.savePanel()
        panel.setCanChooseDirectories_(NO)
        panel.setCanChooseFiles_(YES)
        panel.setAllowsMultipleSelection_(NO)
        panel.setRequiredFileType_('png')
        panel.setAllowsOtherFileTypes_(YES)
        
        def url_to_string(url):
            return str(url)[16:]
        
        panel.setTitle_("Save atlas image (png) as...")
        retValue = panel.runModal()
        logDir = ""
        if retValue:
            filepath = url_to_string(panel.URLs()[0])
        else:
            print "Log directory selection canceled"
            return
        
        ## save as pdf (image doesn't appear to stay a vector graphic after drawing)
        #data = self.atlasImageView.dataWithPDFInsideRect_(self.atlasImageView.bounds())
        #data.writeToFile_atomically_("/Users/graham/Desktop/cnc_snapshot.pdf", False)
        
        # save as png
        self.atlasImage.lockFocus()
        image_rep = NSBitmapImageRep.alloc().initWithFocusedViewRect_(((0,0),self.atlasImage.size()))
        self.atlasImage.unlockFocus()
        data = image_rep.representationUsingType_properties_(NSPNGFileType, None)
        data.writeToFile_atomically_(filepath, False) 