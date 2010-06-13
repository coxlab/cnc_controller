#!/usr/bin/env python

import numpy

import quaternion
import objLoader

from Foundation import *
from AppKit import *
import objc
from objc import IBAction, IBOutlet

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

class Orbiter:
    def __init__(self, radius=100., translation=[0,0,0], rotation=[0,0,0]):
        self.radius = radius
        self.translation = translation
        self.rotation = quaternion.fromEuler(rotation[0],rotation[1],rotation[2])
    
    def rotate(self, ax=0, ay=0, az=0):
        #rotQuaternion = quaternion.fromEuler((y-viewDown[1])*0.01,(x-viewDown[0])*0.01,0.) * rotQuaternion
        self.rotation = quaternion.fromEuler(ax,ay,az) * self.rotation
    
    def translate(self, dx=0, dy=0, dz=0):
        self.translation[0] += dx * self.radius
        self.translation[1] += dy * self.radius
        self.translation[2] += dz * self.radius
    
    def zoom(self, dr):
        self.radius += dr
    
    def setup_model_view(self):
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(self.translation[0],self.translation[1],self.radius,self.translation[0],self.translation[1],self.translation[2], 0,1,0)
        glMultMatrixd(self.rotation.matrix())
    
    def draw_origin(self):
        glPushMatrix() # X
        glRotatef(90,0,1,0)
        glColor(1.,0.,0.,1.)
        gluCylinder(gluNewQuadric(), 0.05, 0.05, 0.5, 10, 3)
        glTranslate(0.,0.,0.5)
        glutSolidCone(0.1, 0.2, 10, 3)
        glPopMatrix()
        
        #glTranslate(0.,0.,-1.)
        glPushMatrix() # Y
        glRotatef(-90,1,0,0)
        glColor(0.,0.,1.,1.)
        gluCylinder(gluNewQuadric(), 0.05, 0.05, 0.5, 10, 3)
        glTranslate(0.,0.,0.5)
        glutSolidCone(0.1, 0.2, 10, 3)
        glPopMatrix()
        
        glColor(0.,1.,0.,1.) # Z
        glPushMatrix()
        gluCylinder(gluNewQuadric(), 0.05, 0.05, 0.5, 10, 3)
        glTranslate(0.,0.,0.5)
        glutSolidCone(0.1, 0.2, 10, 3)
        glPopMatrix()


class OCMeshView(NSOpenGLView):
    def awakeFromNib(self):
        self.orbiter = Orbiter()
        self.obj = None
        self.gl_inited = False
        self.leftDown = None
        self.rightDown = None
    
    def load_obj(self, meshFilename, textureFilename, center=False):
        self.obj = objLoader.OBJ(meshFilename, textureFilename)
        
        if center:
            v = numpy.array(obj.vertices)
            v = v - numpy.mean(v,0)
            self.obj.vertices = v.tolist()
        
        self.obj.prep_lists()
        self.scheduleRedisplay()
    
    # left mouse button
    def mouseDown_(self, event):
        x,y = self.convertPoint_fromView_(event.locationInWindow(), None)
        self.leftDown = (x,y)
    
    def mouseUp_(self, event):
        self.leftDown = None
    
    def mouseDragged_(self, event):
        if self.leftDown != None:
            x,y = self.convertPoint_fromView_(event.locationInWindow(), None)
            self.orbiter.rotate((self.leftDown[1]-y)*0.01,(x-self.leftDown[0])*0.01,0.)
            self.leftDown = (x,y)
            self.scheduleRedisplay()
    
    # right mouse button
    def rightMouseDown_(self, event):
        x,y = self.convertPoint_fromView_(event.locationInWindow(), None)
        self.rightDown = (x,y)
    
    def rightMouseUp_(self, event):
        self.rightDown = None
    
    def rightMouseDragged_(self, event):
        if self.rightDown != None:
            x,y = self.convertPoint_fromView_(event.locationInWindow(), None)
            self.orbiter.translate((self.rightDown[0]-x)/5000.,(self.rightDown[1]-y)/5000.,0.)
            self.rightDown = (x,y)
            self.scheduleRedisplay()
    
    # scroll wheel
    def scrollWheel_(self, event):
        self.orbiter.zoom(-event.deltaY())
        self.scheduleRedisplay()
    
    # drawing
    def scheduleRedisplay(self):
        self.setNeedsDisplay_(True)
    
    def initGL(self):
        glEnable(GL_BLEND)
        glEnable(GL_TEXTURE_2D)
        glDisable(GL_LIGHTING)
        
        glEnable(GL_DEPTH_TEST)
        glClearDepth(1.0)
        glDepthFunc(GL_LEQUAL)
        glClearColor(0., 0., 0., 1.)
        glMatrixMode(GL_PROJECTION)
        gluPerspective(10.,1.,0.1,1000.0)
        self.gl_inited = True
    
    def drawRect_(self, frame):
        if not self.canDraw():
            return
        if self.gl_inited == False:
            self.initGL()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        #frame = self.frame()
        #glViewport(0,0,int(frame.size.width),int(frame.size.height))
        self.orbiter.setup_model_view()
        
        if self.obj != None:
            self.obj.display()
        self.orbiter.draw_origin()
        
        self.openGLContext().flushBuffer()