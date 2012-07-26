#!/usr/bin/env python

import os, sys

import cv
from pylab import *
from mpl_toolkits.mplot3d import Axes3D

import electrodeController.vector as vector

def set_3d_uniform(ax):
    # scale axes 1:1
    ox, oy, oz = ax.get_xlim3d().copy(), ax.get_ylim3d().copy(), ax.get_zlim3d().copy()
    rmax = max((abs(diff(ox)), abs(diff(oy)), abs(diff(oz))))
    ox = (ox - mean(ox))/abs(diff(ox)) * rmax + mean(ox)
    oy = (oy - mean(oy))/abs(diff(oy)) * rmax + mean(oy)
    oz = (oz - mean(oz))/abs(diff(oz)) * rmax + mean(oz)
    ax.set_xlim3d([ox[0],ox[1]])
    ax.set_ylim3d([oy[0],oy[1]])
    ax.set_zlim3d([oz[0],oz[1]])
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_zlabel('z')

# ================= read in data ==================
# get filename from command line
assert len(sys.argv) > 1
logFileDir = sys.argv[1]

# check if it exists and then open it
fn = logFileDir+'/frames/frames.log'
assert os.path.exists(fn)
framesLog = open(fn,'r')

# read and parse data
tcPtsInTc = zeros((3,4))
tcPtsInCam = zeros((3,4))
tcToCam = zeros((4,4))
l = framesLog.readline()
while not l in (None, ''):
    if 'Registering cameras with points in (tcFrame, camera):' in l:
        for i in xrange(3):
            tcPtsInTc[i] = array(framesLog.readline()[:-1].strip(' []').split()).astype(float)
        for i in xrange(3):
            tcPtsInCam[i] = array(framesLog.readline()[:-1].strip(' []').split()).astype(float)
    if 'Adding Frame tricorner to camera' in l:
        for i in xrange(4):
            tcToCam[i] = array(framesLog.readline()[:-1].strip(' []').split()).astype(float)
    l = framesLog.readline()
framesLog.close()

tcToCam = matrix(tcToCam)

# ========= transform points from tc to cam =============
transPtsInTc = vector.apply_matrix_to_points(inv(tcToCam), tcPtsInCam)

# ========== translate data to center point ==============
tcPtsInTc[0] -= tcPtsInTc[1]
tcPtsInTc[2] -= tcPtsInTc[1]
tcPtsInTc[1] -= tcPtsInTc[1]

tcPtsInCam[0] -= tcPtsInCam[1]
tcPtsInCam[2] -= tcPtsInCam[1]
tcPtsInCam[1] -= tcPtsInCam[1]

transPtsInTc[0] -= transPtsInTc[1]
transPtsInTc[2] -= transPtsInTc[1]
transPtsInTc[1] -= transPtsInTc[1]

# ========= print out transformation matrix ==============
print tcToCam
t, r = vector.decompose_matrix(tcToCam)
print "Tricorner to Camera Matrix Decomposition"
print "Translation: %.3f %.3f %.3f" % tuple(t)
print "Rotation: %.3f %.3f %.3f" % (degrees(r[0]), degrees(r[1]), degrees(r[2]))

# ================== plot data ====================
def plot_points(ax,x,y,z,c):
    # x = pts[:,0]
    # y = pts[:,1]
    # z = pts[:,2]
    # 3d
    ax.scatter(x,y,z,c=c)
    set_3d_uniform(ax)
    # 2d
    figure(2)
    subplot(221); scatter(x,y,c=c); xlabel('x'); ylabel('y')
    subplot(222); scatter(x,z,c=c); xlabel('x'); ylabel('z')
    subplot(223); scatter(y,z,c=c); xlabel('y'); ylabel('z')

ax = Axes3D(figure())
figure()
plot_points(ax, tcPtsInTc[:,0],tcPtsInTc[:,1],tcPtsInTc[:,2],'b')
plot_points(ax, tcPtsInCam[:,0],tcPtsInCam[:,2],tcPtsInCam[:,1],'g') # swap y and z for rough fit
plot_points(ax, transPtsInTc[:,0],transPtsInTc[:,1],transPtsInTc[:,2],'r')

show()
# p = loadtxt('tcs_reg_pts')
# 
# px = array(p[:,4])
# py = array(p[:,5])
# pz = array(p[:,6])
# lx = array(p[:,0])
# ly = array(p[:,1])
# rx = array(p[:,2])
# ry = array(p[:,3])
# 
# c1 = array(p[0])
# c2 = array(p[1])
# p0 = array(p[2])
# p1 = array(p[3])
# p2 = array(p[4])
# 
# figCount = 1
# 
# f = figure(figCount); figCount += 1
# ax = Axes3D(f, azim=-166, elev=14)
# x = px[2:]
# y = py[2:]
# z = -pz[2:]
# import vector
# R = vector.euler_to_matrix(-radians(55),0,0)
# T = vector.translation_to_matrix(-mean((x[0],x[2])),-mean((y[0],y[2])),-mean((z[0],z[2])))
# P = T * R
# print P
# for i in xrange(len(x)):
#     p = matrix([x[i],y[i],z[i],1.])
#     print p
#     pp = p * P
#     print pp
#     x[i] = pp[0,0]/pp[0,3]
#     y[i] = pp[0,1]/pp[0,3]
#     z[i] = pp[0,2]/pp[0,3]
# #ax.scatter(mps[:,0], mps[:,1], mps[:,2], c='b')
# labels=['R1','R2','R3','Electrode']
# cs=['g','b','y','r']
# for i in xrange(len(x)):
#     ax.scatter([x[i]], [y[i]], [z[i]], c=cs[i], edgecolors=cs[i])
#     ax.text(x[i]+0.1,y[i]+0.1,z[i]+0.1,labels[i])
# ax.set_xlabel('mm'); ax.set_ylabel('mm'); ax.set_zlabel('mm')
# ax.set_xlim3d([-10,10])
# ax.set_ylim3d([-15,5])
# ax.set_zlim3d([0,20])
# 
# savefig('electrodePlot.eps')
# show()
