#!/usr/bin/env python

import numpy

import electrodeController.cfg as cfg

from Foundation import *
from AppKit import *
import objc
from objc import IBAction, IBOutlet

import electrodeController.controller

# TODO when linear axes are moved, invalidate camera to cnc transform

class OCController (NSObject, electrodeController.controller.Controller):
    ocAP = objc.ivar(u"ocAP")
    ocML = objc.ivar(u"ocML")
    ocDV = objc.ivar(u"ocDV")
    ocAngle = objc.ivar(u"ocAngle")
    ocDepth = objc.ivar(u"ocDepth")
    
    ocX = objc.ivar(u"ocX")
    ocY = objc.ivar(u"ocY")
    ocZ = objc.ivar(u"ocZ")
    ocW = objc.ivar(u"ocW")
    ocB = objc.ivar(u"ocB")
    
    #framesDisplay = objc.IBOutlet()
    framesStatus = objc.ivar(u"framesStatus")
    
    meshView = objc.IBOutlet()
    
    depthTargetField = objc.IBOutlet()
    depthVelocityField = objc.IBOutlet() # TODO this duplicates bVelocityField, how do I link them?
    depthLevelIndicator = objc.IBOutlet()
    
    targetDVField = objc.IBOutlet()
    targetMLField = objc.IBOutlet()
    targetAPField = objc.IBOutlet()
    targetAngleField = objc.IBOutlet()
    
    wAxisMoverWindow = objc.IBOutlet()
    goToTargetWindow = objc.IBOutlet()
    moveRelativeWindow = objc.IBOutlet()
    
    leftZoomView = objc.IBOutlet()
    rightZoomView = objc.IBOutlet()
    
    motorStatusButton = objc.IBOutlet()
    
    zoomPointsController = objc.IBOutlet()
    zoomPoints = NSMutableArray.array()
    
    xVelocityField = objc.IBOutlet()
    yVelocityField = objc.IBOutlet()
    zVelocityField = objc.IBOutlet()
    wVelocityField = objc.IBOutlet()
    bVelocityField = objc.IBOutlet()
    
    def awakeFromNib(self):
        electrodeController.controller.Controller.__init__(self)
        self.disable_motors()
        
        self.connect_cameras()
        
        if cfg.fakeCameras:
            self.cameras.set_frame_directory(cfg.fakeFramesDir)
        
        self.zoomPoints.append({'c':'r','lx':1024.2244, 'ly': 847.3844, 'rx': 384.3434, 'ry': 0.01121, 'x': 0.43, 'y': 23.33, 'z': 400.4343})
        self.zoomPoints.append({'c':'b','lx':0.0, 'ly':0., 'rx':0., 'ry':0., 'x':0., 'y':0., 'z':0., 'angle':5.0})
        self.zoomPointsController.rearrangeObjects()
        
        # update bindings with correct values
        self.update_frames_display()
        self.update_velocities()
        self.update_position()
    
    @IBAction
    def clearZoomPoints_(self, sender):
        self.zoomPoints.clear()
        self.zoomPointsController.rearrangeObjects()
    
    @IBAction
    def addZoomPoints_(self, sender):
        if len(self.leftZoomView.zooms) != len(self.rightZoomView.zooms):
            print "left and right zoom views must have the same number of points"
            # TODO log error
            return
        for l, r in zip(self.leftZoomView.zooms, self.rightZoomView.zooms):
            newPoint = {'c': l['c'], 'lx': l['x'], 'ly': l['y'], 'rx': r['x'], 'ry': r['y']}
            # check if 3d localization is possible
            if all(self.cameras.get_calibrated) and all(self.cameras.get_located):
                l3d = self.cameras.get_3d_position([ [l['x'],l['y']], [r['x'],r['y']] ])
                newPoint['x'] = l3d[0]
                newPoint['y'] = l3d[1]
                newPoint['z'] = l3d[2]
            newPoint['angle'] = float(self.cnc.headAxes.get_position('b'))
            self.zoomPoints.append(newPoint)
        self.zoomPointsController.rearrangeObjects()
    
    # motor methods
    def enable_motors(self):
        self.cnc.enable_motors()
        self.motorStatusButton.setState_(True)
        self.motorStatusButton.setTitle_('On')
    
    def disable_motors(self):
        self.cnc.disable_motors()
        self.motorStatusButton.setState_(False)
        self.motorStatusButton.setTitle_('Off')
    
    @IBAction
    def toggleMotors_(self, sender):
        if self.motorStatusButton.state(): # off is 1, on is 0
            self.enable_motors()
        else:
            self.disable_motors()
    
    @IBAction
    def loadAnimal_(self, sender):
        panel = NSOpenPanel.openPanel()
        panel.setCanChooseDirectories_(NO)
        panel.setCanChooseFiles_(YES)
        panel.setAllowsMultipleSelection_(NO)
        #panel.setAllowedFileTypes_(['obj'])
        
        def url_to_string(url):
            # TODO make this more robust
            return str(url)[16:]
        
        panel.setTitle_("Select an animal configuration file")
        retValue = panel.runModal()
        animalCfg = ""
        if retValue:
            animalCfg = url_to_string(panel.URLs()[0])
        else:
            print "Mesh selection canceled"
            # TODO log error
            return
        
        #panel.setTitle_("Select a .jpg texture file")
        #panel.setAllowedFileTypes_(['jpg'])
        #retValue = panel.runModal()
        #textureFilename = ""
        #if retValue:
        #    textureFilename = url_to_string(panel.URLs()[0])
        #else:
        #    print "Texture selection canceled"
        #    return
        
        #self.load_mesh("/Users/graham/Repositories/coxlab/structured_light_stereotaxy/software/viewer/example_mesh/mesh.obj",
        #                "/Users/graham/Repositories/coxlab/structured_light_stereotaxy/software/viewer/example_mesh/texture.jpg")
        #self.load_mesh(meshFilename, textureFilename)
        
        self.load_animal(animalCfg)
        #print cfg.animalMesh, cfg.animalTexture
        self.meshView.load_obj(cfg.animalMesh, cfg.animalTexture)
        #self.meshView.load_obj("%s/skull.obj" % cfg.meshDir, "%s/Texture/texture.jpg" % cfg.meshDir)
        self.updateFramesDisplay_(sender)
    
    @IBAction
    def registerCameras_(self, sender):
        # get points from saved points (or zoom view)
        tPoints = []
        for z in self.zoomPoints:
            if all((z.has_key('x'),z.has_key('y'),z.has_key('z'))):
                # point is valid
                tPoints.append([z['x'],z['y'],z['z'],1.])
        
        if len(tPoints) != 3:
            # TODO log error
            print "register_cameras requires exactly 3 valid points"
            return
        
        self.register_cameras(numpy.array(tPoints))
        self.updateFramesDisplay_(sender)
    
    @IBAction
    def registerCNC_(self, sender):
        # get points from saved points and angles
        tPoints = []
        angles = []
        for z in self.zoomPoints:
            if all((z.has_key('x'),z.has_key('y'),z.has_key('z'),z.has_key('angle'))):
                tPoints.append([z['x'],z['y'],z['z'],1.])
                angles.append(numpy.radians(z['angle']))
        
        if len(tPoints) != 3 or len(angles) != 3:
            # TODO log error
            print "register_cnc requires exactly 3 valid points"
            return
        
        self.register_cnc(tPoints, angles)
        self.updateFramesDisplay_(sender)
    
    @IBAction
    def goToTarget_(self, sender):
        raise Exception
        #targetDVField = objc.IBOutlet()
        #targetMLField = objc.IBOutlet()
        #targetAPField = objc.IBOutlet()
        #targetAngleField = objc.IBOutlet()
        pass
    
    @IBAction
    def moveWAxis_(self, sender):
        #depthTargetField = objc.IBOutlet()
        #depthVelocityField = objc.IBOutlet() # TODO this duplicates bVelocityField, how do I link them?
        #depthLevelIndicator = objc.IBOutlet()
        raise Exception
        pass
    
    # ========================= UI related functions ==========================
    
    #@IBAction
    #def toggleGoToTargetVisibility_(self, sender):
    #    if self.goToTargetWindow.isVisible():
    #        self.goToTargetWindow.orderOut_(sender)
    #    else:
    #        self.goToTargetWindow.orderFront_(sender)
    #    #print self.goToTargetWindow.isVisible()
    
    #@IBAction
    #def toggleWAxisMoverVisibility_(self, sender):
    #    if self.wAxisMoverWindow.isVisible():
    #        self.wAxisMoverWindow.orderOut_(sender)
    #    else:
    #        self.wAxisMoverWindow.orderFront_(sender)
    #    #print self.wAxisMoverWindow.isVisible()
    
    #@IBAction
    #def toggleMoveRelativeVisibility_(self, sender):
    #    if self.moveRelativeWindow.isVisible():
    #        self.moveRelativeWindow.orderOut_(sender)
    #    else:
    #        self.moveRelativeWindow.orderFront_(sender)
    #    #print self.moveRelativeWindow.isVisible()
    
    @IBAction
    def setVelocities_(self, sender):
        print "in setVelocities"
        if sender == self.xVelocityField:
            print "was x"
            self.cnc.linearAxes.set_velocity(self.xVelocityField.floatValue(),'x')
        elif sender == self.yVelocityField:
            print "was y"
            self.cnc.linearAxes.set_velocity(self.yVelocityField.floatValue(),'y')
        elif sender == self.zVelocityField:
            print "was z"
            self.cnc.linearAxes.set_velocity(self.zVelocityField.floatValue(),'z')
        elif sender == self.wVelocityField:
            print "was w"
            self.cnc.headAxes.set_velocity(self.wVelocityField.floatValue(),'w')
        elif sender == self.bVelocityField:
            print "was b"
            self.cnc.headAxes.set_velocity(self.bVelocityField.floatValue(),'b')
        elif sender == self.depthVelocityField:
            print "was depth"
            self.cnc.headAxes.set_velocity(self.depthVelocityField.floatValue(),'b')
        else:
            # update all with b having precedent
            self.cnc.linearAxes.set_velocity(self.xVelocityField.floatValue(),'x')
            self.cnc.linearAxes.set_velocity(self.yVelocityField.floatValue(),'y')
            self.cnc.linearAxes.set_velocity(self.zVelocityField.floatValue(),'z')
            self.cnc.headAxes.set_velocity(self.wVelocityField.floatValue(),'w')
            self.cnc.headAxes.set_velocity(self.bVelocityField.floatValue(),'b')
        self.update_velocities()
    
    def update_velocities(self):
        self.xVelocityField.setFloatValue_(float(self.cnc.linearAxes.get_velocity('x')))
        self.yVelocityField.setFloatValue_(float(self.cnc.linearAxes.get_velocity('y')))
        self.zVelocityField.setFloatValue_(float(self.cnc.linearAxes.get_velocity('z')))
        self.wVelocityField.setFloatValue_(float(self.cnc.headAxes.get_velocity('w')))
        
        bVel = float(self.cnc.headAxes.get_velocity('b'))
        self.bVelocityField.setFloatValue_(bVel)
        self.depthVelocityField.setFloatValue_(bVel)
    
    def update_position(self):
        if self.framesStatus == 3: # all frames are a good
            # don't read from linear axes
            cncCoord = numpy.ones(4,dtype=numpy.float64)
            cncCoord[:3] = self.cnc.get_tip_position_on_arm()
            skullCoord = self.fManager.transform_point(cncCoord, "cnc", "skull")
            # ML = X
            self._.ocML = skullCoord[0]
            # AP = Y
            self._.ocAP = skullCoord[1]
            # DV = Z
            self._.ocDV = skullCoord[2]
        self._.ocAngle = float(self.cnc.headAxes.get_position('b'))
        # TODO this should be (target - w) not just w
        self._.ocDepth = float(self.cnc.headAxes.get_position('w'))
        
        self._.ocX = float(self.cnc.linearAxes.get_position('x'))
        self._.ocY = float(self.cnc.linearAxes.get_position('y'))
        self._.ocZ = float(self.cnc.linearAxes.get_position('z'))
        self._.ocB = float(self.cnc.headAxes.get_position('b'))
        self._.ocW = float(self.cnc.headAxes.get_position('w'))
    
    def update_frames_display(self):
        state = 0
        if self.fManager.test_route('skull','tricorner'): state += 1
        if self.fManager.test_route('tricorner','camera'): state += 1
        if self.fManager.test_route('camera','cnc'): state += 1
        self._.framesStatus = state
    
    @IBAction
    def updateFramesDisplay_(self, sender):
        self.update_frames_display()
    
    @IBAction
    def updateZoomViews_(self, sender):
        self.update_zoom_views()
    
    def update_zoom_views(self):
        if not self.cameras.get_connected():
            return
        im0, im1 = self.cameras.capture()
        self.leftZoomView.set_image_from_cv(im0)
        self.rightZoomView.set_image_from_cv(im1)
    
    @IBAction
    def locateCameras_(self, sender):
        ims, s = self.cameras.capture_localization_images(cfg.gridSize)
        
        self.leftZoomView.set_image_from_cv(ims[0])
        self.rightZoomView.set_image_from_cv(ims[1])
        if s == True:
            self.cameras.locate(cfg.gridSize, cfg.gridBlockSize)
        
        located = self.cameras.get_located()
        
        # TODO hook this up to the GUI
        if all(located):
            print "Cameras located"
        else:
            print "Cameras NOT located"