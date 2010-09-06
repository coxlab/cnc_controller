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

buildAnimation = False

if buildAnimation:
    # set timespan
    s.frame_start = 0
    s.frame_end = 7
    
    def set_grid_pose(grid, x, y, z, ax, ay, az):
        grid.location.x = x
        grid.location.y = y
        grid.location.z = z
        grid.rotation_euler = [ax, ay, az]
        #grid.rotation_euler.x = ax
        #grid.rotation_euler.y = ay
        #grid.rotation_euler.z = az
    
    # setup calibration frames
    # g.location.? : ? = x,y,z
    # g.rotation_euler.? : ? = x,y,z
    dr = pi/4.
    xs = [0., 4., -4., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
    ys = [0., 0., 0., 4., -4., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
    zs = [0., 0., 0., 0., 0., 3., -3., 0., 0., 0., 0., 0., 0., 0.]
    axs = [0., 0., 0., 0., 0., 0., 0., dr, -dr, 0., 0., 0., 0., 0.] # + pi/2.
    ays = [0., 0., 0., 0., 0., 0., 0., 0., 0., dr, -dr, 0., 0., 0.]
    azs = [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., dr, -dr, 0.]
    for i in range(s.frame_end):
        s.frame_current = i
        set_grid_pose(g, xs[i], ys[i], zs[i], pi/2.+axs[i], ays[i], azs[i])
        #bpy.ops.anim.keyframe_delete()
        #bpy.ops.anim.keyframe_insert()
    
    # setup localization frame
    s.frame_current = s.frame_end
    set_grid_pose(g, 0., 0., 0., pi/2., 0., 0.)
    #bpy.ops.anim.keyframe_delete()
    #bpy.ops.anim.keyframe_insert()


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