#!/usr/bin/env python

from OpenGL.GL import *
from pylab import *

import plotLog
from electrodeController import frameManager

import bjg.gl3dview
import bjg.glObj

class TransformObject:
    def set_transform(self, tMatrix):
        self.tMatrix = tMatrix
    def pre_draw(self):
        glPushMatrix()
        glMultMatrixd(self.tMatrix) # TODO do I need to do this prior to the orbitor transform?
    def post_draw(self):
        glPopMatrix()

class TransformObj(bjg.glObj.GLOBJ, TransformObject):
    def draw(self):
        self.pre_draw()
        self.display()
        self.post_draw()
# 
# class TransformChar(bjg.gl3dview.Char, TransformObject):
#     def draw(self):
#         self.pre_draw()
#         bjg.gl3dview.Char.draw(self)
#         self.post_draw()
# 
# class TransformSphere(bjg.gl3dview.Char, TransformObject):
#     def draw(self):
#         self.pre_draw()
#         bjg.gl3dview.Sphere.draw(self)
#         self.post_draw()

class ArrayViewer(bjg.gl3dview.GL3DView):
    def add_array(self, dataArray, objClass, *args, **kwargs):
        for i in dataArray:
            self.objects.append(objClass(tuple(i[:3]), *args, **kwargs))

if __name__ == '__main__':
    logDir = sys.argv[1]
    f = open('%s/root.log' % logDir, 'r')
    
    colors = [(0,0,1,1), (1,0,0,1), (0,1,0,1), (1,1,0,1), (1,0,1,1), (0,1,1,0)]
    viewFrame = 'skull'
    
    locations = plotLog.get_camera_locations(f)
    matrices = plotLog.get_matrices(f)
    points = plotLog.get_frame_registration_points(f)
    sTipPoints = plotLog.get_skull_positions(f)
    
    fm = frameManager.FrameManager(['skull', 'tricorner', 'camera', 'cnc'])
    for (n,m) in matrices.iteritems():
        fromFrame = n.split()[0]
        toFrame = n.split()[2]
        fm.add_transformation_matrix(fromFrame, toFrame, matrix(m))
    
    # tricorner and seen from camera
    tcPoints, cTcPoints = points['cameras']
    # seen from camera and cnc tip
    cTipPoints, tipPoints = points['cnc']
    
    camLocs = ones((2,4),dtype=float64)
    camLocs[:,:3] = array(locations.values())
    
    # convert all objects to viewFrame
    sTipPoints = array(fm.transform_point(sTipPoints, 'skull', viewFrame))
    camLocs = array(fm.transform_point(camLocs, 'camera', viewFrame))
    tcPoints = array(fm.transform_point(tcPoints, 'tricorner', viewFrame))
    cTcPoints = array(fm.transform_point(cTcPoints, 'camera', viewFrame))
    tipPoints = array(fm.transform_point(tipPoints, 'cnc', viewFrame))
    cTipPoints = array(fm.transform_point(cTipPoints, 'camera', viewFrame))
    
    # setup view
    view = ArrayViewer(radius=1000)#bjg.gl3dview.GL3DView()
    view.init_glut()
    
    view.add_array(sTipPoints, bjg.gl3dview.Char, color=colors[0], char='s') # skull
    view.add_array(camLocs, bjg.gl3dview.Char, color=colors[1], char='e') # 'eyes'
    view.add_array(tcPoints, bjg.gl3dview.Char, color=colors[2], char='h') # hat
    view.add_array(cTcPoints, bjg.gl3dview.Char, color=colors[3], char='H') # transformed Hat
    view.add_array(tipPoints, bjg.gl3dview.Char, color=colors[4], char='t') # tip
    view.add_array(cTipPoints, bjg.gl3dview.Char, color=colors[5], char='T') # transformed Tip
    
    # load objects and transforms
    tcSeat = TransformObj()
    tcSeat.load('media/meshes/tcSeat.obj', 'media/meshes/tcSeat.jpg')
    tcSeat.prep_lists()
    tcSeat.set_transform(fm.get_transformation_matrix('tricorner',viewFrame))
    view.objects.append(tcSeat)
    
    bridge = TransformObj()
    bridge.load('media/meshes/bridge.obj', 'media/meshes/bridge.jpg')
    bridge.prep_lists()
    bridge.set_transform(fm.get_transformation_matrix('tricorner',viewFrame))
    view.objects.append(bridge)
    
    view.run()
        
