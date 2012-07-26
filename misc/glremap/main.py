#!/usr/bin/env python

# test script to try and speed up remapping of images
#  1) pick two points on the images
#  2) generate a new images that is the rotated, resampled version


# setup and generate opengl window (glumpy maybe?)

# load image and display

# select two points

# generate new image in new window?

import sys

import numpy as np
from numpy.linalg import norm

import PIL.Image
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *

from stopwatch import Timer, clockit

im = PIL.Image.open('test_images/1.png').convert("RGB")
im = im.transpose(PIL.Image.FLIP_TOP_BOTTOM) #pil loads things upside down?
scale = 0.5 # screen pixels per image pixel
imW, imH = int(im.size[0] * scale), int(im.size[1] * scale)
sampW, sampH = imW, 20
over_factor = 1.

winW, winH = imW, imH + sampH

pts_img = []

glutInit(sys.argv)
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
glutInitWindowSize(int(winW), int(winH))
mainWinID = glutCreateWindow("GLMapping test")
srcWinID = glutCreateSubWindow(mainWinID,0,0,imW,imH)
sampWinID = glutCreateSubWindow(mainWinID,0,imH,sampW,sampH)
#glutSetWindow(selectWinID)
glClearColor(0., 0., 0., 1.)

def img_to_gl(pt):
    """
    img : (0,0)upper left; (im.size[0],im.size[1])lower right
    gl  : (-1,1)upper left; (1,-1)lower right
    """
    
    global im
    x = (pt[0] / float(im.size[0]) - 0.5) * 2.0
    y = (pt[1] / float(im.size[1]) - 0.5) * -2.0
    if type(pt) == np.ndarray:
        return np.array([x,y])
    else:
        return [x,y]

def gl_to_img(pt):
    """
    gl  : (-1,1)upper left; (1,-1)lower right
    img : (0,0)upper left; (im.size[0],im.size[1])lower right
    """
    global im
    x = (pt[0] + 1.)/2. * im.size[0]
    y = (pt[1] - 1.)/-2. * im.size[1]
    if type(pt) == np.ndarray:
        return np.array([x,y])
    else:
        return [x,y]

def img_to_tex(pt):
    """
    img : (0,0)upper left; (im.size[0],im.size[1])lower right
    tex : (0,0)upper left; (1,1)lower right
    """
    global im
    x = pt[0] / float(im.size[0])
    y = pt[1] / float(im.size[1])
    if type(pt) == np.ndarray:
        return np.array([x,y])
    else:
        return [x,y]

def tex_to_img(pt):
    """
    tex : (0,0)upper left; (1,1)lower right
    img : (0,0)upper left; (im.size[0],im.size[1])lower right
    """
    global im
    x = pt[0] * im.size[0]
    y = pt[1] * im.size[1]
    if type(pt) == np.ndarray:
        return np.array([x,y])
    else:
        return [x,y]

def gl_to_tex(pt):
    """
    gl  : (-1,1)upper left; (1,-1)lower right
    tex : (0,0)upper left; (1,1)lower right
    """
    x = (pt[0]+1.)/2.
    y = (pt[1]-1.)/-2.
    if type(pt) == np.ndarray:
        return np.array([x,y])
    else:
        return [x,y]

def tex_to_gl(pt):
    """
    tex : (0,0)upper left; (1,1)lower right
    gl  : (-1,1)upper left; (1,-1)lower right
    """
    x = pt[0]*2. - 1.
    y = pt[1]*-2 + 1.
    if type(pt) == np.ndarray:
        return np.array([x,y])
    else:
        return [x,y]

def test_transforms():
    global im
    i_ul = [0,0]
    i_ur = [im.size[0],0]
    i_lr = [im.size[0],im.size[1]]
    i_ll = [0,im.size[1]]
    t_ul = [0,0]
    t_ur = [1,0]
    t_lr = [1,1]
    t_ll = [0,1]
    g_ul = [-1,1]
    g_ur = [1,1]
    g_lr = [1,-1]
    g_ll = [-1,-1]
    assert all([img_to_tex(i) == t for (i,t) in [[i_ul,t_ul],[i_ur,t_ur],[i_lr,t_lr],[i_ll,t_ll]]])
    assert all([tex_to_img(t) == i for (i,t) in [[i_ul,t_ul],[i_ur,t_ur],[i_lr,t_lr],[i_ll,t_ll]]]) 
    assert all([img_to_gl(i) == g for (i,g) in [[i_ul,g_ul],[i_ur,g_ur],[i_lr,g_lr],[i_ll,g_ll]]])
    assert all([gl_to_img(g) == i for (i,g) in [[i_ul,g_ul],[i_ur,g_ur],[i_lr,g_lr],[i_ll,g_ll]]])
    assert all([tex_to_gl(t) == g for (t,g) in [[t_ul,g_ul],[t_ur,g_ur],[t_lr,g_lr],[t_ll,g_ll]]])
    assert all([gl_to_tex(g) == t for (t,g) in [[t_ul,g_ul],[t_ur,g_ur],[t_lr,g_lr],[t_ll,g_ll]]])
    print "Transforms: OK"

test_transforms()

# setup texture
def load_texture():
    global texID
    glEnable(GL_TEXTURE_2D)
    texID = glGenTextures(1)
    glColor4f(1., 1., 1., 1.)
    glBindTexture(GL_TEXTURE_2D, texID)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glPixelStorei(GL_UNPACK_ALIGNMENT,1)
    #glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, im.size[0], im.size[1],
    #            0, GL_RGB, GL_UNSIGNED_BYTE, im.tostring("raw", "RGB", 0, -1)) # RADAR GL_UNSIGNED_BYTE may be wrong
    gluBuild2DMipmaps(GL_TEXTURE_2D, 3, im.size[0], im.size[1], GL_RGB, GL_UNSIGNED_BYTE, im.tostring("raw", "RGB", 0, -1))
    glBindTexture(GL_TEXTURE_2D, 0)
    return texID
glutSetWindow(srcWinID) # textures are window specific ?!?!?
srcTexID = load_texture()
glutSetWindow(sampWinID)
sampTexID = load_texture()

ptColors = [(1., 0., 0., 1.),
            (0., 1., 0., 1.),
            (0., 0., 1., 1.),
            (1., 1., 0., 1.),
            (1., 0., 1., 1.),
            (0., 1., 1., 1.)]

ptsInSrc_img = []

def src_display():
    global srcTexID, pts_img, ptsInSrc_img
    glClearColor(0., 0., 0., 1.)
    glClear(GL_COLOR_BUFFER_BIT)
    
    glColor(1., 1., 1., 1.)
    # display src image and any selected points
    glBindTexture(GL_TEXTURE_2D, srcTexID)
    glBegin(GL_QUADS)
    glTexCoord2f(0., 0.)
    glVertex2f(-1., 1.) # top left
    glTexCoord2f(1., 0.)
    glVertex2f(1., 1.) # top right
    glTexCoord2f(1., 1.)
    glVertex2f(1., -1.) # bottom right
    glTexCoord2f(0., 1.)
    glVertex2f(-1., -1.) # bottom left
    glEnd()
    glBindTexture(GL_TEXTURE_2D, 0)
    
    # draw points
    glPointSize(2.)
    glBegin(GL_POINTS)
    for (i,pt_img) in enumerate(pts_img):
        glColor(*ptColors[i % len(ptColors)])
        print pt_img
        pt_gl = img_to_gl(pt_img)
        #glx, gly = pt[0]/float(imW) - 1., pt[1]/float(imH) - 1.
        glVertex2f(*pt_gl)
    glEnd()
    
    if len(ptsInSrc_img):
        # print "Ptsinsrc:",ptsInSrc_img
        glBegin(GL_LINE_STRIP)
        #glColor(1., 0., 0., 1.)
        for (i,pt_img) in enumerate(ptsInSrc_img):
            glColor(*ptColors[i])
            pt_gl = img_to_gl(pt_img)
            glVertex2f(*pt_gl)
        pt_gl = img_to_gl(ptsInSrc_img[0])
        glVertex2f(*pt_gl)
        glEnd()
    
    glutSwapBuffers()

@clockit
def samp_display():
    global pts_img, ptsInSrc_img, sampTexID, over_factor
    glClearColor(0., 0., 0., 1.)
    glClear(GL_COLOR_BUFFER_BIT)
    if len(pts_img) == 2:
        #print "pts:", pts_img
        # calculate edges
        if pts_img[0][1] < pts_img[1][1]:
            spt_img = np.array(pts_img[0]) # shaft point
            tpt_img = np.array(pts_img[1]) # tip point
            #print "shaft = pt0:",spt_img,tpt_img
        else:
            spt_img = np.array(pts_img[1])
            tpt_img = np.array(pts_img[0])
            #print "shaft = pt1:",spt_img,tpt_img
        
        # convert to image coordinates (y+ down, x+ right)
        # spt[1] = im.size[1] - spt[1]
        # tpt[1] = im.size[1] - tpt[1]
        # ------------------------ From electrode_finder ---------------------
        # this stuff is in IMAGE coordinates unless otherwise marked (_frame)
        
        e_center = (spt_img + tpt_img) / 2. # should this be a float division?
        
        e_dir = tpt_img - spt_img
        e_length = over_factor*norm(e_dir)
        e_dir = e_dir / norm(e_dir) # is this a bug, maybe norm(e_dir) should be e_length
        #print "e_dir:", e_dir
        #print "e_length:", e_length
        
        #arbitrary_vec = np.array([1,0])
        
        #e_ortho = arbitrary_vec - e_dir * np.dot(arbitrary_vec, e_dir)
        e_ortho = np.array([-e_dir[1], e_dir[0]])
        e_ortho = e_ortho / norm(e_ortho)
        # print "e_ortho:", e_ortho
        
        x_native = np.array([-sampH,+sampH,+sampH,-sampH])
        y_native = np.array([0,0,e_length,e_length])
        
        npts = [[x_native[i],y_native[i]] for i in xrange(x_native.shape[0])]
        # print "Native:", npts
        def n_to_img(pt):
            x = pt[0] * e_ortho[0] + pt[1] * e_ortho[1] + e_center[0]
            y = pt[0] * e_dir[0] + pt[1] * e_dir[1] + e_center[1]
            return [x,y]
        
        impts = [n_to_img(p) for p in npts]
        
        # x_im = e_ortho[0] * x_native + e_ortho[1] * y_native + e_center[0]
        # y_im = e_dir[0] * x_native + e_dir[1] * y_native + e_center[1]
        # impts = [[x_im[i],y_im[i]] for i in xrange(x_im.shape[0])]
        
        # print "Image", impts
        
        #pts_tex = [img_to_tex([x_im[i],y_im[i]]) for i in xrange(x_im.shape[0])]
        pts_tex = [img_to_tex(p) for p in impts]
        # x_gl = #(x_im / im.size[0])# - 0.5)*2.0
        # y_gl = #(y_im / im.size[1])# - 0.5)*2.0
        
        # print "Tex", pts_tex
        
        ptsInSrc_img = [tex_to_img(p_tex) for p_tex in pts_tex]
        # for i in xrange(x_gl.shape[0]):
        #     ptsInSrc_img.append((x_gl[i]*2.-1, -(y_gl[i]*2-1)))
        # --------------------------------------------------------------------
        
        glColor(1., 1., 1., 1.)
        # display src image and any selected points
        glBindTexture(GL_TEXTURE_2D, sampTexID)
        glBegin(GL_QUADS)
        glTexCoord2f(*pts_tex[0])#0., 1.)
        glVertex2f(-1., -1.) # bottom left
        glTexCoord2f(*pts_tex[1])# 0., 0.)
        glVertex2f(-1., 1.) # top left
        glTexCoord2f(*pts_tex[2])#1., 0.)
        glVertex2f(1., 1.) # top right
        glTexCoord2f(*pts_tex[3])#1., 1.)
        glVertex2f(1., -1.) # bottom right
        glEnd()
        glBindTexture(GL_TEXTURE_2D, 0)
    
    glutSetWindow(srcWinID)
    glutPostRedisplay()
    glutSetWindow(sampWinID)
    glutSwapBuffers()

def main_display():
    glClearColor(0., 0., 0., 1.)
    glClear(GL_COLOR_BUFFER_BIT)
    
    glutSwapBuffers()

glutSetWindow(srcWinID)
glutDisplayFunc(src_display)

glutSetWindow(sampWinID)
glutDisplayFunc(samp_display)

glutSetWindow(mainWinID)
glutDisplayFunc(main_display)

def src_mouse(button, state, x, y):
    global imH, pts_img
    if button == GLUT_LEFT_BUTTON and state == GLUT_UP: # add point
        if len(pts_img) > 1:
            pts_img.pop(0)
        pts_img.append((x*2,y*2))
    elif button == GLUT_RIGHT_BUTTON and state == GLUT_UP: # remove point
        # get closest point, remove
        ptsToDel = []
        imx, imy = x*2, y*2
        for (i,p) in enumerate(pts_img):
            d = ((imx-p[0])**2. + (imy-p[1])**2)**0.5
            if d < 20:
                # remove point
                ptsToDel.append(i)
        [pts_img.pop(ptd) for ptd in ptsToDel[::-1]] # delete points
    
    if len(pts_img) == 2:
        glutSetWindow(sampWinID)
        glutPostRedisplay()
        glutSetWindow(srcWinID)
    glutPostRedisplay()

glutSetWindow(srcWinID)
glutMouseFunc(src_mouse)

glutMainLoop()
