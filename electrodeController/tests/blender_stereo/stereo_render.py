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

buildAnimation = True

if buildAnimation:
    # set timespan
    s.frame_start = 0
    s.frame_end = 13
    
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
    xs = [0., 11., -11., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
    ys = [0., 0., 0., 4., -4., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
    zs = [0., 0., 0., 0., 0., 3., -3., 0., 0., 0., 0., 0., 0., 0.]
    rxs = [0., 0., 0., 0., 0., 0., 0., pi/8., -pi/8., 0., 0., 0., 0., 0.] # + pi/2.
    rys = [0., 0., 0., 0., 0., 0., 0., 0., 0., pi/8., -pi/8., 0., 0., 0.]
    rzs = [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., pi/8., -pi/8., 0.]
    l.location.x = 0.
    l.location.y = -40.
    l.location.z = 0.
    l.rotation_euler.x = pi/2.
    l.rotation_euler.y = 0.
    l.rotation_euler.z = 0.
    r.location.x = 0.
    r.location.y = -40.
    r.location.z = 0.
    r.rotation_euler.x = pi/2.
    r.rotation_euler.y = 0.
    r.rotation_euler.z = 0.
    for i in range(s.frame_end):
        s.frame_current = i
        set_grid_pose(g, xs[i], ys[i], zs[i], pi/2.+rxs[i], rys[i], rzs[i])
        bpy.ops.anim.keyframe_delete()
        bpy.ops.anim.keyframe_insert()
    
    # setup localization frame
    s.frame_current = s.frame_end
    set_grid_pose(g, 0., 0., 0., pi/2., 0., 0.)
    l.location.x = -8.
    l.location.y = -40.
    l.location.z = 0.
    l.rotation_euler.x = pi/2.
    l.rotation_euler.y = 0.
    l.rotation_euler.z = -math.radians(20.)
    r.location.x = 8.
    r.location.y = -40.
    r.location.z = 0.
    r.rotation_euler.x = pi/2.
    r.rotation_euler.y = 0.
    r.rotation_euler.z = math.radians(20.)
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