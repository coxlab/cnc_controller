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
        self._.ocFigureIndex = int(cfg.defaultAtlasImage.split('.')[0])
        pass
    
    @IBAction
    def positionChanged_(self, sender):
        # free old image ?
        #self.atlasImage.dealloc()
        #print self.ocFigureIndex
        self._.atlasImage = NSImage.alloc().initWithContentsOfFile_(u"%s/%03.i.eps" % (cfg.atlasImagesDir, self.ocFigureIndex))
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
                self._.ocFigureIndex = k
    
    # draw electrode (if pipeline is complete)
    def draw_electrode(self):
        # check if pipeline is full
        if self.controller.ocFramesStatus != 3:
            return
        
        # get size of canvas
        def mm_to_canvas(ml,dv):
            # where: +ml = right, dv+ = down
            # ml range +- 8
            # dv range +11
            if self.ocFigureIndex >= 103:
                # 103 and up dv goes 1-12 not 0-11
                dv = dv - 1.
            
            w = self.atlasImage.size().width
            h = self.atlasImage.size().height
            
            x = ml * w/16.0 + w/2.0
            y = h - h/11.0 * dv
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
        
        # drawing tests
        #draw_line(mm_to_canvas(0.0,1.0),mm_to_canvas(1.0,2.0),NSColor.greenColor(),4)
        #draw_circle(mm_to_canvas(1.0,2.0),20,NSColor.blueColor())
        
        
        # set culling distances
        apMax = cfg.atlasSliceLocations[self.ocFigureIndex]
        apMin = apMax - cfg.atlasSliceThickness
        
        #  TODO green for actual probe
        armOffset = self.controller.cnc.arm_length + self.controller.ocW
        armAngle = self.controller.ocB
        
        # get electrode tip location in black
        tip = numpy.ones(4,dtype=numpy.float64)
        tip[:3] = self.controller.cnc.get_tip_position_on_arm()
        tip = self.controller.fManager.transform_point(tip, "cnc", "skull")[0]
        #  small black circle for tip
        if tip[1] <= apMax and tip[1] >= apMin:
            draw_circle(mm_to_canvas(tip[0],tip[2]),10,NSColor.blackColor())
        
        #  small red circles for each pad location
        for padOffset in cfg.electrodePadOffsets:
            pad = numpy.ones(4,dtype=numpy.float64)
            pad[:3] = self.controller.cnc.get_position_on_arm(armAngle, armOffset + padOffset)
            pad = self.controller.fManager.transform_point(tip, "cnc", "skull")[0]
            if pad[1] <= apMax and pad[1] >=apMin:
                draw_circle(mm_to_canvas(pad[0],pad[2]),10,NSColor.redColor())
            
        
        #  small blue circle for ref pad
        ref = numpy.ones(4,dtype=numpy.float64)
        ref[:3] = self.controller.cnc.get_position_on_arm(armAngle, armOffset + cfg.electrodeRefOffset)
        ref = self.controller.fManager.transform_point(ref, "cnc", "skull")[0]
        if ref[1] < apMax and ref[1] >= apMin:
            draw_circle(mm_to_canvas(ref[0],ref[2]),10,NSColor.blueColor())
        
        #  TODO red for forward path
        
        self._.atlasImage.unlockFocus()
    
    # TODO ability to 'log' position
    @IBAction
    def savePosition_(self, sender):
        pass