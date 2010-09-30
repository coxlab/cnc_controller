#!/usr/bin/env python

import os

import numpy

from electrodeController import cfg
from electrodeController import vector

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
    
    ocXInc = objc.ivar(u"ocXInc")
    ocYInc = objc.ivar(u"ocYInc")
    ocZInc = objc.ivar(u"ocZInc")
    ocWInc = objc.ivar(u"ocWInc")
    ocBInc = objc.ivar(u"ocBInc")
    
    #framesDisplay = objc.IBOutlet()
    ocFramesStatus = objc.ivar(u"ocFramesStatus")
    
    meshView = objc.IBOutlet()
    tabView = objc.IBOutlet()
    mainWindow = objc.IBOutlet()
    
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
    XMotorStatusButton = objc.IBOutlet()
    YMotorStatusButton = objc.IBOutlet()
    ZMotorStatusButton = objc.IBOutlet()
    WMotorStatusButton = objc.IBOutlet()
    BMotorStatusButton = objc.IBOutlet()
    
    zoomPointsController = objc.IBOutlet()
    zoomPoints = NSMutableArray.array()
    
    xVelocityField = objc.IBOutlet()
    yVelocityField = objc.IBOutlet()
    zVelocityField = objc.IBOutlet()
    wVelocityField = objc.IBOutlet()
    bVelocityField = objc.IBOutlet()
    
    timer = None
    
    def awakeFromNib(self):
        electrodeController.controller.Controller.__init__(self)
        NSApp().setDelegate_(self)
        self.timer = None
        self.disable_motors()
        
        self.connect_cameras()
        
        if cfg.fakeCameras:
            lFileList = ["%s/%s" % (cfg.leftFakeFramesDir, f) for f in os.listdir(cfg.leftFakeFramesDir)]
            self.cameras.cameras[0].set_file_list(lFileList)
            rFileList = ["%s/%s" % (cfg.rightFakeFramesDir, f) for f in os.listdir(cfg.rightFakeFramesDir)]
            self.cameras.cameras[1].set_file_list(rFileList)
        
        self.zoomPoints.append({'c':'r','lx':313.302540599, 'ly': 328.81604072, 'rx': 284.939403378, 'ry': 348.635889153, 'x': -42.3456234131, 'y': -1.78845750399, 'z': -0.641684310712, 'angle': 12.0, 'w':-0.39959})
        self.zoomPoints.append({'c':'r','lx':316.743317476, 'ly': 347.294286908, 'rx': 290.644721184, 'ry': 366.060238127, 'x': -42.2258470538, 'y': -2.87006594517, 'z': -0.795638750719, 'angle': 12.0, 'w': -1.3996})
        self.zoomPoints.append({'c':'r','lx':320.566402894, 'ly': 365.007916012, 'rx': 296.041643433, 'ry': 384.101378216, 'x': -42.0373785465, 'y': -3.94557101801, 'z': -0.784179556811, 'angle': 12.0, 'w': -2.3996})
        self.zoomPoints.append({'c':'r','lx':324.516924493, 'ly': 384.123343103, 'rx': 301.746961238, 'ry': 401.063133854, 'x': -41.9450601303, 'y': -5.03543038535, 'z': -1.04855227966, 'angle': 12.0, 'w': -3.39961})
        self.zoomPoints.append({'c':'r','lx':328.08513755, 'ly': 401.582099846, 'rx': 307.760674601, 'ry': 419.258471721, 'x': -41.7187588127, 'y': -6.11143462708, 'z': -0.970481809585, 'angle': 12.0, 'w': -4.39962})
        self.zoomPoints.append({'c':'r','lx':332.545403871, 'ly': 420.060346034, 'rx': 313.465992407, 'ry': 436.528622917, 'x': -41.5596850022, 'y': -7.19192871413, 'z': -1.10992178527, 'angle': 12.0, 'w': -5.39963})
        self.zoomPoints.append({'c':'r','lx':335.858744567, 'ly': 437.773975138, 'rx': 319.633903548, 'ry': 453.952971891, 'x': -41.3741330393, 'y': -8.25584253428, 'z': -1.13178715622, 'angle': 12.0, 'w': -6.39963})
        self.zoomPoints.append({'c':'r','lx':340.573883249, 'ly': 456.124785145, 'rx': 325.030825797, 'ry': 471.068925308, 'x': -41.2101402046, 'y': -9.32781793284, 'z': -1.25822032043, 'angle': 12.0, 'w': -7.39964})
        
        self.zoomPointsController.rearrangeObjects()
        
        # set default movement increments
        self._.ocXInc = cfg.xInc
        self._.ocYInc = cfg.yInc
        self._.ocZInc = cfg.zInc
        self._.ocBInc = cfg.bInc
        self._.ocWInc = cfg.wInc
        
        # update bindings with correct values
        self.update_frames_display()
        self.update_velocities()
        self.update_position()
        
        #self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(0.5, self, self.update_position, None, True)
        #NSRunLoop.currentRunLoop().addTimer_forMode_(self.timer, NSDefaultRunLoopMode)
        ##NSRunLoop.currentRunLoop().addTimer_forMode_(self.timer, NSEventTrackingRunLoopMode)
    
    def start_update_timer(self):
        if self.timer == None:
            self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(0.5, self, self.update_position, None, True)
            NSRunLoop.currentRunLoop().addTimer_forMode_(self.timer, NSDefaultRunLoopMode)
            #NSRunLoop.currentRunLoop().addTimer_forMode_(self.timer, NSEventTrackingRunLoopMode)
    
    def stop_update_timer(self):
        if self.timer != None:
            self.timer.invalidate()
            self.timer = None
    
    def applicationWillTerminate_(self, sender):
        print "applicationWillTerminate called"
        #self.timer.invalidate()
        self.cleanup()
        #self.cameras.disconnect()
        #self.timer.invalidate()
        self.stop_update_timer()
        print "applicationWillTerminate done"
        
    
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
            if all(self.cameras.get_calibrated()) and all(self.cameras.get_located()):
                l3d = self.cameras.get_3d_position([ [l['x'],l['y']], [r['x'],r['y']] ])
                newPoint['x'] = l3d[0]
                newPoint['y'] = l3d[1]
                newPoint['z'] = l3d[2]
            newPoint['angle'] = float(self.cnc.headAxes.get_position('b')['b'])
            newPoint['w'] = float(self.cnc.headAxes.get_position('w')['w'])#FIXME w axis flip
            self.zoomPoints.append(newPoint)
        self.zoomPointsController.rearrangeObjects()
    
    # motor methods
    def enable_motors(self):
        #self.cnc.enable_motors()
        self.enable_x_motor()
        self.enable_y_motor()
        self.enable_z_motor()
        self.enable_w_motor()
        self.enable_b_motor()
        self.motorStatusButton.setState_(True)
        self.motorStatusButton.setTitle_('Off')
    
    def disable_motors(self):
        self.disable_x_motor()
        self.disable_y_motor()
        self.disable_z_motor()
        self.disable_w_motor()
        self.disable_b_motor()
        #self.cnc.disable_motors()
        self.motorStatusButton.setState_(False)
        self.motorStatusButton.setTitle_('On')
    
    @IBAction
    def toggleMotors_(self, sender):
        if self.motorStatusButton.state(): # off is 1, on is 0
            self.enable_motors()
        else:
            self.disable_motors()
    
    @IBAction
    def loadLog_(self, sender):
        panel = NSOpenPanel.openPanel()
        panel.setCanChooseDirectories_(YES)
        panel.setCanChooseFiles_(NO)
        panel.setAllowsMultipleSelection_(NO)
        #panel.setAllowedFileTypes_(['obj'])
        
        def url_to_string(url):
            return str(url)[16:]
        
        panel.setTitle_("Select the log directory you'd like to replay")
        retValue = panel.runModal()
        logDir = ""
        if retValue:
            logDir = url_to_string(panel.URLs()[0])
        else:
            print "Log directory selection canceled"
            return
        
        # load log directory
        if cfg.fakeCameras:
            lCamDir = logDir + '/camera/0/'
            lFileList = [lCamDir + f for f in os.listdir(lCamDir)]
            self.cameras.cameras[0].set_file_list(lFileList)
            rCamDir = logDir + '/camera/1/'
            rFileList = [rCamDir + f for f in os.listdir(rCamDir)]
            self.cameras.cameras[1].set_file_list(rFileList)
        
        # TODO load frames
        
        self.updateFramesDisplay_(sender)
    
    @IBAction
    def loadAnimal_(self, sender):
        # I need to switch to the mesh view first because of a bug in load_obj that
        # fubars other textures and prevents the obj from loading properly
        self.tabView.selectTabViewItemAtIndex_(1)
        
        
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
        
        self.mainWindow.setTitle_(u"Loading mesh... this may take a while")
        self.mainWindow.setAlphaValue_(0.8)
        
        
        self.load_animal(animalCfg)
        #print cfg.animalMesh, cfg.animalTexture
        self.meshView.load_obj(cfg.animalMesh, cfg.animalTexture)
        #self.meshView.load_obj("%s/skull.obj" % cfg.meshDir, "%s/Texture/texture.jpg" % cfg.meshDir)
        
        self.mainWindow.setAlphaValue_(1.0)
        self.mainWindow.setTitle_(animalCfg)
        self.updateFramesDisplay_(sender)
    
    @IBAction
    def registerCameras_(self, sender):
        # get points from saved points (or zoom view)
        ptsInCam = []
        for z in self.zoomPoints:
            if all((z.has_key('x'),z.has_key('y'),z.has_key('z'))):
                # point is valid
                ptsInCam.append([z['x'],z['y'],z['z'],1.])
        
        if len(ptsInCam) != 3:
            # TODO log error
            print "register_cameras requires exactly 3 valid points"
            return
        
        self.register_cameras(numpy.array(ptsInCam))
        self.updateFramesDisplay_(sender)
    
    @IBAction
    def measurePath_(self, sender):
        ptsInCam = []
        wPositions = []
        for z in self.zoomPoints:
            if all((z.has_key('x'),z.has_key('y'),z.has_key('z'), z.has_key('w'))):
                ptsInCam.append([z['x'],z['y'],z['z']])
                wPositions.append(float(z['w']))
            
        print "going to measure_tip_path in controller"
        self.measure_tip_path(ptsInCam, wPositions)
        self.updateFramesDisplay_(sender)
    
    @IBAction
    def registerCNC_(self, sender):
        # get points from saved points and angles
        ptsInCam = []
        angles = []
        wPositions = []
        
        print '# lx ly rx ry x y z angle w'
        for z in self.zoomPoints:
            print z['lx'], z['ly'], z['rx'], z['ry'], z['x'], z['y'], z['z'], z['angle'], z['w']
        
        for z in self.zoomPoints:
            if all((z.has_key('x'),z.has_key('y'),z.has_key('z'),z.has_key('angle'),z.has_key('w'))):
                ptsInCam.append([z['x'],z['y'],z['z'],1.])
                angles.append(numpy.radians(z['angle']))
                wPositions.append(float(z['w']))
        
        #if len(ptsInCam) != 4 or len(angles) != 4 or len(wPositions) != 4:
        #    # TODO log error
        #    print "register_cnc requires exactly 4 valid points"
        #    return
        
        # TODO check that all ws are the same
        #wPosition = ws[0]
        #for w in ws:
        #    if w != wPosition:
        #        print "register_cnc requires 3 points with the same w position"
        ptsInCam = numpy.array(ptsInCam)
        angles = numpy.array(angles)
        wPositions = numpy.array(wPositions)
        print "going to register_cnc in controller"
        self.register_cnc(ptsInCam, angles, wPositions)
        self.updateFramesDisplay_(sender)
    
    @IBAction
    def goToTarget_(self, sender):
        raise Exception
        #targetDVField = objc.IBOutlet()
        #targetMLField = objc.IBOutlet()
        #targetAPField = objc.IBOutlet()
        #targetAngleField = objc.IBOutlet()
        pass
    
    #@IBAction
    #def moveWAxis_(self, sender):
    #    #depthTargetField = objc.IBOutlet()
    #    #depthVelocityField = objc.IBOutlet() # TODO this duplicates bVelocityField, how do I link them?
    #    #depthLevelIndicator = objc.IBOutlet()
    #    raise Exception
    #    pass
    
    def enable_x_motor(self):
        self.cnc.linearAxes.enable_motor('x')
        self.XMotorStatusButton.setState_(True)
        self.XMotorStatusButton.setTitle_('Off')
    
    def disable_x_motor(self):
        self.cnc.linearAxes.disable_motor('x')
        self.XMotorStatusButton.setState_(False)
        self.XMotorStatusButton.setTitle_('On')
    
    @IBAction
    def toggleXMotor_(self, sender):
        if self.XMotorStatusButton.state(): # off is 1, on is 0
            self.enable_x_motor()
        else:
            self.disable_x_motor()
    
    @IBAction
    def stopXAxis_(self, sender):
        self.cnc.linearAxes.stop_motion('x')
    
    @IBAction
    def moveXAxisLeft_(self, sender):
        self.cnc.linearAxes.move_relative(-self.ocXInc, 'x')
        #self.update_position()
        self.start_update_timer()
    
    @IBAction
    def moveXAxisRight_(self, sender):
        self.cnc.linearAxes.move_relative(self.ocXInc, 'x')
        #self.update_position()
        self.start_update_timer()
    
    def enable_y_motor(self):
        self.cnc.linearAxes.enable_motor('y')
        self.YMotorStatusButton.setState_(True)
        self.YMotorStatusButton.setTitle_('Off')
    
    def disable_y_motor(self):
        self.cnc.linearAxes.disable_motor('y')
        self.YMotorStatusButton.setState_(False)
        self.YMotorStatusButton.setTitle_('On')
    
    @IBAction
    def toggleYMotor_(self, sender):
        if self.YMotorStatusButton.state(): # off is 1, on is 0
            self.enable_y_motor()
        else:
            self.disable_y_motor()
    
    @IBAction
    def stopYAxis_(self, sender):
        self.cnc.linearAxes.stop_motion('y')
    
    @IBAction
    def moveYAxisForward_(self, sender):
        self.cnc.linearAxes.move_relative(self.ocYInc, 'y')
        #self.update_position()
        self.start_update_timer()
    
    @IBAction
    def moveYAxisBack_(self, sender):
        self.cnc.linearAxes.move_relative(-self.ocYInc, 'y')
        #self.update_position()
        self.start_update_timer()
    
    def enable_z_motor(self):
        self.cnc.linearAxes.enable_motor('z')
        self.ZMotorStatusButton.setState_(True)
        self.ZMotorStatusButton.setTitle_('Off')
    
    def disable_z_motor(self):
        self.cnc.linearAxes.disable_motor('z')
        self.ZMotorStatusButton.setState_(False)
        self.ZMotorStatusButton.setTitle_('On')
    
    @IBAction
    def toggleZMotor_(self, sender):
        if self.ZMotorStatusButton.state(): # off is 1, on is 0
            self.enable_z_motor()
        else:
            self.disable_z_motor()
    
    @IBAction
    def stopZAxis_(self, sender):
        self.cnc.linearAxes.stop_motion('z')
    
    @IBAction
    def moveZAxisUp_(self, sender):
        self.cnc.linearAxes.move_relative(-self.ocZInc, 'z')
        #self.update_position()
        self.start_update_timer()
    
    @IBAction
    def moveZAxisDown_(self, sender):
        self.cnc.linearAxes.move_relative(self.ocZInc, 'z')
        #self.update_position()
        self.start_update_timer()
    
    def enable_w_motor(self):
        self.cnc.headAxes.enable_motor('w')
        self.WMotorStatusButton.setState_(True)
        self.WMotorStatusButton.setTitle_('Off')
    
    def disable_w_motor(self):
        self.cnc.headAxes.disable_motor('w')
        self.WMotorStatusButton.setState_(False)
        self.WMotorStatusButton.setTitle_('On')
    
    @IBAction
    def toggleWMotor_(self, sender):
        if self.WMotorStatusButton.state(): # off is 1, on is 0
            self.enable_w_motor()
        else:
            self.disable_w_motor()
    
    @IBAction
    def stopWAxis_(self, sender):
        self.cnc.headAxes.stop_motion('w')
    
    @IBAction
    def moveWAxisUp_(self, sender):
        self.cnc.headAxes.move_relative(self.ocWInc, 'w')
        #self.update_position()
        self.start_update_timer()
    
    @IBAction
    def moveWAxisDown_(self, sender):
        self.cnc.headAxes.move_relative(-self.ocWInc, 'w')
        #self.update_position()
        self.start_update_timer()
    
    def enable_b_motor(self):
        self.cnc.headAxes.enable_motor('b')
        self.BMotorStatusButton.setState_(True)
        self.BMotorStatusButton.setTitle_('Off')
    
    def disable_b_motor(self):
        self.cnc.headAxes.disable_motor('b')
        self.BMotorStatusButton.setState_(False)
        self.BMotorStatusButton.setTitle_('On')
    
    @IBAction
    def toggleBMotor_(self, sender):
        if self.BMotorStatusButton.state(): # off is 1, on is 0
            self.enable_b_motor()
        else:
            self.disable_b_motor()
    
    @IBAction
    def stopBAxis_(self, sender):
        self.cnc.headAxes.stop_motion('b')
    
    @IBAction
    def moveBAxisClockwise_(self, sender):
        self.cnc.headAxes.move_relative(-self.ocBInc, 'b')
        #self.update_position()
        self.start_update_timer()
    
    @IBAction
    def moveBAxisCounterClockwise_(self, sender):
        self.cnc.headAxes.move_relative(self.ocBInc, 'b')
        #self.update_position()
        self.start_update_timer()
    
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
        self.xVelocityField.setFloatValue_(float(self.cnc.linearAxes.get_velocity('x')['x']))
        self.yVelocityField.setFloatValue_(float(self.cnc.linearAxes.get_velocity('y')['y']))
        self.zVelocityField.setFloatValue_(float(self.cnc.linearAxes.get_velocity('z')['z']))
        self.wVelocityField.setFloatValue_(float(self.cnc.headAxes.get_velocity('w')['w']))
        
        bVel = float(self.cnc.headAxes.get_velocity('b')['b'])
        self.bVelocityField.setFloatValue_(bVel)
        self.depthVelocityField.setFloatValue_(bVel)
    
    @IBAction
    def updatePosition_(self, sender):
        self.update_position()
    
    def update_position(self):
        # check if all axes are still, if so, stop timer
        if self.cnc.motion_done():
            self.stop_update_timer()
        
        #print "update_position:", self.ocFramesStatus
        if int(self.ocFramesStatus) == 3: # all frames are mapped
            #print "all frames are good to go"
            # don't read from linear axes
            cncCoord = numpy.ones(4,dtype=numpy.float64)
            cncCoord[:3] = self.cnc.get_tip_position_on_arm()
            skullCoord = self.fManager.transform_point(cncCoord, "cnc", "skull")[0]
            #print "Found skullCoord:", skullCoord
            #print "updating UI"
            # ML = X
            self._.ocML = skullCoord[0]
            # AP = Y
            self._.ocAP = skullCoord[1]
            # DV = Z
            self._.ocDV = skullCoord[2]
            
            
            # TODO update electrode 
            # first apply rotation and translation as specified by tip position
            b = float(self.cnc.headAxes.get_position('b')['b'])
            cncMatrix = vector.transform_to_matrix(cncCoord[0], cncCoord[1], cncCoord[2], 0., numpy.radians(b), 0.)
            # then apply the transform from cnc to skull
            tMatrix = self.fManager.get_transformation_matrix("cnc","skull")
            # TODO check the order of this
            #print "updating mesh view" 
            self.meshView.electrodeMatrix = numpy.matrix(cncMatrix) * numpy.matrix(tMatrix)
            self.meshView.drawElectrode = True
            
            
            self.meshView.scheduleRedisplay()
            #print "skull coordinates updated"
            cfg.log.info('ML:%.3f AP:%.3f DV:%.3f' % (self.ocML, self.ocAP, self.ocDV))
        
        self._.ocAngle = float(self.cnc.headAxes.get_position('b')['b'])
        # TODO this should be (target - w) not just w
        self._.ocDepth = float(self.cnc.headAxes.get_position('w')['w'])#FIXME w axis flip
        
        self._.ocX = float(self.cnc.linearAxes.get_position('x')['x'])
        self._.ocY = float(self.cnc.linearAxes.get_position('y')['y'])
        self._.ocZ = float(self.cnc.linearAxes.get_position('z')['z'])
        self._.ocB = float(self.cnc.headAxes.get_position('b')['b'])
        self._.ocW = float(self.cnc.headAxes.get_position('w')['w'])#FIXME w axis flip
        
        # if the path of the electrode has been fit...
        if self.cnc.pathParams != None:
            # use self.ocW to calculate the position in the camera frame and then map that to skull coordinates
            print "trying to update mesh views pathParams"
            tipPosition = numpy.ones(4,dtype=numpy.float64)
            tipPosition[:3] = self.cnc.calculate_tip_position(self.ocW)
            print tipPosition
            skullCoord = numpy.array(self.fManager.transform_point(tipPosition, "camera", "skull"))[0]
            print skullCoord
            
            # ML = X
            self._.ocML = skullCoord[0]
            # AP = Y
            self._.ocAP = skullCoord[1]
            # DV = Z
            self._.ocDV = skullCoord[2]
            
            # draw the path and position of the electrode
            o = numpy.array(self.cnc.pathParams[:3])
            m = numpy.array(self.cnc.pathParams[3:])
            p1 = numpy.ones(4, dtype=numpy.float64)
            p2 = numpy.ones(4, dtype=numpy.float64)
            p1[:3] = o #- 50.*m
            p2[:3] = o - 50.*m
            
            p1InS = numpy.array(self.fManager.transform_point(p1, "camera", "skull"))[0]
            p2InS = numpy.array(self.fManager.transform_point(p2, "camera", "skull"))[0]
            print p1, p2
            self.meshView.pathParams = [p1[0], p1[1], p1[2], p2[0], p2[1], p2[2]]
            
            #o = numpy.ones(4,dtype=numpy.float64)
            #o[:3] = self.cnc.pathParams[:3]
            #m = numpy.ones(4,dtype=numpy.float64)
            #m[:3] = self.cnc.pathParams[3:]
            #print o, m
            ##o = vector.make_homogeneous(self.cnc.pathParams[:3])
            ##m = vector.make_homogeneous(self.cnc.pathParams[3:])
            #oInS = numpy.array(self.fManager.transform_point(o, "camera", "skull"))[0]
            #mInS = numpy.array(self.fManager.transform_point(m, "camera", "skull"))[0]
            #print oInS, mInS
            #self.meshView.pathParams = [oInS[0], oInS[1], oInS[2], mInS[0], mInS[1], mInS[2]]
            
            # TODO add the rotation as defined by the path etc...
            self.meshView.electrodeMatrix = numpy.matrix(vector.transform_to_matrix(skullCoord[0], skullCoord[1], skullCoord[2], 0., 0., 0.))
            print self.meshView.electrodeMatrix
            self.meshView.drawElectrode = True
            self.meshView.scheduleRedisplay()
            
            cfg.log.info('ML:%.3f AP:%.3f DV:%.3f' % (self.ocML, self.ocAP, self.ocDV))
        
        # logging
        cfg.cncLog.info('X:%.3f Y:%.3f Z:%.3f B:%.3f W:%.3f' % (self.ocX, self.ocY, self.ocZ, self.ocB, self.ocW))
    
    def update_frames_display(self):
        state = 0
        if self.fManager.test_route('skull','tricorner'): state += 1
        if self.fManager.test_route('tricorner','camera'): state += 1
        if self.fManager.test_route('camera','cnc'): state += 1
        self._.ocFramesStatus = state
        #print "Frames state:", state
        if state == 3:
            self.update_position()
    
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
        print ims, s
        self.leftZoomView.set_image_from_cv(ims[0][0])
        self.rightZoomView.set_image_from_cv(ims[1][0])
        print s
        if s == True:
            self.cameras.locate(cfg.gridSize, cfg.gridBlockSize)
        
        located = self.cameras.get_located()
        # TODO hook this up to the GUI
        if all(located):
            print "Cameras located"
            cfg.cameraLog.info('Cameras Located Successfully')
            cfg.cameraLog.info('\tID\t\t\tX\tY\tZ')
            for c in self.cameras.cameras:
                p = c.get_position()
                cfg.cameraLog.info('\t%i\t%.3f\t%.3f\t%.3f' % (c.camID, p[0], p[1], p[2]))
        else:
            print "Cameras NOT located"
            cfg.cameraLog.info('Camera Localization Failed')