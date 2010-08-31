import bpy

# get cameras
l = bpy.data.objects["Left Camera"]
r = bpy.data.objects["Right Camera"]

# get scene
s = bpy.data.scenes[0]

#s = bpy.data.scenes[0]
s.camera = l
s.render.output_path = '//left/'
bpy.ops.render.render(animation=True)

s.camera = r
s.render.output_path = '//right/'
bpy.ops.render.render(animation=True)