import bpy

def getArea(type):
    for screen in bpy.context.workspace.screens:
        for area in screen.areas:
            if area.type == type:
                return area
            
override = {'area': getArea('VIEW_3D')}


import bpy
context = bpy.context
object = context.active_object


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


prev_region = bpy.context.area.type

print(getArea('VIEW_3D'))

for ns3d in getArea('VIEW_3D').spaces:
    if ns3d.type == "VIEW_3D":
        break

# https://blender.stackexchange.com/questions/15118/how-do-i-override-context-for-bpy-ops-mesh-loopcut
win      = bpy.context.window
scr      = win.screen
areas3d  = [getArea('VIEW_3D')]
region   = [region for region in areas3d[0].regions if region.type == 'WINDOW']

override = {'window':win,
            'screen':scr,
            'area'  :getArea('VIEW_3D'),
            'region':region[0],
            'scene' :bpy.context.scene,
            'space' :getArea('VIEW_3D').spaces[0],
            }
            
prev_perspective = ns3d.region_3d.view_perspective

if ns3d.region_3d.view_perspective == 'PERSP':
    bpy.ops.view3d.view_persportho(override)


print(override['window'])
print(override['area'].type)
print(override['region'].type)

bpy.ops.object.mode_set(override, mode='EDIT')
bpy.ops.mesh.select_all(override, action='SELECT')

bpy.ops.mesh.uv_texture_add(override)
object.data.uv_layers[0].name = 'Color Spread'
object.data.uv_layers[0].active_render = True
object.data.uv_layers[0].active = True


# The Problem
#-----------------------------------
# Changing the view_axis won't change the view when using
# bpy.ops.uv.project_from_view() even though the 3D view
# has been changed.



# Update region:
ns3d.region_3d.update()

# Failures so far
#-----------------------------------
# Setting view axis multiple times
# Setting projection and view axis multiple times
# AGGRESSIVELY SETTING OVERRIDES FOR EVERYTHING
# Using an Override with as many details as possible
# Only having one 3D View Active
    
    
bpy.ops.uv.project_from_view(override, correct_aspect=True, 
    clip_to_bounds=True, scale_to_bounds=True)