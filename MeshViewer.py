#!/usr/bin/env python

from Foundation import *
from AppKit import *
import objc
from objc import IBAction, IBOutlet

from OpenGL.GL import *
from OpenGL.GLU import *

import sys
import numpy

#import obj
import objLoader
#import cameraPair


# =======================================================================
# mesh viewer is in SKULL coordinates but contains matrix (MeshViewer.skullToTCMatrix)
# to convert skull to TC frame (inv(matrix) to go other way)
# =======================================================================



class MeshViewer (NSOpenGLView):
    
    app = objc.IBOutlet()
    
    def awakeFromNib(self):
        # gl_inited is also touched by objc
        self.gl_inited = False
        self.mesh = None
        self.animalCfg = None
        self.renderLoading = False
        
        self.xpos = 0.
        self.ypos = 0.
        self.zpos = 0.
        self.xrot = 0.
        self.yrot = 0.
        self.zrot = 0.
        self.scale = 0.01
        
    
    
    @IBAction
    def loadAnimal_(self, sender):
        panel = NSOpenPanel.openPanel()
        panel.setCanChooseDirectories_(YES)
        panel.setCanChooseFiles_(NO)
        panel.setAllowsMultipleSelection_(NO)
        #panel.setAllowedFileTypes_(['obj'])
        
        def url_to_string(url):
            # TODO make this more robust
            return str(url)[16:]
        
        panel.setTitle_("Select an animal directory")
        retValue = panel.runModal()
        animalDir = ""
        if retValue:
            animalDir = url_to_string(panel.URLs()[0])
        else:
            print "Mesh selection canceled"
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
        self.load_animal(animalDir)
        
    
    def start_loading(self):
        dockTile = self.app.dockTile()
        dockTile.setBadgeLabel_("Wait")
        self.renderLoading = True
    
    def end_loading(self):
        self.renderLoading = False
        dockTile = self.app.dockTile()
        dockTile.setBadgeLabel_("")
    
    def load_animal(self, animalDir):
        dockTile = self.app.dockTile()
        dockTile.setBadgeLabel_("Wait")
        # load animal configuration
        sys.path.append(animalDir)
        self.animalCfg = __import__("animalCfg")
        sys.path.pop()
        # find and load skull mesh
        meshFilename = "%s/%s/skull.obj" % (animalDir, self.animalCfg.skullScan)
        textureFilename = "%s/%s/Texture/texture.jpg" % (animalDir, self.animalCfg.skullScan)
        self.mesh = objLoader.OBJ(meshFilename, textureFilename)
        self.mesh.prep_lists()
        # load skullToTCMatrix
        self.STT = numpy.loadtxt("%s/skullToTCMatrix" % animalDir)
        # check if it's possible to register the camera and skull frames
        dockTile.setBadgeLabel_("")
        self.scheduleRedisplay()
        
    
    def load_mesh(self, meshFilename, textureFilename):
        dockTile = self.app.dockTile()
        dockTile.setBadgeLabel_("Wait")
        self.mesh = objLoader.OBJ(meshFilename, textureFilename)
        dockTile.setBadgeLabel_("Wait")
        self.mesh.prep_lists()
        dockTile.setBadgeLabel_("")
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
        
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        if (self.renderLoading == True):
            self.display_loading()
            self.openGLContext().flushBuffer()
            return            
        if (self.mesh == None):
            print "Mesh is None"
            #self.load_mesh("/Users/graham/Repositories/coxlab/structured_light_stereotaxy/software/viewer/example_mesh/mesh.obj",
            #                "/Users/graham/Repositories/coxlab/structured_light_stereotaxy/software/viewer/example_mesh/texture.jpg")
            # TODO draw "No Mesh" signifier
            self.display_no_mesh()
            self.openGLContext().flushBuffer()
            return
        
        glPushMatrix()
        glTranslate(self.xpos, self.ypos, self.zpos)
        glRotatef(self.xrot, 0., 1., 0.)
        glRotatef(self.yrot, 1., 0., 0.)
        glScalef(self.scale, self.scale, self.scale)
        #print self.scale
        
        self.draw_mesh()
        
        glPopMatrix()
        
        #print "flushing buffer"
        self.openGLContext().flushBuffer()
    
    def display_no_mesh(self):
        # TODO implement this
        pass
    
    def display_loading(self):
        # TODO implement this
        pass
    
    def scrollWheel_(self, event):
        delta = event.deltaY()
        if delta > 0:
            # scale in
            self.scale *= delta+1.
        else:
            self.scale /= abs(delta)+1.
        # TODO add limits
        self.scheduleRedisplay()
    
    def mouseDown_(self, event):
        self.mesh.showTexture = False
        self.mesh.showMesh = False
        self.mesh.showPointCloud = True
    
    def mouseUp_(self, event):
        self.mesh.showTexture = True
        self.mesh.showMesh = True
        self.mesh.showPointCloud = False
        self.scheduleRedisplay()
    
    def mouseDragged_(self, event):
        dx = event.deltaX() / (self.frame_width)
        dy = event.deltaY() / (self.frame_height)
        
        self.xrot += dx * 100.
        self.yrot += dy * 100.
        # TODO, maybe turn off some rendering to speed this up
        self.scheduleRedisplay()
    
    def rightMouseDown_(self, event):
        self.mesh.showTexture = False
        self.mesh.showMesh = False
        self.mesh.showPointCloud = True
    
    def rightMouseUp_(self, event):
        self.mesh.showTexture = True
        self.mesh.showMesh = True
        self.mesh.showPointCloud = False
        self.scheduleRedisplay()
    
    def rightMouseDragged_(self, event):
        dx = event.deltaX() / (self.frame_width)
        dy = event.deltaY() / (self.frame_height)
        
        self.xpos += dx * 10.
        self.ypos -= dy * 10.
        # TODO, maybe turn off some rendering to speed this up
        self.scheduleRedisplay()