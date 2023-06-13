import bpy


cam_location_x = 0
cam_location_y = 6
cam_location_z = 10
def print(data):
    '''overwrite print in blender to all open consoles for easy debugging'''
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'CONSOLE':
                override = {'window': window, 'screen': screen, 'area': area}
                bpy.ops.console.scrollback_append(override, text=str(data), type="OUTPUT")    
                
def getArea(type):
    for screen in bpy.context.workspace.screens:
        for area in screen.areas:
            if area.type == type:
                return area
            
override = {'area': getArea('VIEW_3D')}



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

print("STARTING")

def look_at(obj_camera, point):
    loc_camera = obj_camera.matrix_world.to_translation()

    direction = point - loc_camera
    # point the cameras '-Z' and use its 'Y' as up
    rot_quat = direction.to_track_quat('-Z', 'Y')

    # assume we're using euler rotation
    obj_camera.rotation_euler = rot_quat.to_euler()



#set camera location here

cam.location.x = cam_location_x
cam.location.y = cam_location_y
cam.location.z = cam_location_z

look_at(cam, target.matrix_world.to_translation())

    





print("STARTING")


look_at(cam, target.matrix_world.to_translation())

print("rotated")




    

import bpy
import os
from math import *
from mathutils import *

bpy.ops.object.mode_set(mode="OBJECT")
 
#deselect the 0th vertex
bpy.data.meshes['Cube.126'].vertices[1].select = False
 

bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action='DESELECT')  

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

   

for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        area.spaces[0].region_3d.view_perspective = 'CAMERA'
        
def getView3dAreaAndRegion(context):
  for area in context.screen.areas: 
      if area.type == "VIEW_3D":    
        for region in area.regions:
          if region.type == "WINDOW":
            print("Found WINDOW") 
            return area, region

def select_border(context, view3dAreaAndRegion=None, extend=True):
  if not view3dAreaAndRegion:
    view3dAreaAndRegion = getView3dAreaAndRegion(context)
    print(view3dAreaAndRegion)
  view3dArea, view3dRegion = view3dAreaAndRegion
  override = context.copy()
  override['area'] = view3dArea
  override['region'] = view3dRegion
  bpy.ops.view3d.select_box(override,xmin=0,xmax=view3dArea.width,ymin=0,ymax=view3dArea.height,mode='ADD')
  
select_border(bpy.context)


import bpy
import os
from math import *
from mathutils import *

bpy.ops.object.mode_set(mode="OBJECT")
 
#deselect the 0th vertex
bpy.data.meshes['Cube.126'].vertices[1].select = False
 

bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action='DESELECT')  

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


for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        area.spaces[0].region_3d.view_perspective = 'CAMERA'
        
def getView3dAreaAndRegion(context):
  for area in context.screen.areas: 
      if area.type == "VIEW_3D":    
        for region in area.regions:
          if region.type == "WINDOW":
            print("Found WINDOW") 
            return area, region

def select_border(context, view3dAreaAndRegion=None, extend=True):
  if not view3dAreaAndRegion:
    view3dAreaAndRegion = getView3dAreaAndRegion(context)
    print(view3dAreaAndRegion)
  view3dArea, view3dRegion = view3dAreaAndRegion
  override = context.copy()
  override['area'] = view3dArea
  override['region'] = view3dRegion
  bpy.ops.view3d.select_box(override,xmin=0,xmax=view3dArea.width,ymin=0,ymax=view3dArea.height,mode='ADD')
  
select_border(bpy.context)



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

object = bpy.context.object
if len(object.material_slots) == 0:
    bpy.ops.object.material_slot_add()
    slot = object.material_slots[object.active_material_index]
    mat = bpy.data.materials.new("My material")
    slot.material = mat

bpy.ops.object.material_slot_add()
slot = object.material_slots[object.active_material_index]
mat = bpy.data.materials.new("My material 2")
slot.material = mat

mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
texImage.image = bpy.data.images.load("/Users/maxineperroni-scharf/Desktop/view-dependent/test_images/forest.png")
mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])

ob = bpy.context.view_layer.objects.active

# Assign it to object
if ob.data.materials:
    ob.data.materials[0] = mat
else:
    ob.data.materials.append(mat)
    
    
#mat.diffuse_color = (1, 0, 0, 1)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.object.material_slot_assign()
bpy.ops.object.mode_set(mode='OBJECT')
