#!/usr/bin/env python

import os

import numpy

import cfg
import fiveAxisCNC
import frameManager
import vector
if cfg.fakeCameras:
    from cameraPair import FakeCameraPair as CameraPair
else:
    from cameraPair import CameraPair

# if cfg.useManualImageProcessor:
#     import manualImageProcessing as imageProcessing
# else:
#     import autoImageProcessing as imageProcessing

#TODO
# - collision detection with mesh
# - logging

class Controller:
    def __init__(self):
        self.fManager = frameManager.FrameManager(['skull', 'tricorner', 'camera', 'cnc'])
        self.cnc = fiveAxisCNC.FiveAxisCNC()
        self.cameras = CameraPair(cfg.camIDs)
        self.animal = None
        #self.imageProcessor = imageProcessing.Processor(self.cameras)
    
    
    def load_animal(self, animalCfgFile):
        # load animal configuration file
        if os.path.exists(animalCfgFile):
            cfg.load_external_cfg(animalCfgFile)
        
        # TODO load animal mesh (for collision detection and viewing)
        
        # load skull-to-tricorner transformation matrix and add to frameStack
        self.fManager.add_transformation_matrix('skull', 'tricorner', numpy.matrix(numpy.loadtxt(cfg.skullToTCMatrixFile)))
    
    
    def connect_cameras(self):
        # check if cameras are connected, if not, connect
        if not all(self.cameras.get_connected()):
            self.cameras.connect()
        
        # check if cameras are calibrated, if not, load calibration
        if not all(self.cameras.get_calibrated()):
            self.cameras.load_calibrations(cfg.calibrationDirectory)
    
    def register_cameras(self, ptsInCamera):
        # # find location of 3 tricorner reference points
        # #  - homogenous points
        # #  - ordered from left to right as seen from cameras
        # tPoints = self.imageProcessor.find_tricorner_registration_points()
        # 
        # calculate transformation matrix and add to frameStack
        ptsInTC = cfg.tcRegPoints
        tcToCam = vector.calculate_rigid_transform(ptsInTC,ptsInCamera)
        cfg.framesLog.info('Registering cameras with points in (tcFrame, camera):')
        cfg.framesLog.info(ptsInTC)
        cfg.framesLog.info(ptsInCamera)
        self.fManager.add_transformation_matrix('tricorner', 'camera', tcToCam)
    
    
    def register_cnc(self, ptsInCamera, angles, wPosition):
        r = self.cnc.calculate_arm_length(ptsInCamera, wPosition) + wPosition
        cfg.cncLog.info('Found arm length: %f' % r)
        
        ptsInCNC= numpy.array([[numpy.sin(angles[0])*r, 0., numpy.cos(angles[0])*r, 1.],
                                [numpy.sin(angles[1])*r, 0., numpy.cos(angles[1])*r, 1.],
                                [numpy.sin(angles[2])*r, 0., numpy.cos(angles[2])*r, 1.]])
        
        camToCNC = vector.calculate_rigid_transform(ptsInCamera,ptsInCNC) #TODO check that this is correct
        cfg.framesLog.info('Registering cnc with points in (camera, cnc):')
        cfg.framesLog.info(ptsInCamera)
        cfg.framesLog.info(ptsInCNC)
        self.fManager.add_transformation_matrix('camera', 'cnc', camToCNC)
        
    def automated_find_tip(self):
        # enable axis motors
        self.cnc.enable_motors()
        
        # find tip location
        point1 = self.imageProcessor.locate_electrode_tip()
        angle1 = numpy.radians(float(self.cnc.headAxes.get_position('b')))
        
        deltaAngle = cfg.cncRegDeltaAngle # in degrees
        # move +deltaAngle
        self.cnc.headAxes.move_relative(deltaAngle,'b')
        # find tip location
        point2 = self.imageProcessor.locate_electrode_tip()
        angle2 = numpy.radians(float(self.cnc.headAxes.get_position('b')))
        
        # move -deltaAngle*2
        self.cnc.headAxes.move_relative(deltaAngle*-2.,'b')
        # find tip location
        point3 = self.imageProcessor.locate_electrode_tip()
        angle3 = numpy.radians(float(self.cnc.headAxes.get_position('b')))
        
        tPoints = numpy.vstack((point1,point2,point3))
        self.locate_tip(tPoints,[angle1,angle2,angle3])
    
    
    def go_to_target(self):
        pass
    
    
    def move_w_axis(self):
        pass