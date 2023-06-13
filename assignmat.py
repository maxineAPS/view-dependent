import bpy

def print(data):
    '''overwrite print in blender to all open consoles for easy debugging'''
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'CONSOLE':
                override = {'window': window, 'screen': screen, 'area': area}
                bpy.ops.console.scrollback_append(override, text=str(data), type="OUTPUT")      
               
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