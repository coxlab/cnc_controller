#!/usr/bin/env python
# import pygame
from PIL import Image
from OpenGL.GLU import *
from OpenGL.GL import *

import time


def print_timing(func):
    def wrapper(*arg):
        t1 = time.time()
        res = func(*arg)
        t2 = time.time()
        print '%s took %0.3f ms' % (func.func_name, (t2 - t1) * 1000.0)
        return res
    return wrapper


def LoadTexture(filename):
    glEnable(GL_TEXTURE_2D)
    im = Image.open(filename)
    # im = im.transpose(Image.FLIP_TOP_BOTTOM)
    # imString = im.tostring("raw", "RGB", 0, -1)
    # imString = im.tostring("raw", "RGB", 0, -1)
    texId = 0
    texId = glGenTextures(1)
    # print "Gen Tex: ", texId
    w, h = im.size
    glBindTexture(GL_TEXTURE_2D, texId)
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    gluBuild2DMipmaps(GL_TEXTURE_2D, 3, w, h, GL_RGB, GL_UNSIGNED_BYTE,
                      im.tostring("raw", "RGB", 0, -1))
    # gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGB, w, h, GL_RGB, GL_UNSIGNED_BYTE, imString)
    # glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA,
    # GL_UNSIGNED_BYTE, imString)
    glBindTexture(GL_TEXTURE_2D, 0)
    glDisable(GL_TEXTURE_2D)
    return texId


class OBJ:

    def __init__(self, filename, textureFilename=None, swapyz=False):
        """Loads a Wavefront OBJ file. """
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []
        self.texId = 0

        self.meshList = None
        self.pointCloudList = None

        self.visible = True

        if textureFilename == None:
            self.textureFilename = None
            self.showTexture = False
        else:
            self.textureFilename = textureFilename
            # self.texId = LoadTexture(textureFilename)
            self.showTexture = True

        self.showMesh = True
        self.showPointCloud = False
        material = None
        self.color = (1., 1., 1., 1.)
        for line in open(filename, "r"):
            if line.startswith('#'):
                continue
            values = line.split()
            if not values:
                continue
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
            # elif values[0] in ('usemtl', 'usemat'):
            #    material = values[1]
            # elif values[0] == 'mtllib':
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

    def prep_mesh_list(self):
        if self.textureFilename:
            self.texId = LoadTexture(self.textureFilename)
            # print "tid during load", self.texId
        self.meshList = glGenLists(1)
        glNewList(self.meshList, GL_COMPILE)

        glFrontFace(GL_CCW)
        glMaterialfv(GL_FRONT, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))
        glBegin(GL_TRIANGLES)
        if len(self.normals) != 0:
            if len(self.texcoords) != 0:
                # use normals and texcoords
                for face in self.faces:
                    vs, ns, tcs, m = face
                    glNormal3fv(self.normals[ns[0] - 1])
                    glTexCoord2fv(self.texcoords[tcs[0] - 1])
                    glVertex3fv(self.vertices[vs[0] - 1])
                    glNormal3fv(self.normals[ns[1] - 1])
                    glTexCoord2fv(self.texcoords[tcs[1] - 1])
                    glVertex3fv(self.vertices[vs[1] - 1])
                    glNormal3fv(self.normals[ns[2] - 1])
                    glTexCoord2fv(self.texcoords[tcs[2] - 1])
                    glVertex3fv(self.vertices[vs[2] - 1])
            else:
                # use normals NOT texcoords
                for face in self.faces:
                    vs, ns, tcs, m = face
                    glNormal3fv(self.normals[ns[0] - 1])
                    glVertex3fv(self.vertices[vs[0] - 1])
                    glNormal3fv(self.normals[ns[1] - 1])
                    glVertex3fv(self.vertices[vs[1] - 1])
                    glNormal3fv(self.normals[ns[2] - 1])
                    glVertex3fv(self.vertices[vs[2] - 1])
        elif len(self.texcoords) != 0:
            for face in self.faces:
                vs, ns, tcs, m = face
                glTexCoord2fv(self.texcoords[tcs[0] - 1])
                glVertex3fv(self.vertices[vs[0] - 1])
                glTexCoord2fv(self.texcoords[tcs[1] - 1])
                glVertex3fv(self.vertices[vs[1] - 1])
                glTexCoord2fv(self.texcoords[tcs[2] - 1])
                glVertex3fv(self.vertices[vs[2] - 1])
        else:
            for face in self.faces:
                vs, ns, tcs, m = face
                glVertex3fv(self.vertices[vs[0] - 1])
                glVertex3fv(self.vertices[vs[1] - 1])
                glVertex3fv(self.vertices[vs[2] - 1])
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
        if not self.visible:
            return
        glColor(*self.color)
        if self.showMesh:
            if self.showTexture:
                glEnable(GL_TEXTURE_2D)
                glBindTexture(GL_TEXTURE_2D, self.texId)
            glCallList(self.meshList)
            if self.showTexture:
                glDisable(GL_TEXTURE_2D)
        if self.showPointCloud:
            glCallList(self.pointCloudList)
        # if self.textureFilename != None:
        # print "fn: %s, tid: %s" % (self.textureFilename.split('/')[-1],
        # str(self.texId))
        glBindTexture(GL_TEXTURE_2D, 0)
