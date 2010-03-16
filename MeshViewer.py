#!/usr/bin/env python

from Foundation import *
from AppKit import *
import objc
from objc import IBAction, IBOutlet

from OpenGL.GL import *
from OpenGL.GLU import *

import objLoader
#import cameraPair


class MeshViewer (NSOpenGLView):
    def awakeFromNib(self):
        # gl_inited is also touched by objc
        self.gl_inited = False
        self.mesh = None
    
    def load_mesh(self, meshFilename, textureFilename):
        self.mesh = objLoader.OBJ(meshFilename, textureFilename)
        print "Making mesh lists"
        self.mesh.prep_lists()
        self.scheduleRedisplay()
    
    def draw_mesh(self):
        self.mesh.display()
        
    def initGL(self):
        glEnable(GL_BLEND)
        glEnable(GL_TEXTURE_2D)
        glDisable(GL_LIGHTING)
        #glBlendFunc(GL_ONE, GL_ZERO)
        #glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        #glBlendFunc(GL_ONE_MINUS_DST_ALPHA, GL_DST_ALPHA)
        glPixelStorei(GL_UNPACK_ALIGNMENT,1)
        
        glClearColor(0., 0., 0., 1.)
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        gluPerspective(40.,1.,0.1,1000.0)
        #glViewport(0, 0, int(self.frame_width), int(self.frame_height))
        
        glMatrixMode(GL_MODELVIEW)
        gluLookAt(0,0,10,
              0,0,0,
              0,1,0)
        
        self.gl_inited = True
    
    def scheduleRedisplay(self):
        """Call to force redisplay of the opengl view"""
        self.setNeedsDisplay_(True)
    
    def drawRect_(self, frame):
        """Display function"""
        if not self.canDraw():
            return
        
        if self.gl_inited == False:
            # TODO this is always false and always gets called
            self.initGL()
            pass
        
        frame = self.frame()
        self.frame_width = frame.size.width
        self.frame_height = frame.size.height
        
        if(self.mesh == None):
            print "Mesh is None"
            self.load_mesh("/Users/graham/Repositories/coxlab/structured_light_stereotaxy/software/viewer/example_mesh/mesh.obj",
                            "/Users/graham/Repositories/coxlab/structured_light_stereotaxy/software/viewer/example_mesh/texture.jpg")
            self.openGLContext().flushBuffer()
            return
    
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPushMatrix()
        xpos = 0.
        ypos = 0.
        zpos = 0.
        xrot = 0.
        yrot = 0.
        scale = 0.01
        glTranslate(xpos, ypos, zpos)
        glRotatef(xrot, 0., 1., 0.)
        glRotatef(yrot, 1., 0., 0.)
        glScalef(scale, scale, scale)
        
        self.draw_mesh()
        
        glPopMatrix()
        
        print "flushing buffer"
        self.openGLContext().flushBuffer()