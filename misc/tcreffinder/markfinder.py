#!/usr/bin/env python

from pylab import *
import pymorph

# seeds from cfg file
lSeeds = [[643.27451781, 522.57654614],
                        [771.47429952, 536.68860298],
                        [877.61847028, 517.71243038]]

rSeeds = [[703.82119604, 578.75227713],
                        [802.02238616, 594.22537199],
                        [928.36786805, 578.5496978]]

# get images
NImages = 9#9
lImages = ['testImages/left/%i.png' % i for i in xrange(NImages)]
rImages = ['testImages/right/%i.png' % i for i in xrange(NImages)]

winSize = 32
halfWinSize = winSize/2

for i in xrange(NImages):
    figure()
    gray()
    lImg = (imread(lImages[i]) * 255).astype('uint8')
    rImg = (imread(rImages[i]) * 255).astype('uint8')
    lImg = pymorph.open(lImg, pymorph.sedisk(6))
    rImg = pymorph.open(rImg, pymorph.sedisk(6))
    for j in xrange(3):
        xBound = int(lSeeds[j][0]-halfWinSize)
        yBound = int(lSeeds[j][1]-halfWinSize)
        lclip = lImg[yBound:yBound+winSize,xBound:xBound+winSize]
        #print "left clip shape:", lclip.shape
        xBound = int(rSeeds[j][0]-halfWinSize)
        yBound = int(rSeeds[j][1]-halfWinSize)
        rclip = rImg[yBound:yBound+winSize,xBound:xBound+winSize]
        #print "right clip shape:", rclip.shape
        
        # clipDir = 'testImages/clips/'#%i/' % i
        # if not os.path.exists(clipDir):
        #     os.makedirs(clipDir)
        # imsave('%s%il%i.png' % (clipDir, i, j),lclip)
        # imsave('%s%ir%i.png' % (clipDir, i, j),rclip)
        # 
        # radii = arange(3,8)#linspace(9,13,10)
        # alpha = 2 # 2: from paper (Loy and Zelinsky), 10: from eyetracker
        # lS = ip.fast_radial_transform(lclip,radii,alpha)
        # rS = ip.fast_radial_transform(rclip,radii,alpha)
        # 
        # border = 7
        # lS = lS[border:-border,border:-border]
        # rS = rS[border:-border,border:-border]
        # 
        # lCenter = array(divmod(abs(lS).argmax(),lS.shape[1]))
        # rCenter = array(divmod(abs(rS).argmax(),rS.shape[1]))
        # 
        # print "Left:", lCenter
        # print "Right:", rCenter
        
        
        subplot(231+j)
        imshow(lclip)#[border:-border,border:-border])
        #imshow(lS)
        #scatter(*lCenter)
        subplot(234+j)
        imshow(rclip)#[border:-border,border:-border])
        #imshow(rS)
        #scatter(*rCenter)

show()
