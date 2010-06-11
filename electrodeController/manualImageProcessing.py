#!/usr/bin/env python

# Manual image processing

import time

import cameraPair

class Processor:
    def __init__(self, cameras):
        self.cameras = cameras
        self.leftZoomView = None
        self.rightZoomView = None
    
    
    def find_tricorner_registration_points(self):
        # return homogeneous points
        if self.leftZoomView == None or self.rightZoomView == None:
            raise Exception('Manual Processor needs a self.leftZoomView and self.rightZoomView')
        ims = self.cameras.capture()
        self.leftZoomView.set_image_from_cv(ims[0])
        self.leftZoomView.validPoints = False
        self.rightZoomView.set_image_from_cv(ims[1])
        self.rightZoomView.validPoints = False
        
        while self.leftZoomView.validPoints == False or self.rightZoomView.validPoints == False:
            time.sleep(1)
        
        leftPoints = self.leftZoomView.get_zoom_locations()
        rightPoints = self.rightZoomView.get_zoom_locations()
        rPoints = []
        for l, r in zip(leftPoints, rightPoints):
            rPoints.append(self.cameras.get_3d_position([l,r]))
        
        return rPoints
    
    
    def find_electrode_tip(self):
        # return homogeneous point
        pass