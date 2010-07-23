import scipy.ndimage as ndimage
import cv
import numpy
import matplotlib.pylab as plt

def array2cv(a):
    dtype2depth = {
        'uint8':   cv.IPL_DEPTH_8U,
        'int8':    cv.IPL_DEPTH_8S,
        'uint16':  cv.IPL_DEPTH_16U,
        'int16':   cv.IPL_DEPTH_16S,
        'int32':   cv.IPL_DEPTH_32S,
        'float32': cv.IPL_DEPTH_32F,
        'float64': cv.IPL_DEPTH_64F,
    }
    try:
        nChannels = a.shape[2]
    except:
        nChannels = 1
    
    cv_im = cv.CreateImageHeader((a.shape[1],a.shape[0]),
          dtype2depth[str(a.dtype)],
          nChannels)
    cv.SetData(cv_im, a.tostring(),
             a.dtype.itemsize*nChannels*a.shape[1])
    return cv_im

_NE = numpy.array([[0,0,1],[0,0,0],[0,0,0]])

# Filter kernels for calculating the value of neighbors in several directions 
_N  = numpy.array([[0, 1, 0], 
                   [0, 0, 0], 
                   [0, 1, 0]], dtype=bool) 

_NE = numpy.array([[0, 0, 1], 
                   [0, 0, 0], 
                   [1, 0, 0]], dtype=bool) 

_W  = numpy.array([[0, 0, 0], 
                   [1, 0, 1], 
                   [0, 0, 0]], dtype=bool) 

_NW = numpy.array([[1, 0, 0], 
                   [0, 0, 0], 
                   [0, 0, 1]], dtype=bool) 



# After quantizing the angles, vertical (north-south) edges get values of 3, 
# northwest-southeast edges get values of 2, and so on, as below: 
_NE_d = 0 
_W_d = 1 
_NW_d = 2 
_N_d = 3 


def canny(image, high_threshold, low_threshold): 
    grad_x = ndimage.sobel(image, 0) 
    grad_y = ndimage.sobel(image, 1) 
    grad_mag = numpy.sqrt(grad_x**2+grad_y**2) 
    
    grad_angle = numpy.arctan2(grad_y, grad_x) 
    # next, scale the angles in the range [0, 3] and then round to quantize 
    quantized_angle = numpy.around(3 * (grad_angle + numpy.pi) / (numpy.pi * 2)) 

    # Non-maximal suppression: an edge pixel is only good if its magnitude is 
    # greater than its neighbors normal to the edge direction. We quantize 
    # edge direction into four angles, so we only need to look at four 
    # sets of neighbors 
                     
    NE = ndimage.maximum_filter(grad_mag, footprint=_NE) 
    W  = ndimage.maximum_filter(grad_mag, footprint=_W) 
    NW = ndimage.maximum_filter(grad_mag, footprint=_NW) 
    N  = ndimage.maximum_filter(grad_mag, footprint=_N) 
    thinned = (((grad_mag > W)  & (quantized_angle == _N_d )) | 
         ((grad_mag > N)  & (quantized_angle == _W_d )) | 
         ((grad_mag > NW) & (quantized_angle == _NE_d)) | 
         ((grad_mag > NE) & (quantized_angle == _NW_d)) ) 
    thinned_grad = thinned * grad_mag 
    
    # Now, hysteresis thresholding: find seeds above a high threshold, then 
    # expand out until we go below the low threshold 
    high = thinned_grad > high_threshold 
    low = thinned_grad > low_threshold 
    canny_edges = ndimage.binary_dilation(high, structure=numpy.ones((3,3)), iterations=-1, mask=low) 
    return grad_mag, thinned_grad, canny_edges


def hough_line_segments(input_im, rho, theta, threshold, min_length, max_gap):

    cvim = array2cv(input_im)
    
    result = cv.HoughLines2(cvim, cv.CreateMemStorage(), cv.CV_HOUGH_PROBABILISTIC, rho, theta, threshold, min_length, max_gap)

    # unpack the results into something less terrible?
    
    return result