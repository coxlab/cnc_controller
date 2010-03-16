#!/usr/bin/env python

from Foundation import *
from AppKit import *
import objc
from objc import IBAction, IBOutlet

from OpenGL.GL import *

import cameraPair
import cfg

class ImageBridge (NSObject):
    # need outlets to the 2 opengl views
    # initialization
    leftImageView = objc.IBOutlet()
    rightImageView = objc.IBOutlet()
    
    registrationPointTableView = objc.IBOutlet()
    
    def awakeFromNib(self):
        # create camera pair
        self.cameras = cameraPair.CameraPair()
        
        self.points = [{'lx': 0, 'ly': 0, 'rx': 0, 'ry': 0,
                        'x': 0, 'y': 0, 'z': 0, 'c': 0},]
    
    @IBAction
    def captureCalibrationImage_(self, sender):
        gridSize = cfg.gridSize if ('gridSize' in dir(cfg)) else (8,5)
        gridBlockSize = cfg.gridBlockSize if ('gridBlockSize' in dir(cfg)) else 2.73
        ims, success = self.cameras.capture_calibration_images(gridSize, gridBlockSize)
        #im1, im2, success = self.cameras.capture_calibration_images()
        self._.leftImageView.update_image(ims[0][0])
        self._.rightImageView.update_image(im[1][0])
        print "Calibration Images are:", success
    
    @IBAction
    def calibrateCameras_(self, sender):
        gridSize = cfg.gridSize if ('gridSize' in dir(cfg)) else (8,5)
        gridBlockSize = cfg.gridBlockSize if ('gridBlockSize' in dir(cfg)) else 2.73
        self.cameras.calibrate(gridSize, gridBlockSize)
    
    @IBAction
    def addZoomedAreas_(self, sender):
        self.leftImageView.add_zoomed_area(0.5, 0.5)
        self.leftImageView.scheduleRedisplay()
        self.rightImageView.add_zoomed_area(0.5, 0.5)
        self.rightImageView.scheduleRedisplay()
        self.update_bindings()
    
    def update_bindings(self):
        """ force the table to update """
        #self.print_zoom_xys()
        self.update_points()
        self.registrationPointTableView.reloadData()
    
    def print_zoom_xys(self):
        for i in xrange(len(self.leftImageView.zooms)):
            l = self.leftImageView.zooms[i]
            r = self.rightImageView.zooms[i]
            w = self.leftImageView.frame_width
            h = self.leftImageView.frame_height
            print "%f %f %f %f" % (l['x']*w, l['y']*h, r['x']*w, r['y']*h)
    
    @IBAction
    def connectToCameras_(self, sender):
        self.cameras.connect()
    
    @IBAction
    def loadCalibration_(self, sender):
        #TODO add this to the configuration file
        calibrationDirectory = '/Users/graham/Repositories/coxlab/cncController/stereoCalibration'
        if 'calibrationDirectory' in dir(cfg):
            calibrationDirectory = cfg.calibrationDirectory
        
        self.cameras.load_calibrations(calibrationDirectory)
        #self.cameras.compute_rectify_matricies((1280,960))
    
    @IBAction
    def captureFrames_(self, sender):
        im1, im2 = self.cameras.capture()
        self._.leftImageView.update_image(im1)
        self._.rightImageView.update_image(im2)
    
    
    # data source methods to make this NSTableView complient
    def numberOfRowsInTableView_(self, view):
        return len(self.leftImageView.zooms)
    
    def update_points(self):
        self.points = []
        for i in xrange(len(self.leftImageView.zooms)):
            lx = self.leftImageView.zooms[i]['x'] * self.cameras.cameras[0].imageSize[0]
            ly = self.leftImageView.zooms[i]['y'] * self.cameras.cameras[0].imageSize[1]
            rx = self.rightImageView.zooms[i]['x'] * self.cameras.cameras[1].imageSize[0]
            ry = self.rightImageView.zooms[i]['y'] * self.cameras.cameras[1].imageSize[1]
            x, y, z = self.cameras.get_3d_position(( (lx,ly), (rx,ry) ))
            self.points.append({'lx': lx, 'ly': ly, 'rx': rx, 'ry': ry,
                'x': x, 'y': y, 'z': z, 'c': self.leftImageView._defaultZoomColorNames[i]})
    
    def tableView_objectValueForTableColumn_row_(self, view, column, row):
        col = column.identifier()
        return self.points[row][col]


class CVImageViewer (NSOpenGLView):
    
    _defaultZoomColors = cfg.zoomColors
    
    _defaultZoomColorNames = cfg.zoomColorNames
    
    _zhw = cfg.zoomHalfWidth
    
    imageBridge = objc.IBOutlet()
    
    def _to_gl(self, x, y):
        return x*2.-1., y*2.-1.
    
    def awakeFromNib(self):
        self.gl_inited = False
        self.image = None
        self.zooms = []
        self.add_zoomed_area(0.5, 0.5)
        self.selectedZoom = 0
        #for i in xrange(3):
        #    self.add_zoomed_area()
        #self.add_zoomed_area({'x': 0.25, 'y': 0.5, 'z': 1., 'c': (1., 0., 0., 0.5)})
        #self.add_zoomed_area({'x': 0.5, 'y': 0.5, 'z': 1., 'c': (0., 1., 0., 0.5)})
        #self.add_zoomed_area({'x': 0.75, 'y': 0.5, 'z': 1., 'c': (0., 0., 1., 0.5)})
        #self.selectedZoom = 0
        #self.zoomedX = 0.5
        #self.zoomedY = 0.5
        #self.zoom = 1.
        #self.acceptsFirstResponder()
        #self.becomeFirstResponder()
    
    #def mouseEntered_(self, event):
    #    print event
    
    #def mouseExited_(self, event):
    #    print event
    
    def add_zoomed_area(self, x=None, y=None, z=None, c=None):
        if x == None:
            x = 0.1
        if y == None:
            y = 0.1
        if z == None:
            z = 1.
        if c == None:
            c = self._defaultZoomColors[len(self.zooms) % len(self._defaultZoomColors)]
        self.zooms.append({'x': x, 'y': y, 'z': z, 'c': c})
    
    def select_closest_zoom(self, x, y):
        closest = 0
        dist = 1000000
        for (i, z) in enumerate(self.zooms):
            #print "x:", pos.x, "y:", pos.y
            #print "zx:", z['x'], "y:", z['y']
            d = ((x - z['x']) ** 2 + (y - z['y']) ** 2) ** 0.5
            if d < dist:
                closest = i
                dist = d
            #print d
        self.selectedZoom = closest
    
    def scrollWheel_(self, event):
        # select the zoomed window closest to the click position
        pos = self.convertPoint_fromView_(event.locationInWindow(), None)
        self.select_closest_zoom(pos.x/self.frame_width, pos.y/self.frame_height)
        
        # update zoom
        dZoom = event.deltaY()
        if dZoom > 0:
            # zoom in
            #print "zoom in:", dZoom
            self.zooms[self.selectedZoom]['z'] *= dZoom+1.
        elif dZoom < 0:
            # zoom out
            #print "zoom out:", dZoom
            self.zooms[self.selectedZoom]['z'] /= abs(dZoom)+1
        if self.zooms[self.selectedZoom]['z'] < 1.0:
            self.zooms[self.selectedZoom]['z'] = 1.0
        if self.zooms[self.selectedZoom]['z'] > 100.:
            self.zooms[self.selectedZoom]['z'] = 100.
        self.scheduleRedisplay()
    
    def mouseDown_(self, event):
        # select the zoomed window closest to the click position
        pos = self.convertPoint_fromView_(event.locationInWindow(), None)
        self.select_closest_zoom(pos.x/self.frame_width, pos.y/self.frame_height)
        self.scheduleRedisplay()
    
    def mouseUp_(self, event):
        pass
    
    def mouseDragged_(self, event):
        dx = event.deltaX() / (self.frame_width * self.zooms[self.selectedZoom]['z'])
        dy = -event.deltaY() / (self.frame_height * self.zooms[self.selectedZoom]['z'])
        #self.zoomedX += dx
        #self.zoomedY += dy
        self.zooms[self.selectedZoom]['x'] += dx
        self.zooms[self.selectedZoom]['y'] += dy
        #print self.zooms[self.selectedZoom]['x'], self.zooms[self.selectedZoom]['y']
        #print self.zoomedX, self.zoomedY
        self.scheduleRedisplay()
        
        # calculate position on image: bottom left = 0,0
        #print("Cross at position:", self.image.width * self.zoomedX,
        #            self.image.height * self.zoomedY)
    
    def rightMouseDown_(self, event):
        pass
    
    def rightMouseUp_(self, event):
        #pos = self.convertPoint_fromView_(event.locationInWindow(), None)
        #self.add_zoomed_area(pos.x/self.frame_width, pos.y/self.frame_height)
        #self.scheduleRedisplay()
        pass
    
    def rightMouseDragged_(self, event):
        pass
    
    #def mouseMoved_(self, event):
    #    print event
    
    def update_image(self, image):
        self.image = image
        self.scheduleRedisplay()
    
    def draw_image(self):
        texture = glGenTextures(1)
        
        glColor4f(1.,1.,1.,1.)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE8, self.image.width, self.image.height,
                    0, GL_LUMINANCE, GL_UNSIGNED_BYTE, self.image.tostring())
        glBindTexture(GL_TEXTURE_2D, texture)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0) 
        glVertex3f(-1., 1.,  0.0) # Bottom Left
        glTexCoord2f(1.0, 0.0)
        glVertex3f( 1., 1.,  0.0) # Bottom Right
        glTexCoord2f(1., 1.)
        glVertex3f( 1.0,  -1.0,  0.0) # Top Right
        glTexCoord2f(0.0, 1.0)
        glVertex3f(-1.0,  -1.0,  0.0) # Top Left
        glEnd()
        glBindTexture(GL_TEXTURE_2D, 0)
        
        glDeleteTextures(texture)
    
    def draw_zoomed_crosshairs(self, index):
        #print "draw zoomed crosshairs"
        #zhw = 0.1
        #def to_gl(x,y):
        #    return x*2.-1., y*2.-1.
        
        zx = self.zooms[index]['x']
        zy = self.zooms[index]['y']
        #zz = self.zooms[index]['z']
        
        glColor4f(*self.zooms[index]['c'])
        glBegin(GL_LINES)
        
        glVertex2f(*self._to_gl(zx, zy-self._zhw))
        glVertex2f(*self._to_gl(zx, zy+self._zhw))
        
        glVertex2f(*self._to_gl(zx-self._zhw, zy))
        glVertex2f(*self._to_gl(zx+self._zhw, zy))
        glEnd()
    
    def draw_zoomed_border(self, index):
        #zhw = 0.1
        #def to_gl(x,y):
        #    return x*2.-1., y*2.-1.
        
        zx = self.zooms[index]['x']
        zy = self.zooms[index]['y']
        
        glColor4f(*self.zooms[index]['c'])
        glBegin(GL_LINE_STRIP)
        glVertex2f(*self._to_gl(zx-self._zhw, zy-self._zhw))
        glVertex2f(*self._to_gl(zx-self._zhw, zy+self._zhw))
        glVertex2f(*self._to_gl(zx+self._zhw, zy+self._zhw))
        glVertex2f(*self._to_gl(zx+self._zhw, zy-self._zhw))
        glVertex2f(*self._to_gl(zx-self._zhw, zy-self._zhw))
        glEnd()
    
    def draw_zoomed_image(self, index):
        #print "draw zoomed image"
        texture = glGenTextures(1)
        
        glColor4f(1.,1.,1.,1.)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)#GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)#GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE8, self.image.width, self.image.height,
                    0, GL_LUMINANCE, GL_UNSIGNED_BYTE, self.image.tostring())
        glBindTexture(GL_TEXTURE_2D, texture)
        
        
        # zoomed coords: 0,0 = bottom left, 1,1 = top right
        # texture coords: 0,0 = bottom left, 1,1 = top right
        # opengl coords: -1,-1 = bottom left, 1,1 = top right 
        #zhw = 0.1 # zoom window half width
        #self.zoom = 10.
        #def to_gl(x,y):
        #    return x*2.-1., y*2.-1.
        
        zx = self.zooms[index]['x']
        zy = self.zooms[index]['y']
        zz = self.zooms[index]['z']
        zc = self.zooms[index]['c']
        
        glBegin(GL_QUADS)
        # bottom left
        glTexCoord2f(zx - self._zhw/zz, 1 - zy + self._zhw/zz)
        gx,gy = self._to_gl(zx-self._zhw, zy-self._zhw)
        glVertex3f(gx, gy, 0.)
        
        # bottom right
        glTexCoord2f(zx + self._zhw/zz, 1 - zy + self._zhw/zz)
        gx,gy = self._to_gl(zx+self._zhw, zy-self._zhw)
        glVertex3f(gx, gy, 0.)
        
        # top right
        glTexCoord2f(zx + self._zhw/zz, 1 - zy - self._zhw/zz)
        gx,gy = self._to_gl(zx+self._zhw, zy+self._zhw)
        glVertex3f(gx, gy, 0.)
        
        # top left
        glTexCoord2f(zx - self._zhw/zz, 1 - zy - self._zhw/zz)
        gx,gy = self._to_gl(zx-self._zhw, zy+self._zhw)
        glVertex3f(gx, gy, 0.)
        glEnd()
        glBindTexture(GL_TEXTURE_2D, 0)
        
        glDeleteTextures(texture)
        
        #glBegin(GL_QUADS)
        ## bottom left
        #glTexCoord2f(self.zoomedX - zhw/self.zoom, 1 - self.zoomedY + zhw/self.zoom)
        #gx,gy = to_gl(self.zoomedX-zhw, self.zoomedY-zhw)
        #glVertex3f(gx, gy, 0.)
        #
        ## bottom right
        #glTexCoord2f(self.zoomedX + zhw/self.zoom, 1 - self.zoomedY + zhw/self.zoom)
        #gx,gy = to_gl(self.zoomedX+zhw, self.zoomedY-zhw)
        #glVertex3f(gx, gy, 0.)
        #
        ## top right
        #glTexCoord2f(self.zoomedX + zhw/self.zoom, 1 - self.zoomedY - zhw/self.zoom)
        #gx,gy = to_gl(self.zoomedX+zhw, self.zoomedY+zhw)
        #glVertex3f(gx, gy, 0.)
        #
        ## top left
        #glTexCoord2f(self.zoomedX - zhw/self.zoom, 1 - self.zoomedY - zhw/self.zoom)
        #gx,gy = to_gl(self.zoomedX-zhw, self.zoomedY+zhw)
        #glVertex3f(gx, gy, 0.)
        #glEnd()
        #glBindTexture(GL_TEXTURE_2D, 0)
        #
        #glDeleteTextures(texture)
    
    def initGL(self):
        glEnable(GL_BLEND)
        glEnable(GL_TEXTURE_2D)
        glDisable(GL_LIGHTING)
        #glBlendFunc(GL_ONE, GL_ZERO)
        #glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        #glBlendFunc(GL_ONE_MINUS_DST_ALPHA, GL_DST_ALPHA)
        glPixelStorei(GL_UNPACK_ALIGNMENT,1)
        #self.gl_inited = True
    
    def scheduleRedisplay(self):
        """Call to force redisplay of the opengl view"""
        self.setNeedsDisplay_(True)
    
    def drawRect_(self, frame):
        """Display function"""
        if not self.canDraw():
            print "cannot draw: self.canDraw() == False"
            #self.openGLContext().flushBuffer()
            return
            
        if self.gl_inited == False:
            self.initGL()
            pass
        
        frame = self.frame()
        self.frame_width = frame.size.width
        self.frame_height = frame.size.height
        
        glViewport(0, 0, int(self.frame_width), int(self.frame_height))
        #glOrtho(0, 1., 0, 1.,-1.,1.)
    
        glClear(GL_COLOR_BUFFER_BIT)
        if(self.image == None):
            print "No image"
            self.openGLContext().flushBuffer()
            return
        
        self.draw_image()
        
        for i in xrange(len(self.zooms)):
            if i == self.selectedZoom:
                continue
            self.draw_zoomed_image(i)
            self.draw_zoomed_crosshairs(i)
        
        self.draw_zoomed_image(self.selectedZoom)
        self.draw_zoomed_crosshairs(self.selectedZoom)
        self.draw_zoomed_border(self.selectedZoom)
        
        self.imageBridge.update_bindings()
        
        self.openGLContext().flushBuffer()