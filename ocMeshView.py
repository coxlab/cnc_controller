#!/usr/bin/env python

import time

import numpy

import quaternion
from electrodeController import objLoader
from electrodeController import cfg
from electrodeController import vector

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
    
    def reset(self):
        self.translation = [0, 0, 0]
        self.rotation = quaternion.fromEuler(0,0,0)
        self.radius = 100.
    
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
        glPushMatrix() # X, red
        glRotatef(90,0,1,0)
        glColor(1.,0.,0.,1.)
        gluCylinder(gluNewQuadric(), 0.05, 0.05, 0.5, 10, 3)
        glTranslate(0.,0.,0.5)
        glutSolidCone(0.1, 0.2, 10, 3)
        glPopMatrix()
        
        #glTranslate(0.,0.,-1.)
        glPushMatrix() # Y, green
        glRotatef(-90,1,0,0)
        glColor(0.,1.,0.,1.)
        gluCylinder(gluNewQuadric(), 0.05, 0.05, 0.5, 10, 3)
        glTranslate(0.,0.,0.5)
        glutSolidCone(0.1, 0.2, 10, 3)
        glPopMatrix()
        
        glColor(0.,0.,1.,1.) # Z, blue
        glPushMatrix()
        gluCylinder(gluNewQuadric(), 0.05, 0.05, 0.5, 10, 3)
        glTranslate(0.,0.,0.5)
        glutSolidCone(0.1, 0.2, 10, 3)
        glPopMatrix()


class OCMeshView(NSOpenGLView):
    def awakeFromNib(self):
        self.orbiter = Orbiter()#rotation=[2.3561944901923448,0.,0.])
        self.objs = []
        self.gl_inited = False
        self.leftDown = None
        self.rightDown = None
        self.electrode = None
        self.meshFilenames = []
        self.meshTextureFilenames = []
        self.drawElectrode = True
        self.electrodeMatrix = numpy.matrix(numpy.identity(4,dtype=numpy.float64))
        self.pathParams = numpy.array([0., 0., 0., 0., 0., 1.])
        self.points = None
        self.pathPoints = None
    
    @IBAction
    def showHelp_(self, sender):
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Mesh Tab Help")
        alert.setInformativeText_("""
        Left Drag = Rotate View
        Right Drag = Translate View
        Scroll = Zoom
        t = toggle Texture
        p = toggle pointcloud
        m = toggle mesh
        r = reset view""")
        alert.setAlertStyle_(NSInformationalAlertStyle)
        alert.runModal()
    
    # so we get a keyDown event
    def acceptsFirstResponder(self):
        return YES
    
    def becomeFirstResponder(self):
        return YES
    
    def resignFirstResponder(self):
        return YES
    
    def keyDown_(self, event):
        c = event.characters()
        if (event.modifierFlags() & NSControlKeyMask):
            try:
                i = int(c) - 1
                if i in xrange(len(self.objs)):
                    self.objs[i].visible = not self.objs[i].visible
                    self.scheduleRedisplay()
            except ValueError:
                pass
        else: # non ctrl things
            if len(self.objs) > 0:
                if c == 't':
                    for o in self.objs:
                        o.showTexture = not o.showTexture
                    self.scheduleRedisplay()
                elif c == 'p':
                    for o in self.objs:
                        o.showPointCloud = not o.showPointCloud
                    self.scheduleRedisplay()
                elif c == 'm':
                    for o in self.objs:
                        o.showMesh = not o.showMesh
                    self.scheduleRedisplay()
            
            
            if c == 'r':
                self.orbiter.reset()
                self.scheduleRedisplay()
            elif c == '1':
                self.orbiter.rotation = quaternion.fromEuler(0,0,0)
                self.scheduleRedisplay()
            elif c == '!':
                self.orbiter.rotation = quaternion.fromEuler(numpy.pi,0,0)
                self.scheduleRedisplay()
            elif c == '2':
                self.orbiter.rotation = quaternion.fromEuler(-numpy.pi/2,0)
                self.scheduleRedisplay()
            elif c == '@':
                self.orbiter.rotation = quaternion.fromEuler(numpy.pi/2,0)
                self.scheduleRedisplay()
            elif c == '3':
                self.orbiter.rotation = quaternion.fromEuler(-numpy.pi/2,0,-numpy.pi/2)
                self.scheduleRedisplay()
            elif c == '#':
                self.orbiter.rotation = quaternion.fromEuler(-numpy.pi/2,0,numpy.pi/2)
                self.scheduleRedisplay()
    
    def load_obj(self, meshFilename, textureFilename):
        # so, if this is called before the mesh tab has been visited,
        # gl_inited will be false, and the loading will fail :(
        # and it will fubar other textures (see zoomView)
        
        self.meshFilenames.append(meshFilename)
        self.meshTextureFilenames.append(textureFilename)
        if self.gl_inited == False:
            return
        
        self.objs.append(objLoader.OBJ(meshFilename, textureFilename))
        #self.objs[-1].prep_lists()
        
        self.scheduleRedisplay()
        
        #while self.obj == None:
        #    print "sleeping"
        #    time.sleep(1)
        #print "self.obj is not none"
        
        #self.obj = objLoader.OBJ(meshFilename, textureFilename)
        #self.obj.prep_lists()
        
        #self.scheduleRedisplay()
    
    def load_electrode(self, meshFilename, textureFilename=None):
        self.electrode = objLoader.OBJ(meshFilename, textureFilename)
        self.electrode.prep_lists()
        self.electrode.color = (0.4, 0.7, 0.4, 1.0)
        
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
        #glEnable(GL_ALPHA_TEST)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        glEnable(GL_TEXTURE_2D)
        glDisable(GL_LIGHTING)
        
        glEnable(GL_DEPTH_TEST)
        glClearDepth(1.0)
        glDepthFunc(GL_LEQUAL)
        glClearColor(0., 0., 0., 1.)
        glMatrixMode(GL_PROJECTION)
        gluPerspective(10.,1.,1.,1000.0)
        
        self.load_electrode(cfg.electrodeMesh, cfg.electrodeTexture)
        
        self.gl_inited = True
        
        if len(self.meshFilenames) > 0 and len(self.objs) == 0:
            for i in xrange(len(self.meshFilenames)):
                self.objs.append(self.meshFilenames[i],self.meshTextureFilenames[i])
                #self.objs[-1].prep_lists()
    
    def draw_tip_path(self):
        #o = numpy.array(self.pathParams[:3])
        #m = numpy.array(self.pathParams[3:])
        #p0 = o + (-1000. * m)
        #p1 = o + (1000. * m)
        p0 = self.pathParams[:3]
        p1 = self.pathParams[3:]
        glColor4f(0., 0., 1., 1.)
        glLineWidth(1.)
        glBegin(GL_LINES)
        glVertex3f(*p0)
        glVertex3f(*p1)
        glEnd()
        #glColor4f(0., 1., 0., 0.5) # alpha doesn't seem to work on lines
        #glLineWidth(4.)
        #glBegin(GL_LINES)
        #glVertex3f(*p0)
        #glVertex3f(*p1)
        #glEnd()
    
    #def draw_electrode_path(self):
    #    glColor(1., 0., 0., 1.)
    #    glBegin(GL_LINES)
    #    glVertex3f(0., 0., -100000.)
    #    glVertex3f(0., 0., 100000.)
    #    glEnd()
    
    def draw_points(self, points, size, color):
        glPointSize(size)
        glColor(*color)
        glBegin(GL_POINTS)
        for p in points:
            glVertex3f(*p)
        glEnd()
    
    def drawRect_(self, frame):
        if not self.canDraw():
            return
        if self.gl_inited == False:
            self.initGL()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        #frame = self.frame()
        #glViewport(0,0,int(frame.size.width),int(frame.size.height))
        self.orbiter.setup_model_view()
        
        for o in self.objs:
            if o.meshList == None:
                print "prepping lists in draw"
                o.prep_lists()
            o.display()
        
        glPushMatrix()
        self.draw_tip_path()
        glPopMatrix()
        
        if self.pathPoints != None:
            glPushMatrix()
            self.draw_points(self.pathPoints, 3, (0.5, 0.5, 1., 1.))
            glPopMatrix()
        
        if self.points != None:
            glPushMatrix()
            self.draw_points(self.points, 5, (1., 1., 1., 1.))
            glPopMatrix()
        
        if self.electrode != None and self.drawElectrode:
            glPushMatrix()
            #glTranslatef(self.electrodeMatrix[3,0], self.electrodeMatrix[3,1], self.electrodeMatrix[3,2])
            glMultMatrixd(numpy.array(self.electrodeMatrix))
            #self.draw_electrode_path()
            self.electrode.display()
            glPopMatrix()
        
        self.orbiter.draw_origin()
        
        self.openGLContext().flushBuffer()