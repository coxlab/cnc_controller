#!/usr/bin/env python

from pylab import *

import stopwatch

def find_crossing(arr, threshold):
    pts = where(arr < threshold)[0]
    if len(pts):
        return pts[-1]
    else:
        return -1

def calc_thresh(im, yLimits):
    clip = im[yLimits[0]:yLimits[1]]
    return mean(clip) - std(clip) * 2.

@stopwatch.clockit
def find_tip(im, yLimits, threshold=None, stripDims=[100,20]):
    t = stopwatch.Timer()
    clip = im[yLimits[0]:yLimits[1]]
    print str(t), "Post Clip"
    if threshold == None: # this is slow, maybe just do it one per camera (or exposure setting)
        threshold = calc_thresh(im, yLimits)#mean(clip) - std(clip) * 2.
    print str(t), "Post Thresh Calc"
    col = clip.min(1)
    y = find_crossing(col, threshold)
    print str(t), "Post y-crossing"
    if y == -1 or y-stripDims[0] < 0 or y+stripDims[1]+1 > clip.shape[0]:
        return -1, -1
    row = clip[y-stripDims[0]:y+stripDims[1]].min(0)
    x = find_crossing(row, threshold)
    print str(t), "Post x-crossing"
    if x == -1:
        return -1, -1
    return x, y + yLimits[0]
    # row = clip.min(0)
    # col = clip.min(1)
    # if threshold == None:
    #     threshold = mean(clip) - std(clip) * 3.
    #     print threshold
    # pxs = where(row < threshold)[0]
    # pys = where(col < threshold)[0] + yLimits[0]
    # if len(pxs) and len(pys):
    #     
    #     return pxs[-1], pys[-1]
    # else:
    #     return -1, -1


if __name__ == '__main__':
    import glob
    baseDir = "/Volumes/vnsl/cncLogs/1295986493/cameras/"
    nFiles = 5
    for uuid in (49712223528793946, 49712223528793951):
        imDir = baseDir + '/' + str(uuid) + '/'
        imFiles = glob.glob(imDir+'/*.png')
        assert len(imFiles)
        if len(imFiles) > nFiles:
            imFiles = imFiles[:nFiles]
        t = None
        for fn in imFiles:
            im = double(imread(fn))
            yLimits = {49712223528793946: [206, 763],
                        49712223528793951: [190, 755]}
            
            if t == None:
                t = calc_thresh(im, yLimits[uuid])
            x,y = find_tip(im, yLimits[uuid])#, t)
            
            figure()
            imshow(im, cmap=cm.gray, interpolation='nearest')
            title("%i/%s" % (uuid, fn))
            plot(x, y, 'r*')
    show()