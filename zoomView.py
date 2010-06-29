#!/usr/bin/env python

import sys, atexit

import PIL.Image
from ctypes import c_int
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *

# glut does a wonderful thing (this might be apples fault... one of the two)
# when you click File->Quit Python (instead of Shift-Q), python will receive a SIGKILL
# it is impossible to catch this and therefore impossible to clean up prior to exit
# so...
# it's VERY important that this program be exited using Shift-Q and NOTHING ELSE
# sorry :(

class ZoomView:
    """
    TODO Um... document this
    """
    
    _defaultZoomColors = [(1., 0., 0., 0.5),
                (0., 1., 0., 0.5),
                (0., 0., 1., 0.5),
                (1., 1., 0., 0.5),
                (1., 0., 1., 0.5),
                (0., 1., 1., 0.5)]
    
    def __init__(self): #, scale=1.):
        self.imageTexture = None
        self.zoomTexture = None
        self.zooms = [] # dict{'x', 'y', 'z', 'c'}
        # where x/y is in image coordinates
        # z is the zoom factor (>1 = zoomed in)
        # c is the color (r,g,b,a) for drawing the border
        self.selectedZoom = 0
        # TODO: I can get rid of this if I can find a way to get the
        #  dimensions of the opengl window
        # glutGet(GLUT_WINDOW_WIDTH)
        # glutGet(GLUT_WINDOW_HEIGHT)
        #self.scale = float(scale)
        
        ## size is not necessary if I just go from screen <-> image coordinates
        #self.size = size # size of the zoomed view is window coordinates in the form (width, height)
        self.imageSize = (1., 1.)
        self.contrast = 1.
        self.lastLeftMouse = None
        self.mouseIsIn = True
    
    
    
    # ============ OpenGL drawing function ============
    
    def draw(self):
        if self.imageTexture == None:
            return
        self.draw_image()
        if len(self.zooms) > 0:
            self.draw_zooms()
        #self.draw_test_quad()
    
    def draw_zoom(self, index):
        zoom = self.zooms[index]
        glXY = self._image_to_gl(zoom['x'], zoom['y'])
        glHalfSize = 0.3 # this is a proportion of the image size
        
        texXY = self._image_to_tex(zoom['x'], zoom['y'])
        texHalfSize = glHalfSize / 2.
        
        # zoomed box
        glColor4f(1.0, 1.0, 1.0, 1.0)
        #glColor4f(0.5, 0.5, 0.5, 1.0)
        glBindTexture(GL_TEXTURE_2D, self.imageTexture)
        #glBindTexture(GL_TEXTURE_2D, self.zoomTexture)
        glUseProgram(self.shader)
        
        # print "finding my_color_texture"
        # self.shader_texture_loc = glGetUniformLocation(self.shader, "my_color_texture")
        # print "found my_color_texture"
        # 
        # print "finding contrast"
        # self.shader_contrast_loc = glGetUniformLocation(self.shader, "contrast")
        # print "found contrast"
        # 
        # glUniform4f(self.shader_contrast_loc, 2.0, 2.0, 2.0, 1.0)
        
        glBegin(GL_QUADS)
        zhw = texHalfSize / zoom['z']
        glTexCoord2f(texXY[0]-zhw, texXY[1]+zhw)
        glVertex2f(glXY[0]-glHalfSize, glXY[1]-glHalfSize)
        glTexCoord2f(texXY[0]+zhw, texXY[1]+zhw)
        glVertex2f(glXY[0]+glHalfSize, glXY[1]-glHalfSize)
        glTexCoord2f(texXY[0]+zhw, texXY[1]-zhw)
        glVertex2f(glXY[0]+glHalfSize, glXY[1]+glHalfSize)
        glTexCoord2f(texXY[0]-zhw, texXY[1]-zhw)
        glVertex2f(glXY[0]-glHalfSize, glXY[1]+glHalfSize)
        glEnd()
        glBindTexture(GL_TEXTURE_2D, 0)
        glUseProgram(0)
        
        
        # crosshairs
        glColor4f(*zoom['c'])
        glBegin(GL_LINES)
        glVertex2f(glXY[0]-glHalfSize, glXY[1])
        glVertex2f(glXY[0]+glHalfSize, glXY[1])
        glVertex2f(glXY[0], glXY[1]-glHalfSize)
        glVertex2f(glXY[0], glXY[1]+glHalfSize)
        glEnd()
        
        # if selected:
        if index == self.selectedZoom:
            # draw border
            glColor4f(*zoom['c'])
            glBegin(GL_LINE_STRIP)
            glVertex2f(glXY[0]-glHalfSize, glXY[1]-glHalfSize)
            glVertex2f(glXY[0]+glHalfSize, glXY[1]-glHalfSize)
            glVertex2f(glXY[0]+glHalfSize, glXY[1]+glHalfSize)
            glVertex2f(glXY[0]-glHalfSize, glXY[1]+glHalfSize)
            glVertex2f(glXY[0]-glHalfSize, glXY[1]-glHalfSize)
            glEnd()
        
    
    def draw_zooms(self):
        for i in xrange(len(self.zooms)):
            if i == self.selectedZoom:
                continue
            self.draw_zoom(i)
        self.draw_zoom(self.selectedZoom)
    
    def draw_image(self):
        glEnable(GL_TEXTURE_2D)
        self.load_texture_from_string(self.imageData)
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBindTexture(GL_TEXTURE_2D, self.imageTexture)
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
    
    def draw_test_quad(self):
        # test quad
        glColor4f(1., 0., 0., 1.)
        glBegin(GL_QUADS)
        glVertex2f(0., 1.)
        glVertex2f(1., 1.)
        glVertex2f(1., 0.)
        glVertex2f(0., 0.)
        glEnd()
    
    
    
    # ============ OpenGL Related callbacks ============    
    
    def process_normal_keys(self, key, x, y):
        if not self.mouseIsIn:
            return
        x, y = self._window_to_image(x,y)
        #print "process_normal_keys:", key, x, y
        #key = key.lower()
        if key == 'a':
            self.add_zoomed_area(x, y)
            self.selectedZoom = len(self.zooms)-1
        elif not len(self.zooms):
            return
        elif key == 'x':
            #self.selectedZoom =  self.find_closest_zoom_index(x,y)
            self.zooms[self.selectedZoom]['z'] *= 0.9
            if self.zooms[self.selectedZoom]['z'] < 1.:
                self.zooms[self.selectedZoom]['z'] = 1.
        elif key == 'z':
            #self.selectedZoom =  self.find_closest_zoom_index(x,y)
            self.zooms[self.selectedZoom]['z'] *= 1.1
            if self.zooms[self.selectedZoom]['z'] > 100.:
                self.zooms[self.selectedZoom]['z'] = 100.
        elif key == 'd':
            i = self.find_closest_zoom_index(x,y)
            if i == self.selectedZoom:
                self.selectedZoom = 0
            self.zooms.remove(self.zooms[i])
        elif key == 'c':
            self.change_contrast(1.)
        elif key == 'C':
            self.change_contrast(-1.)
        elif key == 'r':
            self.reset_contrast()
    
    def process_mouse(self, button, state, x, y):
        if (not self.mouseIsIn) or (not len(self.zooms)):
            return
        x, y = self._window_to_image(x,y)
        #print "process_mouse:", button, state, x, y
        if button == GLUT_LEFT_BUTTON:
            if state == GLUT_DOWN:
                self.leftMouseDown = (x,y)
                self.lastLeftMouse = (x,y)
                self.selectedZoom = self.find_closest_zoom_index(x,y)
            if state == GLUT_UP:
                self.lastLeftMouse = None
                self.leftMouseDown = None
    
    def process_mouse_entry(self, state):
        #print "process_mouse_entry:", state
        if state == GLUT_LEFT:
            self.mouseIsIn = False
        else:
            self.mouseIsIn = True
    
    def process_active_mouse_motion(self, x, y):
        if not len(self.zooms):
            return
        #if not self.mouseIsIn:
        #    return
        x, y = self._window_to_image(x,y)
        #print "process_active_mouse_motion:", x, y
        if self.lastLeftMouse == None:
            return
        dX = x - self.lastLeftMouse[0]
        dY = y - self.lastLeftMouse[1]
        self.zooms[self.selectedZoom]['x'] = self.zooms[self.selectedZoom]['x'] + dX / self.zooms[self.selectedZoom]['z']
        if self.zooms[self.selectedZoom]['x'] > self.imageSize[0]:
            # TODO this could still be invalid (if x == self.imageSize[0])
            self.zooms[self.selectedZoom]['x'] = self.imageSize[0]-1.
        if self.zooms[self.selectedZoom]['x'] < 0.:
            # TODO this could still be invalid (if x == self.imageSize[0])
            self.zooms[self.selectedZoom]['x'] = 0.
        self.zooms[self.selectedZoom]['y'] = self.zooms[self.selectedZoom]['y'] + dY / self.zooms[self.selectedZoom]['z']
        if self.zooms[self.selectedZoom]['y'] > self.imageSize[1]:
            # TODO this could still be invalid (if x == self.imageSize[0])
            self.zooms[self.selectedZoom]['y'] = self.imageSize[1]-1.
        if self.zooms[self.selectedZoom]['y'] < 0.:
            # TODO this could still be invalid (if x == self.imageSize[0])
            self.zooms[self.selectedZoom]['y'] = 0.
        self.lastLeftMouse = (x,y)
        #print "\tdeltas:", dX, dY
    
    # it doesn't look like I can get the scroll wheel through opengl
    
    
    
    # ================ ZoomView functions ===============
    
    def load_texture_from_string(self, imageData):
        self.imageData = imageData
        glEnable(GL_TEXTURE_2D)
        if self.imageTexture != None:
            glDeleteTextures(self.imageTexture)
        self.imageTexture = glGenTextures(1)
        
        # fill texture
        glColor4f(1.,1.,1.,1.)
        glBindTexture(GL_TEXTURE_2D, self.imageTexture)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE8, self.imageSize[0], self.imageSize[1],
                    0, GL_LUMINANCE, GL_UNSIGNED_BYTE, self.imageData) # RADAR GL_UNSIGNED_BYTE may be wrong
        glBindTexture(GL_TEXTURE_2D, 0)
        
        self.generate_zoomed_texture()
        
    
    def load_image(self, imageFilename):
        #glEnable(GL_TEXTURE_2D)
        #if self.imageTexture != None:
        #    # free the image
        #    glDeleteTextures(self.imageTexture)
        #self.imageTexture = glGenTextures(1)
        
        # load image (as color)
        image = PIL.Image.open(imageFilename).convert("RGB")
        self.imageSize = image.size
        
        glutSize = (glutGet(GLUT_WINDOW_WIDTH) , glutGet(GLUT_WINDOW_HEIGHT) )
        self.scale = max(glutSize[0]/float(self.imageSize[0]), glutSize[1]/float(self.imageSize[1]))
        #self.scale = scale = max(800./i.size[0], 600./i.size[1])
        
        #mSharpen = [[0.0, -1.0, 0.0],
        #            [-1.0, 5.0, -1.0],
        #            [0.0, -1.0, 0.0]]
        #
        #glConvolutionFilter2D(GL_CONVOLUTION_2D, GL_RGB, 3, 3, GL_LUMINANCE, GL_FLOAT, mSharpen);
        #glEnable(GL_CONVOLUTION_2D);
        
        # table = [(i / 256.)**10. for i in xrange(256)]
        # glColorTable(GL_COLOR_TABLE, GL_LUMINANCE, 256, GL_LUMINANCE, GL_FLOAT, table)
        # glEnable(GL_COLOR_TABLE)
        
        # fill texture
        #glColor4f(1.,1.,1.,1.)
        #glBindTexture(GL_TEXTURE_2D, self.imageTexture)
        #glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
        #glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
        #glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        #glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        #glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, image.size[0], image.size[1],
        #            0, GL_RGB, GL_UNSIGNED_BYTE, image.tostring()) # RADAR GL_UNSIGNED_BYTE may be wrong
        #glBindTexture(GL_TEXTURE_2D, 0)
        
        #self.imageData = image.tostring()
        
        #self.generate_zoomed_texture()
        self.load_texture_from_string(image.tostring())
    
    def change_contrast(self, deltaContrast):
        self.contrast += deltaContrast
        if self.contrast < 0.:
            self.contrast = 0.
        self.generate_zoomed_texture()
    
    def reset_contrast(self):
        if self.contrast != 1.:
            self.contrast = 1.
            self.generate_zoomed_texture()
    
    def generate_zoomed_texture(self):
        # # generate texture
        # if self.zoomTexture != None:
        #     glDeleteTextures(self.zoomTexture)
        # self.zoomTexture = glGenTextures(1)
        # 
        
        vShader = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vShader, """
        varying vec2 texture_coordinate;
        void main() {
            gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
            texture_coordinate = vec2(gl_MultiTexCoord0);
        }""")
        glCompileShader(vShader)
        
        fShader = glCreateShader(GL_FRAGMENT_SHADER)
        # a much better way to do this would be to use a glUniform
        # however, every time I call glGetUniformLocation, the program
        # segfaults
        glShaderSource(fShader, """
        vec4 contrast = vec4(%f,%f,%f,1.0);
        uniform sampler2D my_color_texture;
        varying vec2 texture_coordinate;
        void main() {
            gl_FragColor = texture2D(my_color_texture, texture_coordinate);
            gl_FragColor = pow(gl_FragColor, contrast);
        }""" % (self.contrast,self.contrast,self.contrast))
        glCompileShader(fShader)
        
        program = glCreateProgram()
        glAttachShader(program, vShader)
        glAttachShader(program, fShader)
        #print glGetProgramInfoLog(program)
        glLinkProgram(program)
        
        # print "Link status:", glGetProgramiv(program, GL_LINK_STATUS)
        # print glGetProgramInfoLog(program)
        # glValidateProgram(program)
        # print "Validate state:", glGetProgramiv(program, GL_VALIDATE_STATUS)
        # print "N Shaders:", glGetProgramiv(program, GL_ATTACHED_SHADERS)
        # print "Active Uniforms:", glGetProgramiv(program, GL_ACTIVE_UNIFORMS)
        # print glGetProgramInfoLog(program)
        # 
        # print "trying to find my_color_texture"
        # #self.shader_texture_loc = glGetUniformLocation(program, "my_color_texture")
        # print "found my_color_texture"
        # 
        # print "trying to find contrast"
        # self.shader_contrast_loc = c_int(1)
        # #self.shader_contrast_loc = glGetUniformLocation(program, "contrast")
        # print "found contrast"
        # if self.shader_contrast_loc in (None, -1):
        #     print "wtf?!?!?!?!?"
        
        #print glGetUniformLocation(program, "my_color_texture")
        
        self.shader = program
        # 
        # glColor4f(1.,1.,1.,1.)
        # glBindTexture(GL_TEXTURE_2D, self.zoomTexture)
        # glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
        # glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
        # glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        # glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        # 
        # # image processing
        # table = [(i / 256.)**self.contrast for i in xrange(256)]
        # glColorTable(GL_COLOR_TABLE, GL_LUMINANCE, 256, GL_LUMINANCE, GL_FLOAT, table)
        # glEnable(GL_COLOR_TABLE)
        # 
        # glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, self.imageSize[0], self.imageSize[1],
        #             0, GL_RGB, GL_UNSIGNED_BYTE, self.imageData) # RADAR GL_UNSIGNED_BYTE may be wrong
        # #glCopyTexImage2D(self.zoomTexture, 0, GL_RGB8, 0, 0, self.imageSize[0], self.imageSize[1], 0)
        # #glCopyTexImage2D(self.zoomTexture, 0, GL_RGB8, 0, 0, 256, 256, 0)
        # 
        # # clean up
        # glBindTexture(GL_TEXTURE_2D, 0)
        # glDisable(GL_COLOR_TABLE)
    
    # (-1,  1)    (1,  1)  |  (0,0)     (w,0)  | (0,0)   (1,0)
    #          gl          |       image       |      tex
    # (-1, -1)    (1, -1)  |  (0,h)     (w,h)  | (1,0)   (1,1)
    
    def _window_to_image(self, x, y):
        return x / self.scale, y / self.scale
    
    def _image_to_window(self, x, y):
        return x * self.scale, y * self.scale
    
    def _image_to_gl(self, x, y):
        return x * 2. / self.imageSize[0] - 1., y * -2. / self.imageSize[1] + 1.
    
    def _gl_to_image(self, x, y):
        return (x + 1.) / 2. * self.imageSize[0], (y + 1) / -2. * self.imageSize[1]
    
    def _image_to_tex(self, x, y):
        return x / float(self.imageSize[0]), y / float(self.imageSize[1])
    
    def _tex_to_image(self, x, y):
        return x * self.imageSize[0], y * self.imageSize[1]
    
    def get_zoom_locations(self):
        points = []
        for z in self.zooms:
            points.append([z['x'], z['y']])
        return points
    
    def add_zoomed_area(self, x=None, y=None, z=None, c=None):
        if x == None:
            x = 0.1
        if y == None:
            y = 0.1
        if z == None:
            if len(self.zooms):
                z = self.zooms[self.selectedZoom]['z']
            else:
                z = 1.
        if c == None:
            c = self._defaultZoomColors[len(self.zooms) % len(self._defaultZoomColors)]
        self.zooms.append({'x': x, 'y': y, 'z': z, 'c': c})
    
    def find_closest_zoom_distance(self, x, y):
        closest = -1
        dist = 1000000
        for (i, z) in enumerate(self.zooms):
            d = ((x - z['x']) ** 2 + (y - z['y']) ** 2) ** 0.5
            if d < dist:
                closest = i
                dist = d
        return dist, closest
    
    def find_closest_zoom_index(self, x, y):
        return self.find_closest_zoom_distance(x,y)[1]
        





def test_zoom_view(imageFilename, zooms=[]):
    # calculate size of image, and if window should be resized
    i = PIL.Image.open(imageFilename)
    scale = 1.
    if (i.size[0] * i.size[1]) > (800 * 600):
        scale = max(800./i.size[0], 600./i.size[1])
    elif (i.size[0] * i.size[1]) < (320 * 240):
        scale = max(320./i.size[0], 240./i.size[1])
    
    print "#Image: %s" % imageFilename
    
    print "#Image Width: %i, Height: %i" % i.size
    
    print "#Scaling image for display by: %05.3f" % scale
    
    width = i.size[0] * scale
    height = i.size[1] * scale
    
    print "#window Width: %i, Height: %i" % (int(width), int(height))
    del i
    
    print "#"
    print "# subpixel locations of reference points"
    print "#"
    
    print "# x y"
    
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(int(width), int(height))
    glutCreateWindow("glZoomView")
    glClearColor(0.,0.,0.,1.)
    
    zoomView = ZoomView()#scale)
    zoomView.load_image(imageFilename)
    for z in zooms:
        zoomView.add_zoomed_area(z['x'], z['y'], z['z'])
    
    for i, z in enumerate(zoomView.zooms):
        print "Zoom:", i, z
    
    def display():
        glClear(GL_COLOR_BUFFER_BIT)
        #print "drawing:", zoomView
        zoomView.draw()
        glutSwapBuffers()
        #glutPostRedisplay()
    
    glutDisplayFunc(display)
    
    def process_active_mouse_motion(x, y):
        zoomView.process_active_mouse_motion(x,y)
        glutPostRedisplay()
    glutMotionFunc(process_active_mouse_motion)
    
    def process_mouse_entry(state):
        zoomView.process_mouse_entry(state)
        #glutPostRedisplay()
    glutEntryFunc(process_mouse_entry)
    
    def process_mouse(button, state, x, y):
        zoomView.process_mouse(button, state, x, y)
        glutPostRedisplay()
    glutMouseFunc(process_mouse)
    
    def process_normal_keys(key, x, y):
        # if key == 'p':
        #     for z in zoomView.zooms:
        #         print "%.2f %.2f" % (z['x'], z['y'])
        if key == 'Q':
            #for z in zoomView.zooms:
            #    print "%.2f %.2f" % (z['x'], z['y'])
            sys.exit(0)
        zoomView.process_normal_keys(key, x, y)
        glutPostRedisplay()
    glutKeyboardFunc(process_normal_keys)
    
    # #glutPassiveMotionFunc(process_passive_mouse_motion)
    
    def process_menu(value):
        # 0 : does nothing
        # 1 : quits
        if value == 0:
            return value
        else:
            process_normal_keys(chr(value), 0, 0)
            return value # for some reason I have to return a value here, idk?
    
    glutCreateMenu(process_menu)
    #shortcutMenu = glutCreateMenu(process_menu)
    glutAddMenuEntry("--Keyboard Controls--", 0)
    glutAddMenuEntry("a : Add Zoomed Area", ord('a'))
    glutAddMenuEntry("d : Delete Zoomed Area", ord('d'))
    glutAddMenuEntry("z : Zoom In", ord('z'))
    glutAddMenuEntry("x : Zoom Out", ord('x'))
    glutAddMenuEntry("c : Increase Contrast", ord('c'))
    glutAddMenuEntry("C : Decrease Contrast", ord('C'))
    glutAddMenuEntry("r : Reset Contrast", ord('r'))
    
    #mouseMenu = glutCreateMenu(process_menu)
    glutAddMenuEntry("--Mouse Controls--", 0)
    glutAddMenuEntry("r : Open Menu", 0)
    glutAddMenuEntry("l : Select/Drag Zoomed Area", 0)
    
    #glutCreateMenu(process_menu)
    #glutAddSubMenu("Keyboard Shortcuts", shortcutMenu)
    #glutAddSubMenu("Mouse Controls", mouseMenu)
    glutAddMenuEntry("------", 0)
    glutAddMenuEntry("Q : Quit", ord('Q'))
    glutAttachMenu(GLUT_RIGHT_BUTTON)
    
    def print_zoom_view_uvs():
        for z in zoomView.zooms:
           print "%.2f %.2f" % (z['x'], z['y'])
    atexit.register(print_zoom_view_uvs)
    
    glutMainLoop()

if __name__ == '__main__':
    #zooms = [ {'x': 100.0, 'y': 100.0, 'z': 1.},
    #            {'x': 200.0, 'y': 200.0, 'z': 2.},
    #            {'x': 300.0, 'y': 300.0, 'z': 3.} ]
    zooms = []
    
    #testImagefile = "tests/test.png"
    testImagefile = "tests/H1_skull_2.jpg"
    
    if len(sys.argv) > 1:
        #print sys.argv
        testImagefile = sys.argv[1]
    
    test_zoom_view(testImagefile, zooms)