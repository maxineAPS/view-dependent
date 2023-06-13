import bpy

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


import bpy
context = bpy.context
object = context.active_object


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

bpy.ops.view3d.view_selected(override)
bpy.ops.view3d.view_axis(override, type='LEFT')

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

obj = bpy.context.active_object
print(obj)
print(obj.data.polygons)
for i in range(1000):
    obj.data.polygons[i].select = False

print("DONE")