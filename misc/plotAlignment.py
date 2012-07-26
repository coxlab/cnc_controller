#!/usr/bin/env python

from StringIO import StringIO

from pylab import *
from mpl_toolkits.mplot3d import Axes3D

from electrodeController.cnc import linefit
from electrodeController import vector

f = open('alignmentPts.txt', 'r')

f.readline() # first line is comment

rs = ""
gs = ""
bs = ""
ys = ""

for l in f:
    if l[0] == 'r':
        rs += l[3:-2] + '\n'
    elif l[0] == 'g':
        gs += l[3:-2] + '\n'
    elif l[0] == 'b':
        bs += l[3:-2] + '\n'
    elif l[0] == 'y':
        ys += l[3:-2] + '\n'

f.close()

#print len(rs), len(gs), len(bs), len(ys)

r = loadtxt(StringIO(rs),delimiter=',')
g = loadtxt(StringIO(gs),delimiter=',')
b = loadtxt(StringIO(bs),delimiter=',')
y = loadtxt(StringIO(ys),delimiter=',')

sets = [r,g,b,y]
colors = ['r','g','b','y']

# --- is movement aligned with the probe ---
# fit line to r/g/b/y, remove translation/origin just look at orientation vector : global vector
rGlobal = linefit.fit_3d_line(r[:,4:7],r[:,8])[3:]
gGlobal = linefit.fit_3d_line(g[:,4:7],g[:,8])[3:]
bGlobal = linefit.fit_3d_line(b[:,4:7],b[:,8])[3:]
yGlobal = linefit.fit_3d_line(y[:,4:7],y[:,8])[3:]
globalVectors = [rGlobal, gGlobal, bGlobal, yGlobal]
globalVector = mean(array(globalVectors),0)
globalVector = globalVector/norm(globalVector)

#print rGlobal, gGlobal, bGlobal, yGlobal
# # plot globals
# ax = Axes3D(figure())
# for i in xrange(len(globalVectors)):
#     v = globalVectors[i]
#     ax.scatter([v[0]],[v[1]],[v[2]],c=colors[i])
#     ax.plot([0.,v[0]],[0.,v[1]],[0.,v[2]],c=colors[i])
# ax.autoscale_one_to_one()

# average r[i],y[i] and b[i],g[i], calculate vector between averages : local vector
localVectors = []
errVectors = []
for i in xrange(len(r)):
    p0 = (r[i,4:7] + y[i,4:7])/2.
    p1 = (b[i,4:7] + g[i,4:7])/2.
    v = p0 - p1
    v = v/norm(v)
    localVectors.append(v)
    eV = globalVector - v
    eV = eV/norm(eV)
    errVectors.append(eV)
#print localVectors

# plot locals
ax = Axes3D(figure())
for i in xrange(len(localVectors)):
    v = localVectors[i]
    ax.scatter([v[0]],[v[1]],[v[2]],alpha=0.1)
    ax.plot([0.,v[0]],[0.,v[1]],[0.,v[2]],alpha=0.1)
v = globalVector
ax.scatter([v[0]],[v[1]],[v[2]])
ax.plot([0.,v[0]],[0.,v[1]],[0.,v[2]])
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.autoscale_one_to_one()
# 
# # plot error
# ax = Axes3D(figure())
# for i in xrange(len(errVectors)):
#     v = errVectors[i]
#     ax.scatter([v[0]],[v[1]],[v[2]])
#     ax.plot([0.,v[0]],[0.,v[1]],[0.,v[2]])
# ax.autoscale_one_to_one()

# plot individual errors
figure()
errVectors = array(errVectors)
# xErr = errVectors[:,0]
# yErr = errVectors[:,1]
# zErr = errVectors[:,2]
xErr = []
yErr = []
zErr = []
aErr = []
gvXY = globalVector[:2]/norm(globalVector[:2])
gvYZ = globalVector[1:]/norm(globalVector[1:])
gvXZ = globalVector[::2]/norm(globalVector[::2])
for v in localVectors:
    lvXY = v[:2]/norm(v[:2])
    lvYZ = v[1:]/norm(v[1:])
    lvXZ = v[::2]/norm(v[::2])
    xErr.append(degrees(vector.angle_between_vectors(lvYZ,gvYZ)))
    yErr.append(degrees(vector.angle_between_vectors(lvXZ,gvXZ)))
    zErr.append(degrees(vector.angle_between_vectors(lvXY,gvXY)))
    aErr.append(degrees(vector.angle_between_vectors(v,globalVector)))
# xErr = [degrees(vector.angle_between_vectors(l[1:]/norm(l[1:]),globalVector[1:]/norm(globalVector[1:]))) for l in localVectors]
# yErr = [degrees(vector.angle_between_vectors([l[0],l[2]],[globalVector[0],globalVector[2]])) for l in localVectors]
# zErr = [degrees(vector.angle_between_vectors(l[:2],globalVector[:2])) for l in localVectors]
subplot(411)
plot(xErr)
ylabel('xErr')
subplot(412)
plot(yErr)
ylabel('yErr')
subplot(413)
plot(zErr)
ylabel('zErr')
subplot(414)
plot(aErr)
ylabel('angleErr')
xlabel('local angle index')

yaw = []
pitch = []
gy = degrees(arctan2(globalVector[0],globalVector[1]))
gp = degrees(arctan2(globalVector[2],sqrt(globalVector[0]**2 + globalVector[1]**2)))
for v in localVectors:
    vy = degrees(arctan2(v[0],v[1]))
    vp = degrees(arctan2(v[2],sqrt(v[0]**2 + v[1]**2)))
    yaw.append(vy-gy)
    pitch.append(vp-gp)
    # dv = globalVector - v
    # dv /= norm(dv)
    # yaw.append(degrees(arctan2(dv[0],dv[1])))
    # pitch.append(degrees(arctan2(dv[2],sqrt(dv[0]**2 + dv[1]**2))))
figure()
subplot(211)
plot(yaw)
ylabel('about Z')
subplot(212)
plot(pitch)
ylabel('about Y')
xlabel('local angle index')
suptitle('tilt of probe')

# compare local to global

# --- Is probe tilted ---
# compare distance between red and green and blue and yellow

# ---- plot raw data ----
# ax = Axes3D(figure())
# for i in xrange(len(sets)):
#     data = sets[i]
#     c = colors[i]
#     # plot data
#     ax.plot(data[:,4],data[:,5],data[:,6],c=c)
#     ax.scatter(data[:,4],data[:,5],data[:,6],c=c)
# ax.autoscale_one_to_one()

show()
