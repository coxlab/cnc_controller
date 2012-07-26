#!/usr/bin/env python

# test script to try and speed up remapping of images
#  1) pick two points on the images
#  2) generate a new images that is the rotated, resampled version


# setup and generate opengl window (glumpy maybe?)

# load image and display

# select two points

# generate new image in new window?


from PIL import Image

#from pylab import *
import numpy, glumpy

bw, bh = 640, 480
sw, sh = 320, 240
tw, th = bw, bh+sh
window = glumpy.Window(tw,th) # half size


im = numpy.asarray(Image.open('test_images/1.png'))


I = glumpy.Image(im, format='L', cmap=glumpy.colormap.Grey, interpolation='bicubic')
ON = glumpy.Image(numpy.zeros((sh,sw), dtype='uint8'), cmap=glumpy.colormap.IceAndFire, interpolation='nearest')
OC = glumpy.Image(numpy.zeros((sh,sw), dtype='uint8'), cmap=glumpy.colormap.IceAndFire, interpolation='bicubic')

shape, items = glumpy.layout([ [(ON, 2), (OC, 2)],
                                [I, '-'] ], padding=0, border=0)

print shape, items

#window.set_size(int(shape[0]*tw), int(shape[1]*tw))#int(shape[0]*th), int(shape[1]*tw))
window.set_size(tw,th)

@window.event
def on_mouse_motion(x,y,dx,dy):
    global im, I, ON, OC, bw, bh, sw, sh, tw, th, shape
    i,x0,y0,w,h = items[0]
    print x, y, dx, dy
    x0, y0 = x0*th*shape[0], y0*tw*shape[1]
    w, h = w*tw*shape[0]-1, h*th*shape[1]+1
    x = min(max(x-x0,0),w)/float(w)*bw
    y = (1-min(max(y-y0,0),h)/float(h))*bh
    x = max(min(x,bw-sw//2),sw//2)
    y = max(min(y,bh-sh//2),sh//2)
    ON.data[...] = I.data[y-sh//2:y+sh//2, x-sw//2:x+sw//2]
    OC.data[...] = I.data[y-sh//2:y+sh//2, x-sw//2:x+sw//2]
    window.draw()

@window.event
def on_draw():
    global tw, th, items
    window.clear()
    for item in items:
        img,x,y,w,h = item
        x,y = x*th*shape[0], y*tw*shape[1]
        w,h = w*th*shape[0]-1, h*tw*shape[1]+1
        img.update()
        img.blit(x,y,w,h)

window.mainloop()
