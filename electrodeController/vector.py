#!/usr/bin/env python

from numpy import *
from pylab import norm
from scipy import optimize

# what coordinates should I use????????????????
# +x = east: about x = attitude (pitch)
# +y = north: about y = bank (roll)
# +z = up: about z = heading (yaw)

# vector = matrix([[x,y,z,1]])
# rotation_matrix = matrix([[r00, r01, r02, 0],
#                           [r10, r11, r12, 0],
#                           [r20, r21, r22, 0],
#                           [tx,  ty,  tz,  1]])
# translation_matrix = matrix([ [1,  0,  0,  0],
#                               [0,  1,  0,  0],
#                               [0,  0,  1,  0],
#                               [tx, ty, tz, 1]])
# transformation_matrix = rotation_matrix * translation_matrix

def apply_matrix_to_points(tMatrix, points):
    """This function is really just to preserve the order of operations"""
    if points.shape[1] != 4:
        if points.shape[1] == 3:
            # convert to homogeneous
            np = ones((points.shape[0],4),dtype=points.dtype)
            np[:,:3] = points[:,:]
            points = np
        else:
            raise Exception
    return array(points * tMatrix)

def rotate_and_translate(R,T):
    """This function is really just to preserve the order of operations"""
    return R * T

def translate_and_rotate(T,R):
    return T * R

def make_homogeneous(pts, axis=1):
    pts = array(pts)
    s = array(pts.shape)
    s[axis] += 1
    npts = ones(s, pts.dtype)
    npts[:pts.shape[0],:pts.shape[1]] = pts[:]
    return npts

def pad_matrix(m):
    m2 = vstack((m,zeros((1,m.shape[1]))))
    return hstack((m2,zeros((m2.shape[0],1))))

def euler_to_matrix(aboutX, aboutY, aboutZ):# roll, pitch, yaw
    """
    Applied in this order: aboutX, aboutY, aboutZ
    """
    # #m = matrix(identity(4,dtype=float64))
    # xrot = matrix(identity(4,dtype=float64))
    # xrot[1,1] = cos(aboutX)
    # xrot[1,2] = -sin(aboutX)
    # xrot[2,1] = sin(aboutX)
    # xrot[2,2] = cos(aboutX)
    # 
    # yrot = matrix(identity(4,dtype=float64))
    # yrot[0,0] = cos(aboutY)
    # yrot[0,2] = sin(aboutY)
    # yrot[2,0] = -sin(aboutY)
    # yrot[2,2] = cos(aboutY) 
    # 
    # zrot = matrix(identity(4,dtype=float64))
    # zrot[0,0] = cos(aboutZ)
    # zrot[0,1] = -sin(aboutZ)
    # zrot[1,0] = sin(aboutZ)
    # zrot[1,1] = cos(aboutZ) 
    # 
    # #return zrot * yrot * xrot
    # P = zrot * yrot * xrot
    
    m = matrix(identity(4,dtype=float64))
    cx = cos(aboutX); cy = cos(aboutY); cz = cos(aboutZ)
    sx = sin(aboutX); sy = sin(aboutY); sz = sin(aboutZ)
    m[0,0] = cy*cz
    m[0,1] = sx*sy*cz-cx*sz
    m[0,2] = cx*sy*cz+sx*sz
    m[1,0] = cy*sz
    m[1,1] = sx*sy*sz+cx*cz
    m[1,2] = cx*sy*sz-sx*cz
    m[2,0] = -sy
    m[2,1] = sx*cy
    m[2,2] = cx*cy
    
    # if not all(abs(P - m) < ones(4)*1e-8):
    #     print "P:"
    #     print array(P)
    #     print "m:"
    #     print array(m)
    #     raise Exception
    return m

def scale_to_transform(x,y,z):
    m = matrix(identity(4,dtype=float64))
    m[0,0] = x
    m[1,1] = y
    m[2,2] = z
    return m

def translation_to_matrix(x,y,z):
    m = matrix(identity(4,dtype=float64))
    # m[0,3] = x
    # m[1,3] = y
    # m[2,3] = z
    m[3,0] = x
    m[3,1] = y
    m[3,2] = z
    return m

def transform_to_matrix(tx=0., ty=0., tz=0., ax=0., ay=0., az=0.):
    # R = euler_to_matrix(ax,ay,az)
    # T = translation_to_matrix(tx,ty,tz)
    # P = rotate_and_translate(R,T)
    m = matrix(identity(4,dtype=float64))
    cx = cos(ax); cy = cos(ay); cz = cos(az)
    sx = sin(ax); sy = sin(ay); sz = sin(az)
    m[0,0] = cy*cz
    m[0,1] = sx*sy*cz-cx*sz
    m[0,2] = cx*sy*cz+sx*sz
    m[1,0] = cy*sz
    m[1,1] = sx*sy*sz+cx*cz
    m[1,2] = cx*sy*sz-sx*cz
    m[2,0] = -sy
    m[2,1] = sx*cy
    m[2,2] = cx*cy
    m[3,0] = tx
    m[3,1] = ty
    m[3,2] = tz
    # if not all(abs(P - m) < ones(4)*1e-8):
    #     print "P:"
    #     print array(P)
    #     print "m:"
    #     print array(m)
    #     raise Exception
    return m

def calculate_normal(p1, p2, p3, normalize=True):
    # u = 1 -> 2
    # v = 1 -> 3
    n = cross(array(p2) - array(p1), array(p3) - array(p1))
    if normalize:
        return n / norm(n)
    else:
        return n

def rebase(v1, v2, v3):
    """If current basis is B={(1,0,0),(0,1,0),(0,0,1)}, and new basis is C={v1,v2,v3}:
    This function computes the transformation P (only rotates at the moment) that completes:
    ub = P * uc"""
    P = matrix(zeros((3,3), dtype=float64))
    P[:,0] = transpose(matrix(v1)).copy()
    P[:,1] = transpose(matrix(v2)).copy()
    P[:,2] = transpose(matrix(v3)).copy()
    P = pad_matrix(P)
    P[3,3] = 1
    return P

def recenter(points):
    """Returns a translation matrix that when applied:
    new_points = points * matrix"""
    return translation_matrix(*-array(mean(points,0))[0][:3])

def angle_between_vectors(v1, v2):
    return arccos(dot(v1, v2))

def calculate_rigid_transform(originalPts, transformedPts, p0=zeros(6,dtype=float64)):
    """Accepts homogenous points only, only uses the first 3 points"""
    fit_it = lambda p: ravel((originalPts[:3] - (transformedPts[:3] * transform_to_matrix(*p)))[:,:3])
    return transform_to_matrix(*(optimize.leastsq(fit_it, p0)[0]))

# def vectors_to_axis_rotation(v1, v2, axis):
#     """Axis = 0,1,2 = corresponding to x,y,z"""
#     arccos

# def get_x_rotation(v1):
#     return -arctan2(v1[2],sqrt(v1[0]*v1[0]+v1[1]*v1[1]))
#     # a1 = arctan2(v1[2],sqrt(v1[0]*v1[0]+v1[1]*v1[1]))
#     # a2 = arctan2(v1[1],v1[0])
#     # return a1, a2
# 
# def get_y_rotation(v1):
#     xrot = get_x_rotation(v1)
#     #unrotate x
#     return arctan2()
# void rotate(double &x, double &y, double angle){
#   double c=cos(angle),s=sin(angle);
#   double x0 = x;
#   x = x*c - s*y;
#   y = x0*s + x0*y;
# }
# 
# int main(void){
#   double target_x=1,target_y=2,target_z=3;
# 
#   double x=1,y=0,z=0;
#   rotate(y,z,4); // Replace 4 by whatever you want. This is your free parameter
#   rotate(x,z,atan2(target_z,sqrt(target_x*target_x+target_y*target_y)));
#   rotate(x,y,atan2(target_y,target_x));
#   std::cout << x << ',' << y << ',' << z << std::endl;
# }



# def get_x_rotation(v1):
#     axis = array([1.,0.,0.])
#     angle = arccos(cross(v1,axis))
#     return angle

# def normals_to_rotation(n1, n2):
#     #n1 = n1/norm(n1)
#     #n2 = n1/norm(n2)
#     c = dot(n1,n2)/ (norm(n1) * norm(n2))
#     s = norm(cross(n1,n2))/(norm(n1) * norm(n2))
#     t = 1. - c
#     a = n1#cross(n1,n2)
#     r = matrix(identity(4,dtype=float64))
#     r[0,0] = t*a[0]*a[0] + c
#     r[0,1] = t*a[0]*a[1] - a[2]*s
#     r[0,2] = t*a[0]*a[2] + a[1]*s
#     r[1,0] = t*a[0]*a[1] + a[2]*s
#     r[1,1] = t*a[1]*a[1] + c
#     r[1,2] = t*a[1]*a[2] - a[0]*s
#     r[2,0] = t*a[0]*a[2] - a[1]*s
#     r[2,1] = t*a[1]*a[2] + a[0]*s
#     r[2,2] = t*a[2]*a[2] + c
#     return r
#def euler_from_vectors(v1, v2):
#    