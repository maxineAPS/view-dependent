import bpy
from math import *
from mathutils import *
import bmesh 
import torch

def print(data):
    '''overwrite print in blender to all open consoles for easy debugging'''
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'CONSOLE':
                override = {'window': window, 'screen': screen, 'area': area}
                bpy.ops.console.scrollback_append(override, text=str(data), type="OUTPUT")    

def getView3dAreaAndRegion(context):
  for area in context.screen.areas: 
      if area.type == "VIEW_3D":    
        for region in area.regions:
          if region.type == "WINDOW":
            return area, region

def select_border(context, view3dAreaAndRegion=None, extend=True):
  if not view3dAreaAndRegion:
    view3dAreaAndRegion = getView3dAreaAndRegion(context)

  view3dArea, view3dRegion = view3dAreaAndRegion
  override = context.copy()
  override['area'] = view3dArea
  override['region'] = view3dRegion
  bpy.ops.view3d.select_box(override,xmin=0,xmax=view3dArea.width,ymin=0,ymax=view3dArea.height,mode='ADD')
  
def getArea(type):
    for screen in bpy.context.workspace.screens:
        for area in screen.areas:
            if area.type == type:
                return area
            
def look_at(obj_camera, point):
    loc_camera = obj_camera.matrix_world.to_translation()

    direction = point - loc_camera
    # point the cameras '-Z' and use its 'Y' as up
    rot_quat = direction.to_track_quat('-Z', 'Y')

    # assume we're using euler rotation
    obj_camera.rotation_euler = rot_quat.to_euler()
    
def generate_mesh_with_segments(H, COL = None, offset_x = 0, offset_y = 0, vertical_segment_height = 0.1, discretize=True):
    mat = bpy.data.materials.new("white")
    bpy.data.materials["white"].diffuse_color = [1.0, 1.0, 1.0, 1.0]
   
    width = 1/len(H)
    for i in range(len(H)):
        for j in range(len(H[0])):
       
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
            if obj.type == 'MESH':
                obj.select_set(True)
        bpy.ops.object.join()
    
    for obj in scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
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
    bmesh.update_edit_mesh(obj.data)
    
    merge_threshold = 0.01

    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
   
    if not bpy.context.active_object.hide_viewport:
        for object in bpy.context.scene.objects:
            if not object.hide_viewport:
                bpy.context.view_layer.objects.active = object
                break
            
    bpy.ops.object.select_all(action='DESELECT')

    MSH_OBJS = [m for m in bpy.context.scene.objects if m.type == 'MESH']
    for OBJS in MSH_OBJS:
        #select all mesh objects
        OBJS.select_set(state=True)
        #make one active
        bpy.context.view_layer.objects.active = OBJS
    
    bpy.ops.object.join()
    bpy.ops.object.convert(target='MESH') 
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

def proj_image_from_cam_loc(image_path, cam_location_x, cam_location_y, cam_location_z):
    
    obj_name = bpy.context.active_object.name
    
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action='DESELECT') 
    override = {'area': getArea('VIEW_3D')}

    context = bpy.context
    object = context.active_object
    scene = bpy.context.scene

    mesh_obs = [o for o in scene.objects if o.type == 'MESH']

    if mesh_obs:
        bpy.ops.object.origin_set(
            {"object" : mesh_obs[0],
            "selected_objects" : mesh_obs,
            "selected_editable_objects" : mesh_obs,
            }
        )

    target = bpy.data.objects[obj_name]
    cam = bpy.data.objects['Camera']
    target.location.x = 0
    target.location.y = 0
    
    #set camera location here
    cam.location.x = cam_location_x
    cam.location.y = cam_location_y
    cam.location.z = cam_location_z + 1 #+1 as we are looking at the top of the mesh, during optimization camera was centered at 1)

    #point camera to surface
    look_at(cam, target.matrix_world.to_translation())
    print("need to print inbetween here for some reason to avoid blender bug")
    look_at(cam, target.matrix_world.to_translation())
    
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces[0].region_3d.view_perspective = 'CAMERA'

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

    if ns3d.region_3d.view_perspective == 'PERSP':
        bpy.ops.view3d.view_persportho(override)

    bpy.ops.object.mode_set(override, mode='EDIT')
    bpy.ops.mesh.uv_texture_add(override)
    object.data.uv_layers[0].name = 'Color Spread'
    object.data.uv_layers[0].active_render = True
    object.data.uv_layers[0].active = True

    # Update region:
    ns3d.region_3d.update()
    select_border(bpy.context)
    
    bpy.ops.uv.project_from_view(override, correct_aspect=True, 
        clip_to_bounds=True, scale_to_bounds=True)

    #assign image materials
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
    texImage.image = bpy.data.images.load(image_path)
    mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])

    ob = bpy.context.view_layer.objects.active

    # Assign it to object
    if ob.data.materials:
        ob.data.materials[0] = mat
    else:
        ob.data.materials.append(mat)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.material_slot_assign()

    
def process_mesh(heights_path, colors_path, image_paths, camera_angles):

    clear_meshes()
    H = torch.load("/Users/maxineperroni-scharf/Desktop/view-dependent/models/06_12_2023_18-07-38_heights.pt")
    COL = torch.load("/Users/maxineperroni-scharf/Desktop/view-dependent/models/06_12_2023_18-07-38_colors.pt")
    generate_mesh_with_segments(H, COL)
    for i in range(len(image_paths)):
        image_path = image_paths[i]
        cam_angle = camera_angles[i]
        proj_image_from_cam_loc(image_path, -cam_angle[0]*10, -cam_angle[1]*10, -cam_angle[2]*10)



heights_path = "/Users/maxineperroni-scharf/Desktop/view-dependent/models/06_12_2023_18-07-38_heights.pt"
colors_path = "/Users/maxineperroni-scharf/Desktop/view-dependent/models/06_12_2023_18-07-38_colors.pt"
image_paths = ["/Users/maxineperroni-scharf/Desktop/view-dependent/test_images/forest.png", "/Users/maxineperroni-scharf/Desktop/view-dependent/test_images/clouds.png"]
camera_angles = [[1, 0, -2], [-1, 0, -2]]


process_mesh(heights_path, colors_path, image_paths, camera_angles)



  
