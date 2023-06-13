import bpy
import bmesh 
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
                

def generate_mesh_with_segments(H, COL = None, offset_x = 0, offset_y = 0, vertical_segment_height = 0.1, discretize=True):
    mat = bpy.data.materials.new("white")
    bpy.data.materials["white"].diffuse_color = [1.0, 1.0, 1.0, 1.0]
   
    width = 1/len(H)
    for i in range(len(H)):
        for j in range(len(H[0])):
            print(H[i][j])
            
            num_strips = int(H[i][j]/vertical_segment_height)
            remainder = H[i][j]-num_strips*vertical_segment_height
            x_coord = i*width + offset_x + width/2
            y_coord = j*width + offset_y + width/2
            if COL != None:
                mat = bpy.data.materials.new(name=str(i) + "." + str(j) + "." + str(offset_x) + "." + str(offset_y))
                bpy.data.materials[str(i) + "." + str(j) + "." + str(offset_x) + "." + str(offset_y)].diffuse_color = [COL[i][j][0], COL[i][j][1], COL[i][j][2], 1.0]

            for k in range(1, num_strips+1):

            
                bpy.ops.mesh.primitive_cube_add(location=(x_coord, y_coord, (k-0.5)*vertical_segment_height), scale=(width/2, width/2, vertical_segment_height/2))
           
                ob = bpy.context.active_object
                # Assign it to object
                if ob.data.materials:
                # assign to 1st material slot
                    ob.data.materials[0] = mat
                else:
                    # no slots
                    ob.data.materials.append(mat)
                    
       
            if not discretize:
                bpy.ops.mesh.primitive_cube_add(location=(x_coord, y_coord, num_strips*vertical_segment_height + remainder/2), scale=(width/2, width/2, remainder/2))
           
                ob = bpy.context.active_object
                # Assign it to object
                if ob.data.materials:
                # assign to 1st material slot
                    ob.data.materials[0] = mat
                else:
                    # no slots
                    ob.data.materials.append(mat)
                    
            scene = bpy.context.scene


        for obj in scene.objects:
            # whatever objects you want to join...
            if obj.type == 'MESH':
                obj.select_set(True)
            #bpy.context.view_layer.objects.active = bpy.data.objects["Cube"]
        bpy.ops.object.join()
    
    

    for obj in scene.objects:
            # whatever objects you want to join...
        if obj.type == 'MESH':
            obj.select_set(True)
            #bpy.context.view_layer.objects.active = bpy.data.objects["Cube"]
    bpy.ops.object.join()
    
    
    obj = bpy.context.active_object


    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data) 
    
    face_count_map = {}


    #first loop, getting number of occurances of each face
    
    for f in bm.faces:
        vertices = []
        for v in f.verts:

            coords = str(round(v.co[0], 4)) + "." +str(round(v.co[1], 4)) + "." + str(round(v.co[2], 4))
            vertices.append(coords)
        
        vertices.sort()
        verts = str(vertices)
        if verts not in face_count_map:
            face_count_map[verts] = 1
        else:
            face_count_map[verts]+= 1
                
                
    #second loop, removing any face which has a count >1  
    faces_to_delete = []
    for f in bm.faces:
        vertices = []
        for v in f.verts:

            coords = str(round(v.co[0], 4)) + "." +str(round(v.co[1], 4)) + "." + str(round(v.co[2], 4))
            vertices.append(coords)
        
        vertices.sort()
        verts = str(vertices)
        if face_count_map[verts] > 1:

            faces_to_delete.append(f)

            
    bmesh.ops.delete(bm, geom=faces_to_delete, context = 'FACES') 
    print(faces_to_delete)
    

    # if you make edits then you need to update at the end
    bmesh.update_edit_mesh(obj.data)
    
    
    
    merge_threshold = 0.05 # here you can define Merge By Distance threshold

    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    # This is to make sure that there is an active object in the scene:
    #----------------------------------------------
    if not bpy.context.active_object.hide_viewport:
        for object in bpy.context.scene.objects:
            if not object.hide_viewport:
                bpy.context.view_layer.objects.active = object
                break
            
    #Deselect all
    bpy.ops.object.select_all(action='DESELECT')

#Mesh objects
    MSH_OBJS = [m for m in bpy.context.scene.objects if m.type == 'MESH']

    for OBJS in MSH_OBJS:
        #Select all mesh objects
        OBJS.select_set(state=True)

    #Makes one active
        bpy.context.view_layer.objects.active = OBJS
    
    #----------------------------------------------
    bpy.ops.object.join()
    bpy.ops.object.convert(target='MESH') # Here I've added an option which will
                                      # apply all modifiers by converting object
                                      # to mesh
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold = merge_threshold)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(type = 'FACE')
    bpy.ops.mesh.select_interior_faces()
    bpy.ops.mesh.delete(type='FACE')
    bpy.ops.object.mode_set(mode='OBJECT')
                
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
                    
def generate_mesh(H, COL = None, offset_x = 0, offset_y = 0):
    mat = bpy.data.materials.new("white")
    bpy.data.materials["white"].diffuse_color = [1.0, 1.0, 1.0, 1.0]
    
    width = 1/len(H)
    for i in range(len(H)):
        for j in range(len(H[0])):
            x_coord = i*width + offset_x + width/2
            y_coord = j*width + offset_y + width/2
            
            bpy.ops.mesh.primitive_cube_add(location=(x_coord, y_coord, H[i][j]/2), scale=(width/2, width/2, H[i][j]/2))
           
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
H = torch.load("/Users/maxineperroni-scharf/Desktop/view-dependent/models/06_12_2023_18-07-38_heights.pt")
COL = torch.load("/Users/maxineperroni-scharf/Desktop/view-dependent/models/06_12_2023_18-07-38_colors.pt")
#generate_mesh(H, COL)

generate_mesh_with_segments(H, COL)



print("done")
