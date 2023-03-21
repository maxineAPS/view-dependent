import bpy
import pysbs
from pathlib import Path
import os
from random import randint
import torch
#/Applications/Blender.app/Contents/Resources/2.93/python/bin/python3.9 pip install ...

#helper function for printing in blender console
def print(data):
    '''overwrite print in blender to all open consoles for easy debugging'''
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'CONSOLE':
                override = {'window': window, 'screen': screen, 'area': area}
                bpy.ops.console.scrollback_append(override, text=str(data), type="OUTPUT")      
                

def generate_mesh(H, COL = None, offset_x = 0, offset_y = 0):
    mat = bpy.data.materials.new("white")
    bpy.data.materials["white"].diffuse_color = [1.0, 1.0, 1.0, 1.0]
    
    width = 1/len(H)
    for i in range(len(H)):
        for j in range(len(H[0])):
            x_coord = i*width*2 + offset_x + width
            y_coord = j*width*2 + offset_y + width
            
            bpy.ops.mesh.primitive_cube_add(location=(x_coord, y_coord, H[i][j]), scale=(width, width, H[i][j]))
           
            ob = bpy.context.active_object
            # Assign it to object
            if ob.data.materials:
            # assign to 1st material slot
                ob.data.materials[0] = mat
            else:
                # no slots
                ob.data.materials.append(mat)
                
            if COL != None:
                mat = bpy.data.materials.new(name=str(i) + "." + str(j) + "." + str(offset_x) + "." + str(offset_y))
                bpy.data.materials[str(i) + "." + str(j) + "." + str(offset_x) + "." + str(offset_y)].diffuse_color = [COL[i][j][0], COL[i][j][1], COL[i][j][2], 1.0]

            ob = bpy.context.active_object
            ob.name = "t" + str(i) + "." + str(j)
            # Assign it to object
            if ob.data.materials:
            # assign to 1st material slot
                ob.data.materials[0] = mat
            else:
                # no slots
                ob.data.materials.append(mat)
            
#remove all meshes and materials
def clear_meshes():
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)
        
    for material in bpy.data.materials:
        material.user_clear()
        bpy.data.materials.remove(material)


clear_meshes()
H = torch.load("/Users/maxineperroni-scharf/Dropbox/Mac/Desktop/view_dependent_code_release/march20H.pt")
COL = torch.load("/Users/maxineperroni-scharf/Dropbox/Mac/Desktop/view_dependent_code_release/march20COL.pt")
generate_mesh(H, COL)

print("done")
