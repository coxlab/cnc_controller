#!/usr/bin/env python

import os, sys

from pylab import *
import pymorph as mm

frameDir = 'test_frames/49712223528793946'
seedLocs = [[700.61, 577.27],
            [798.16, 592.16],
            [925.60, 577.91]]

# frameDir = 'test_frames/49712223528793951'
# seedLocs = [[640.13, 518.21],
#             [768.14, 532.46],
#             [875.03, 514.42]]

kern = [[0, 0, 0, 1, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 1, 1, 1, 0, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 0],
        [1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1],
        [0, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 0, 1, 1, 1, 1, 1, 0, 0],
        [0, 0, 0, 1, 1, 1, 0, 0, 0]]
kern = array(kern)

windowSize = 15 # grab a 2Nx2N sub-image around each seed

def find_tc_refs(frame, seedLocs):
    """
    Method works well with dark spots on light background, need method for reverse, and other cases
    """
    im = imread(frame)
    locs = []
    for sloc in seedLocs:
        sim = im[sloc[1]-windowSize:sloc[1]+windowSize,sloc[0]-windowSize:sloc[0]+windowSize]
        sim -= sim.min()
        sim /= sim.max()
        sim = (sim * 255).astype('uint8')
        subplot(221)
        gray()
        imshow(sim)
        subplot(222)
        #cim = mm.close(sim,mm.sedisk(3))
        cim = mm.erode(sim,mm.sedisk(3)) # this almost works perfectly
        cim = mm.dilate(cim,mm.sedisk(3))
        imshow(cim)
        # stretch image
        cim = cim.astype(float)
        cim -= cim.min()
        cim /= cim.max()
        cim = (cim * 255).astype('uint8')
        subplot(223)
        bim = mm.binary(cim,128)
        cbim = mm.edgeoff(invert(bim))
        cbim = mm.areaopen(cbim,10)#mm.erode(cbim) # dilate to pick up small spots
        imshow(cbim,interpolation='nearest')
        subplot(224)
        lbls = mm.label(cbim)
        cs = mm.blob(lbls,'centroid')
        clbls = mm.label(cs)
        centroid = array(clbls).argmax()
        imshow(clbls,interpolation='nearest')
        subplot(221)
        slocs = divmod(centroid,cbim.shape[1])[::-1]
        print slocs
        scatter(*slocs)
        show()
        locs.append(sloc)
    return locs


if __name__ == '__main__':
    frames = [frameDir + '/' + f for f in os.listdir(frameDir) if '.png' in f] # get all png files in frameDir
    locs = []
    for frame in frames[:]:
        locs.append(find_tc_refs(frame,seedLocs))
    
    locs = array(locs) # [NFrames,NLocations,XY]