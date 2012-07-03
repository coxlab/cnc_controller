#!/usr/bin/env python

import numpy
import pylab

import scipy.ndimage

import skimage
import skimage.io
import skimage.filter
import skimage.morphology

# defs
bgfn = 'background_images/0/0.png'
imfns = ['test_images/0/%i.png' % i for i in xrange(9)]
locfn = 'test_images/tip_locations.txt'

tl = (200, 206)
br = (800, 670)

show = True
global cx, cy
cx = None
cy = None


def coarse_find(image, tl, br, threshold=0.5):
    x0, y0 = tl
    x1, y1 = br
    bim = image[y0:y1, x0:x1] < threshold  # probe is dark
    return numpy.max(numpy.where(numpy.max(bim, 0))) + x0, \
            numpy.max(numpy.where(numpy.max(bim, 1))) + y0


def clip_to_seed(image, x, y, d):
    if show:
        global cx, cy
        cx, cy = x - d, y - d
        pylab.plot(x, y, 'b.')
    return image[y - d: y + d, x - d: x + d]


def denoise(image, **kwargs):
    kwargs['weight'] = kwargs.get('weight', 0.05)
    return skimage.filter.tv_denoise(image, **kwargs)


def binarize(image, threshold=None):
    if threshold is None:
        threshold = (image.min() + image.max()) / 2.
    return image < threshold  # probe is dark


def skeletonize(image):
    return skimage.morphology.skeletonize(image)


def find_seed_points(x, y, skel_image):
    ys, xs = numpy.where(skel_image)
    sds = ((xs - x) ** 2. + (ys - y) ** 2.).argsort()[::-1]
    if show:
        sxs = numpy.take(xs, sds)
        sys = numpy.take(ys, sds)
        global cx, cy
        pylab.plot(sxs + cx, sys + cy, 'g.')
        return sxs, sys
    return numpy.take(xs, sds), numpy.take(ys, sds)


def resample(image, sx, sy, ex, ey):
    if ex - sx == 0:
        return
    m = (ey - sy) / float(ex - sx)
    if m == 0:
        return
    b = sy - m * sx
    ty, by = (10, image.shape[0] - 10)
    top = ((ty - b) / m, ty)
    bottom = ((by - b) / m, by)
    # generate coordinates on line
    xs = numpy.linspace(top[0], bottom[0], 1000, False)
    ys = numpy.linspace(top[1], bottom[1], 1000, False)
    return scipy.ndimage.interpolation.map_coordinates(image, [xs, ys]), xs, ys


def find_tip(image, sx, sy, ex, ey, threshold=None):
    values, xs, ys = resample(image, sx, sy, ex, ey)
    bg = values[-100:]
    mi = values.argmin()
    m = numpy.mean(bg)
    #m, s = numpy.mean(bg), numpy.std(bg)
    pis = numpy.where(values[mi:] >= m)[0]
    #m, s = numpy.mean(bg), numpy.std(bg)
    #pis = numpy.where(values < m - s * 3)[0]
    if len(pis) == 0:
        return None, None
    #i = numpy.max(pis)
    i = numpy.min(pis) + mi
    if show:
        pylab.figure('line')
        pylab.plot(values)
        #pylab.axhline(m - s * 3)
        pylab.axhline(m)
        pylab.figure('image')
        #global cx, cy
        #pylab.plot(xs + cx, ys + cy, 'b.')
    return xs[i], ys[i]


def culled_mean(xs, ys):
    xs = numpy.array(xs)
    ys = numpy.array(ys)
    nbp = 10
    while nbp > 3:
        x, y = numpy.mean(xs), numpy.mean(ys)
        d = (xs - x) ** 2. + (ys - y) ** 2.
        m, s = numpy.mean(d), numpy.std(d)
        gi = numpy.where(numpy.abs(d) < m + s * 5.)[0]
        nbp = len(xs) - len(gi)
        cxs, cys = xs[gi], ys[gi]
    return x, y
    #return numpy.mean(xs), numpy.mean(ys)


def process(image, tl, br, d):
    x, y = coarse_find(image, tl, br)
    cim = clip_to_seed(image, x, y, d)
    mid = d
    sxs, sys = find_seed_points(mid, mid, \
            skeletonize(binarize(denoise(cim))))
    txs = []
    tys = []
    half = int(numpy.floor(len(sxs) / 2.))
    ex = numpy.mean(sxs[-half:])
    ey = numpy.mean(sys[-half:])
    for si in xrange(half):
    #for si in xrange(len(sxs) / 2, len(sxs)):
        sx = sxs[si]
        sy = sys[si]
        # TODO don't use mid, just use the skeletonized points
        #tx, ty = find_tip(cim, sx, sy, mid, mid)
        tx, ty = find_tip(cim, sx, sy, ex, ey)
        if (tx is not None) and (ty is not None):
            txs.append(tx + x - d)
            tys.append(ty + y - d)
    if show:
        pylab.plot(txs, tys, 'm.')
        tx, ty = culled_mean(txs, tys)
        pylab.plot(tx, ty, 'rx')
        return tx, ty
    return culled_mean(txs, tys)


def load_data():
    # loading
    bg = skimage.img_as_float(skimage.io.imread(bgfn))
    ims = [skimage.img_as_float(skimage.io.imread(imfn)) for imfn in imfns]

    locs = pylab.loadtxt(locfn)
    lxs = locs[:, 0]
    lys = locs[:, 1]
    return ims, bg, lxs, lys

if __name__ == '__main__':
    print "Target is a red +, Guess is a red x"
    ims, _, lxs, lys = load_data()
    # image processing
    for (i, im) in enumerate(ims):
        pylab.figure('image')
        pylab.imshow(im, interpolation='nearest', cmap=pylab.cm.gray)
        tx, ty = process(im, tl, br, 50)
        print tx, ty, lxs[i], lys[i], \
                ((tx - lxs[i]) ** 2. + (ty - lys[i]) ** 2.) ** 0.5
        #pylab.close('all')
        pylab.plot(lxs[i], lys[i], 'r+')
        pylab.show()

    pylab.show()
