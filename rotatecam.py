import bpy

def print(data):
    '''overwrite print in blender to all open consoles for easy debugging'''
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'CONSOLE':
                override = {'window': window, 'screen': screen, 'area': area}
                bpy.ops.console.scrollback_append(override, text=str(data), type="OUTPUT")      
                

import bpy
import os
from math import *
from mathutils import *

#set your own target here
target = bpy.data.objects['Cube.126']
cam = bpy.data.objects['Camera']
t_loc_x = target.location.x
t_loc_y = target.location.y

print("target location")
print(t_loc_x)
print(t_loc_y)
cam_loc_x = cam.location.x
cam_loc_y = cam.location.y
# The different radii range

def look_at(obj_camera, point):
    loc_camera = obj_camera.matrix_world.to_translation()

    direction = point - loc_camera
    # point the cameras '-Z' and use its 'Y' as up
    rot_quat = direction.to_track_quat('-Z', 'Y')

    # assume we're using euler rotation
    obj_camera.rotation_euler = rot_quat.to_euler()



#set camera location here

cam.location.x = 5
cam.location.y = 0
cam.location.z = 10

look_at(cam, target.matrix_world.to_translation())
   