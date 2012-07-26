#! /usr/bin/env python

from numpy import *
import sys

raw_data = genfromtxt(sys.argv[1])

by_w_position = {}

for r in range(0, raw_data.shape[0]):
    w = raw_data[r, 8];
    a = raw_data[r, 7];
    x,y,z = raw_data[r,4:7];
   
    if not w in by_w_position:
        by_w_position[w] = {}

    by_w_position[w][a] = array([x,y,z])

radii = {}
for w in by_w_position.keys():
    by_angle = by_w_position[w]
    angles = by_angle.keys()
    sorted_angles = sort(angles)

    accum_radius = 0
    for i in range(0, len(sorted_angles)-1):
        
        a_diff = sorted_angles[i+1] - sorted_angles[i]
        v1 = by_angle[sorted_angles[i+1]]
        v2 = by_angle[sorted_angles[i]]
        accum_radius += (sqrt(sum((v1-v2)**2))/2) / sin(radians(a_diff/2))
    
    radii[w] = accum_radius / (len(sorted_angles)-1)

ws = radii.keys()
sorted_ws = sort(ws)
for w in sorted_ws:
    print("%.4f: %.4f : %.4f" % (-w, radii[w], radii[w] + w))


for i in range(0, len(sorted_ws)-1):
    print("w diff: %f, radius diff: %f" % (sorted_ws[i+1] - sorted_ws[0], radii[sorted_ws[0]] - radii[sorted_ws[i+1]]))
    

            

    


