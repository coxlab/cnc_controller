from image_proc import canny, hough_line_segments, array2cv
from scipy.ndimage import binary_erosion, imread, map_coordinates, spline_filter, median_filter
from scipy import convolve
import scipy.optimize
import matplotlib.pylab as plt
import matplotlib.cm as cm
from numpy import *
from numpy.random import rand
from numpy.linalg import norm
from scipy.interpolate import interp2d


def find_electrode(im):
    # apply some sort of windowing / exclude irrelvant image pixels
    
    # apply a canny edge detector
    (grad_mag, thinned_grad, edge_im) = canny(im, 150, 50);

    # show the canny image
    if False:
        plt.imshow(edge_im)
        plt.colorbar()
        plt.show()
    
    # thin out the image a bit
    #sparser_edge_im = uint8(binary_erosion(edge_im)); 
    sparser_edge_im = uint8(128 * edge_im)
    
    # simple hough transform to find the electrode
    lines = hough_line_segments(sparser_edge_im, 1, 1*2*pi/360., 5, 40,10)
    
    # Assume that the one of interest is the one that is lowest and most to the right
    best_line = None
    
    
    # find the "lowest" point
    best_lowness = 0
    for l in lines:
        start_point = array(l[0])
        end_point = array(l[1])
        
        start_lowness = sum(start_point)
        end_lowness = sum(end_point)
        
        if(start_lowness > best_lowness):
            best_line = l
            best_lowness = start_lowness
            
        if(end_lowness > best_lowness):
            best_line = l
            best_lowness = end_lowness
            
        if((best_line == l) and (start_lowness > end_lowness)):
            best_line = (end_point, start_point)
            
    return best_line


def resample_slab(im, line, sample_width=20, sample_step=1, over_factor=1.5):
    
    e_start = array(line[0])
    e_end = array(line[1])
    
    # make sure that the points are arranged top to bottom
    if e_start[1] > e_end[1]:
        e_tmp = e_end
        e_end = e_start
        e_start = e_tmp
        
    
    e_center = (e_start + e_end)/2
    
    e_dir = e_end - e_start
    e_length = over_factor*norm(e_dir)
    e_dir = e_dir / norm(e_dir)
    
    arbitrary_vec = array([1, 0])
    
    e_ortho = arbitrary_vec - e_dir * dot(arbitrary_vec,e_dir)
    e_ortho = e_ortho / norm(e_ortho)
    
    
    
    # a grid of coorindates for the slab (slab-relative)
    (X_native, Y_native) = mgrid[0:e_length:sample_step, -sample_width:sample_width:sample_step]
    
    # convert the slab coordinates to image coordinates
    X_im = e_dir[0] * X_native + e_dir[1] * Y_native + e_center[0]
    Y_im = e_ortho[0] * X_native + e_ortho[1] * Y_native + e_center[1]
    
    # don't go over the edge
    for i in range(0, Y_im.shape[1]):
        row = Y_im[:,i]
        if any(row > im.shape[0]):
            X_im = X_im[:,0:i]
            Y_im = Y_im[:,0:i]
            break
        
    
    # look at the slab resampling
    if False:
        plt.imshow(im)
        plt.hold(True)
        for i in range(0, X_im.shape[0], 4):
            for j in range(0, X_im.shape[1], 4):
                plt.plot(X_im[i,j], Y_im[i,j], '*');
        plt.colorbar()
        plt.show()
    
    # Do the actual resampling
    coords = array([Y_im, X_im])
    transformed = map_coordinates(im, coords)
    transformed.shape = X_im.shape
    
    # Create a transform to get back to image coordinates
    return_transform = lambda c: e_center + c[1] * e_dir + (c[0] - sample_width) * e_ortho
    
    return (transformed, return_transform)



def estimate_tip_location_in_slab(slab):
    """ Estimate where the tip is in the slab, assuming that the slab is oriented correctly
    """
    
    cross_section = mean(slab, 0)
    center_axis = argmax(cross_section)
    trough_depth = min(cross_section)
    
    width = 3
    flank_width = 10
    center_slice = mean(slab[:, center_axis-width:center_axis+width], 1) 
    left_flank = mean(slab[:, 0:center_axis-flank_width], 1)
    right_flank = mean(slab[:, center_axis+flank_width:], 1)
    
    
    normalized_center_slice = center_slice -  (left_flank + right_flank)/2
    
    if False:
        plt.plot(cross_section)
        plt.title("Cross section - ")
        plt.show()
    
    
    # determine the noise level for the background
    background_offset = 50
    background_std = std(normalized_center_slice[-background_offset:])
    
    tip_cutoff = -1
    for t in range(background_offset, len(normalized_center_slice)):
        
        val = normalized_center_slice[-t]
        if val > 3 * background_std:
            tip_cutoff = len(normalized_center_slice) - t
            break
    
    if False:
        plt.plot(normalized_center_slice)
        plt.title("Center slice - ")
        plt.hold(True)
        plt.plot(tip_cutoff, 0, 'r*')
        plt.show()

    
    
    return (array([center_axis,tip_cutoff]), trough_depth)


def electrode_alignment_objective(params, im, line_segment):
    try:
        a = params[0]
    except:
        a = params
    
    print "Evaluating angle = ", a
    theta = a * pi / 180.
    e_start = array(line_segment[0])
    e_end = array(line_segment[1])
    
    e_dir = e_end - e_start
    
    new_dir = dot(array([[cos(theta),-sin(theta)],[sin(theta), cos(theta)]]), e_dir)
    
    # print e_start
    # print e_end
    # print e_start + new_dir
    
    line_segment = (e_start, e_start + new_dir)
    
    (slab, to_image_coords) = resample_slab(im, line_segment)
    (tip, trough) = estimate_tip_location_in_slab(slab)
    
    if False:
        plt.imshow(slab, cmap=cm.gray)
        plt.hold(True)
        plt.plot(tip[0], tip[1], 'r*')
        plt.show()
    
    return (-trough, to_image_coords(tip))

def find_electrode_tip(im, line_segment):
    
    (slab, to_image_coords) = resample_slab(im, line_segment)
    (tip, trough_depth) = estimate_tip_location_in_slab(slab)
    
    # plot the slab and the electrode tip estimate
    if False:
        plt.imshow(slab)
        plt.hold(True)
        plt.plot(tip[0], tip[1], 'r*')
        plt.show()
    
    return to_image_coords(tip)


def find_electrode_tip_with_refinement(im, base_im, angle_range, angle_resolution):
    diff_im = abs(im - base_im)
    diff_im = median_filter(diff_im, 4)
    
    
    l = find_electrode(diff_im)
    tip = find_electrode_tip(diff_im, l)
    
    a = scipy.optimize.brute(lambda a: electrode_alignment_objective(a, diff_im, l)[0], ranges=(slice(-7,7,.25),))
    print "a=", a
    (trough, new_tip) = electrode_alignment_objective(a[0], diff_im, l)
    
    return new_tip
    

if __name__ == "__main__":
    
    #load a test image
    base_dir = "/Users/davidcox/Desktop/electrode_tip/1/0/"
    base_im = double(imread(base_dir + "4.png"))
    im = double(imread(base_dir + "13.png"))
   
    tip = find_electrode_tip_with_refinement(im, base_im, (-7,7), 0.25)
    
    
    plt.imshow(im, cmap=cm.gray)
    plt.hold(True)
    plt.plot(tip[0], tip[1], 'r*')
    plt.show()

