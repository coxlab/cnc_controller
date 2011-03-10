#!/usr/bin/env python

import os

import numpy

import cfg
if cfg.verboseLogging:
    cfg.start_logging()
import camera
import cnc
import frameManager
import vector

# if cfg.fakeCameras:
#     import cameraPair
#     from cameraPair import FakeCameraPair as CameraPair
# else:
#     import cameraPair
#     from cameraPair import CameraPair

# if cfg.useManualImageProcessor:
#     import manualImageProcessing as imageProcessing
# else:
#     import autoImageProcessing as imageProcessing

#TODO
# - collision detection with mesh
# - logging

class Controller:
    def __init__(self):
        # construct cameras
        if cfg.fakeCameras == True:
            self.cameras = camera.stereocamera.StereoCamera(cfg.leftCamID, cfg.rightCamID, camera.filecamera.FileCamera)
        else:
            self.cameras = camera.stereocamera.StereoCamera(cfg.leftCamID, cfg.rightCamID, camera.dc1394camera.DC1394Camera)
        
        self.logDir = cfg.logDir
        self.NPathPoints = 0
        self.pathPointsInCam = None
        
        # new logging
        for c in [self.cameras.leftCamera, self.cameras.rightCamera]:
            cLogDir = '%s/cameras/%i' % (cfg.logDir, c.camID)
            if not os.path.exists(cLogDir): os.makedirs(cLogDir)
            c.logDir = cLogDir
        
        self.cameras.logDirectory = cfg.cameraLogDir
        self.connect_cameras()
        
        # create frame manager
        self.fManager = frameManager.FrameManager(['skull', 'tricorner', 'camera', 'cnc'])
        # TODO load tc to camera matrix
        
        # construct cnc
        self.cnc = cnc.cnc.FiveAxisCNC()
        
        self.animal = None
    
    def connect_cameras(self):
        # check if cameras are connected, if not, connect
        if not all(self.cameras.get_connected()):
            self.cameras.connect()
        
        # check if cameras are calibrated, if not, load calibration
        if not all(self.cameras.get_calibrated()):
            self.cameras.load_calibrations(cfg.calibrationDirectory)
    
    def cleanup(self):
        self.cameras.disconnect()
        if cfg.fakeCameras == False:
            camera.dc1394camera.close_dc1394()
    
    
    # --- frame constructing/loading ---
    
    def load_animal(self, animalCfgFile):
        # load animal configuration file
        if os.path.exists(animalCfgFile):
            cfg.load_external_cfg(animalCfgFile)
        
        # TODO load animal mesh (for collision detection and viewing)
        
        # load skull-to-tricorner transformation matrix and add to frameStack
        self.fManager.add_transformation_matrix('skull', 'tricorner', numpy.matrix(numpy.loadtxt(cfg.skullToTCMatrixFile)))
    
    def load_log(self, logDir):
        # load log directory
        if cfg.fakeCameras:
            print "assigning frame directories"
            lCamDir = logDir + '/cameras/'+ str(cfg.leftCamID) + '/'
            lFileList = [lCamDir + f for f in os.listdir(lCamDir) if '.png' in f]
            rCamDir = logDir + '/cameras/'+ str(cfg.rightCamID) + '/'
            rFileList = [rCamDir + f for f in os.listdir(rCamDir) if '.png' in f]
            self.cameras.leftCamera.set_file_list(lFileList)
            self.cameras.rightCamera.set_file_list(rFileList)
        
        stt = logDir + '/skull_to_tricorner'
        if os.path.exists(stt):
            self.fManager.add_transformation_matrix('skull', 'tricorner', numpy.matrix(numpy.loadtxt(stt)))
            numpy.savetxt(self.logDir+'/skull_to_tricorner', self.fManager.get_transformation_matrix('skull', 'tricorner'))
        
        rcpts = logDir + '/registerCameraPts'
        if os.path.exists(rcpts):
            print "loading rcpts: %s" % rcpts
            # convert pts(lx,ly,rx,ry) to (x,y,z)
            if not all(self.cameras.get_located()):
                print "locating cameras"
                lr, rr = self.cameras.capture_localization_images(cfg.gridSize)
                print lr[1], rr[1]
                #self.leftZoomView.set_image_from_cv(ims[0][0])
                #self.rightZoomView.set_image_from_cv(ims[1][0])
                if lr[1] == True and rr[1] == True:
                    self.cameras.locate(cfg.gridSize, cfg.gridBlockSize)
                else:
                    raise Exception, "Cameras failed to localize when trying to load registerCameraPts"
                #self.locateCameras_(None)
                print "testing localization result"
                if all(self.cameras.get_located()):
                    print "Cameras located"
                    cfg.cameraLog.info('Cameras Located Successfully')
                    cfg.cameraLog.info('\tID\t\t\tX\tY\tZ')
                    for c in [self.cameras.leftCamera, self.cameras.rightCamera]:
                        p = c.get_position()
                        cfg.cameraLog.info('\t%i\t%.3f\t%.3f\t%.3f' % (c.camID, p[0], p[1], p[2]))
                else:
                    raise Exception, "Cameras failed to localize when trying to load registerCameraPts"
            pts = numpy.loadtxt(rcpts)
            numpy.savetxt(self.logDir+'/registerCameraPts', pts)
            ptsInCam = []
            for p in pts:
                xyz = self.cameras.get_3d_position([p[0],p[1]], [p[2],p[3]])
                ptsInCam.append([xyz[0],xyz[1],xyz[2],1.])
            self.register_cameras(numpy.array(ptsInCam))
            
            ptsInSkull = []
            for p in ptsInCam:
                camCoord = numpy.ones(4,dtype=numpy.float64)
                camCoord[:3] = [p[0], p[1], p[2]]
                skullCoord = self.fManager.transform_point(camCoord, "camera", "skull")[0]
                ptsInSkull.append([skullCoord[0], skullCoord[1], skullCoord[2]])
            self.meshView.points = ptsInSkull
        
        mppts = logDir + '/measurePathPts'
        if os.path.exists(mppts):
            print "loading mppts: %s" % mppts
            # check if frames are flushed out
            if not self.fManager.test_route('skull','camera'):
                raise Exception, "attempting to add path points with an incomplete frame stack"
            pts = numpy.loadtxt(mppts)
            
            numpy.savetxt(self.logDir+'/measurePathPts', pts)
            
            ptsInCam = []
            wPositions = []
            for p in pts:
                xyz = self.cameras.get_3d_position([p[0],p[1]], [p[2],p[3]])
                ptsInCam.append([xyz[0],xyz[1],xyz[2]])
                wPositions.append(p[4])
            numpy.savetxt(self.logDir+'/pathPointsInCam', ptsInCam)
            self.measure_tip_path(ptsInCam, wPositions)
            self.NPathPoints = len(ptsInCam)
            lp = self.cnc.linearAxes.get_position()
            self.pathOrigin = [float(lp['x']), float(lp['y']), float(lp['z'])]
            print self.pathOrigin
        
        #self.updateFramesDisplay_(sender)
    
    def register_cameras(self, ptsInCamera):
        # # find location of 3 tricorner reference points
        # #  - homogenous points
        # #  - ordered from left to right as seen from cameras
        # tPoints = self.imageProcessor.find_tricorner_registration_points()
        # 
        # calculate transformation matrix and add to frameStack
        ptsInTC = cfg.tcRegPoints
        
        # only use 3 points
        #tcToCam = vector.calculate_rigid_transform(ptsInTC,ptsInCamera)
        
        # use all points
        tcToCam = vector.fit_rigid_transform(ptsInTC, ptsInCamera)
        
        cfg.framesLog.info('Registering cameras with points in (tcFrame, camera):')
        cfg.framesLog.info(ptsInTC)
        cfg.framesLog.info(ptsInCamera)
        self.fManager.add_transformation_matrix('tricorner', 'camera', tcToCam)
    
    def measure_tip_path(self, ptsInCamera, wPositions):
        pathParams = self.cnc.measure_tip_path(ptsInCamera, wPositions)
        self.pathPointsInCam = ptsInCamera
        cfg.cncLog.info('Found tip path params: %+.2f %+.2f %+.2f %.2f %.2f %.2f' % (pathParams[0], pathParams[1], pathParams[2], pathParams[3], pathParams[4], pathParams[5]))
    
    # ----- Dead function only beyond this point -----
    # ----- Dead function only beyond this point -----
    # ----- Dead function only beyond this point -----
    # ----- Dead function only beyond this point -----
    
    def register_cnc(self, ptsInCamera, angles, wPositions):
        raise Exception, "Does not work"
        armLength = self.cnc.calculate_arm_length(ptsInCamera, angles, wPositions)
        cfg.cncLog.info('Found arm length: %f' % armLength)
        
        ptsInCNC = numpy.zeros((len(angles),4),dtype=numpy.float64)
        # trying to make this agree with the camera frame as much as possible
        # counter-clockwise is +, clockwise is -
        # so at angle 0 we're straight down (y-) centered (x0) and z0
        # + angles take the tip right (x+)
        ptsInCNC[:,0] = numpy.sin(angles)*(wPositions+armLength)
        ptsInCNC[:,1] = -numpy.cos(angles)*(wPositions+armLength)
        ptsInCNC[:,3] = numpy.ones(len(angles))
        # ptsInCNC= numpy.array([[numpy.sin(angles[0])*r, 0., numpy.cos(angles[0])*r, 1.],
        #                         [numpy.sin(angles[1])*r, 0., numpy.cos(angles[1])*r, 1.],
        #                         [numpy.sin(angles[2])*r, 0., numpy.cos(angles[2])*r, 1.]])
        
        camToCNC = vector.calculate_rigid_transform(ptsInCamera[:3],ptsInCNC[:3]) #TODO check that this is correct
        cfg.framesLog.info('Registering cnc with points in (camera, cnc):')
        cfg.framesLog.info(ptsInCamera)
        cfg.framesLog.info(ptsInCNC)
        self.fManager.add_transformation_matrix('camera', 'cnc', camToCNC)
    
    def automated_find_tip(self):
        raise Exception, "Does not work"
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