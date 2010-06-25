#!/usr/bin/env python
#import pygame
from PIL import Image
from OpenGL.GLU import *
from OpenGL.GL import *

def LoadTexture(filename):
    im = Image.open(filename)
    im = im.transpose(Image.FLIP_TOP_BOTTOM)
    imString = im.tostring()
    texId = 0
    glGenTextures(1, texId)
    w, h = im.size
    glBindTexture(GL_TEXTURE_2D, texId)
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    gluBuild2DMipmaps(GL_TEXTURE_2D, 3, w, h, GL_RGB, GL_UNSIGNED_BYTE, imString)
    #glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, imString)
    glBindTexture(GL_TEXTURE_2D, 0)
    return texId

 
class OBJ:
    def __init__(self, filename, textureFilename, swapyz=False):
        """Loads a Wavefront OBJ file. """
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []
        
        self.meshList = None
        self.pointCloudList = None
        
        self.showTexture = True
        self.showMesh = True
        self.showPointCloud = False
        material = None
        for line in open(filename, "r"):
            if line.startswith('#'): continue
            values = line.split()
            if not values: continue
            if values[0] == 'v':
                v = map(float, values[1:4])
                if swapyz:
                    v = v[0], v[2], v[1]
                self.vertices.append(v)
            elif values[0] == 'vn':
                v = map(float, values[1:4])
                if swapyz:
                    v = v[0], v[2], v[1]
                self.normals.append(v)
            elif values[0] == 'vt':
                self.texcoords.append(map(float, values[1:3]))
            #elif values[0] in ('usemtl', 'usemat'):
            #    material = values[1]
            #elif values[0] == 'mtllib':
            #    self.mtl = MTL(values[1])
            elif values[0] == 'f':
                face = []
                texcoords = []
                norms = []
                for v in values[1:]:
                    w = v.split('/')
                    face.append(int(w[0]))
                    if len(w) >= 2 and len(w[1]) > 0:
                        texcoords.append(int(w[1]))
                    else:
                        texcoords.append(0)
                    if len(w) >= 3 and len(w[2]) > 0:
                        norms.append(int(w[2]))
                    else:
                        norms.append(0)
                self.faces.append((face, norms, texcoords, material))
        self.texId = LoadTexture(textureFilename)
    def prep_mesh_list(self):
        self.meshList = glGenLists(1)
        glNewList(self.meshList, GL_COMPILE)
        
        glFrontFace(GL_CCW)
        for face in self.faces:
            #print "processing face..."
            vertices, normals, texture_coords, material = face
            #mtl = self.mtl[material]
            #if 'texture_Kd' in mtl:
            #    # use diffuse texmap
            #    glBindTexture(GL_TEXTURE_2D, mtl['texture_Kd'])
            #else:
            #    # just use diffuse colour
            #    glColor(*mtl['Kd'])
            glMaterialfv(GL_FRONT,GL_DIFFUSE,(1.0, 1.0, 1.0, 1.0))
            glBegin(GL_POLYGON)
            for i in range(0, len(vertices)):
                if normals[i] > 0:
                    glNormal3fv(self.normals[normals[i] - 1])
                if texture_coords[i] > 0:
                    glTexCoord2fv(self.texcoords[texture_coords[i] - 1])
                glVertex3fv(self.vertices[vertices[i] - 1])
            glEnd()
        glEndList()
    def prep_point_cloud_list(self):
        self.pointCloudList = glGenLists(1)
        glNewList(self.pointCloudList, GL_COMPILE)
        
        glPointSize(2.0)
        glBegin(GL_POINTS)
        for v in self.vertices:
            glVertex3f(*v)
        glEnd()
        glEndList()        
    def prep_lists(self):
        self.prep_mesh_list()
        self.prep_point_cloud_list()
    def display(self):
        glColor(1.,1.,1.,1.)
        if self.showMesh:
            if self.showTexture:
                glEnable(GL_TEXTURE_2D)
                glBindTexture(GL_TEXTURE_2D, self.texId)
            glCallList(self.meshList)
            if self.showTexture:
                glDisable(GL_TEXTURE_2D)
        if self.showPointCloud:
            glCallList(self.pointCloudList)