import bpy

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