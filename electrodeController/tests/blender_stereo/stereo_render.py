import math
from math import pi

import bpy


# get cameras
l = bpy.data.objects["Left Camera"]
r = bpy.data.objects["Right Camera"]

# get grid
g = bpy.data.objects["Grid"]

# get scene
s = bpy.data.scenes[0]


# --------------------------------------
# ---- build calibration animation -----
# --------------------------------------

# set timespan
s.frame_start = 0
s.frame_end = 7

def set_grid_pose(grid, x, y, z, ax, ay, az):
    grid.location.x = x
    grid.location.y = y
    grid.location.z = z
    grid.rotation_euler.x = ax
    grid.rotation_euler.y = ay
    grid.rotation_euler.z = az

# setup calibration frames
# g.location.? : ? = x,y,z
# g.rotation_euler.? : ? = x,y,z
for i in range(7):
    s.frame_current = i
    set_grid_pose(g, 0., 0., 0., pi/2., 0., 0.)
    bpy.ops.anim.keyframe_delete()
    bpy.ops.anim.keyframe_insert()

# setup localization frame
s.frame_current = 7
set_grid_pose(g, 0., 0., 0., pi/2., 0., 0.)
bpy.ops.anim.keyframe_delete()
bpy.ops.anim.keyframe_insert()


# ---------------------------
# ---- render animation -----
# ---------------------------

# render animation seen from left camera
s.camera = l
s.render.output_path = '//left/'
bpy.ops.render.render(animation=True)

# render animation seen from right camera
s.camera = r
s.render.output_path = '//right/'
bpy.ops.render.render(animation=True)


# --------------------------------------
# ---- build localization animation ----
# --------------------------------------