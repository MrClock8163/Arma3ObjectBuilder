#   ---------------------------------------- HEADER ----------------------------------------
#   
#   Author: MrClock
#   Add-on: Arma 3 Object Builder
#   
#   Description:
#       The script converts objects set up with ATBX (ArmaToolbox) properties to the
#       A3OB (Arma 3 Object Buikder) setup.
#
#   Usage:
#       1. switch every object that needs conversion to Object Mode
#       2. select objects to convert (if not all scene objects are to be converted)
#       3. set settings as necessary
#       4. run script
#   
#   ----------------------------------------------------------------------------------------


#   --------------------------------------- SETTINGS ---------------------------------------

class Settings:
    # Convert only selected objects
    only_selected = False
    # Clean up ATBX properties
    cleanup = True
    # Convert LOD objects
    convert_lod = True
    # Convert DTM objects
    convert_dtm = True


#   ---------------------------------------- LOGIC -----------------------------------------

import math
import importlib

import bpy

name = None
for addon in bpy.context.preferences.addons.keys():
    if addon.endswith("Arma3ObjectBuilder"):
        name = addon
        break
else:
    raise Exception("Arma 3 Object Builder could not be found")

a3ob_utils = importlib.import_module(addon).utilities
a3ob_io = importlib.import_module(addon).io

utils = a3ob_utils.generic
structutils = a3ob_utils.structure
lodutils = a3ob_utils.lod
ProcessLogger = a3ob_utils.logger.ProcessLogger
LOD = a3ob_io.data_p3d.P3D_LOD_Resolution
import_p3d = a3ob_io


LOD_TYPE_MAPPING = {
    '-1.0': str(LOD.VISUAL),
    '1.000e+3': str(LOD.VIEW_GUNNER),
    '1.100e+3': str(LOD.VIEW_PILOT),
    '1.200e+3': str(LOD.VIEW_CARGO),
    '1.000e+4': str(LOD.SHADOW),
    '1.001e+4': str(LOD.SHADOW),
    '1.100e+4': str(LOD.SHADOW),
    '1.101e+4': str(LOD.SHADOW),
    '2.000e+4': str(LOD.EDIT),
    '1.000e+13': str(LOD.GEOMETRY),
    '2.000e+13': str(LOD.GEOMETRY_BUOY),
    '4.000e+13': str(LOD.GEOMETRY_PHYSX),
    '1.000e+15': str(LOD.MEMORY),
    '2.000e+15': str(LOD.LANDCONTACT),
    '3.000e+15': str(LOD.ROADWAY),
    '4.000e+15': str(LOD.PATHS),
    '5.000e+15': str(LOD.HITPOINTS),
    '6.000e+15': str(LOD.VIEW_GEOMETRY),
    '7.000e+15': str(LOD.FIRE_GEOMETRY),
    '8.000e+15': str(LOD.VIEW_CARGO_GEOMERTRY),
    '9.000e+15': str(LOD.VIEW_CARGO_FIRE_GEOMETRY),
    '1.000e+16': str(LOD.VIEW_COMMANDER),
    '1.100e+16': str(LOD.VIEW_COMMANDER_GEOMETRY),
    '1.200e+16': str(LOD.VIEW_COMMANDER_FIRE_GEOMETRY),
    '1.300e+16': str(LOD.VIEW_PILOT_GEOMETRY),
    '1.400e+16': str(LOD.VIEW_PILOT_FIRE_GEOMETRY),
    '1.500e+16': str(LOD.VIEW_GUNNER_GEOMETRY),
    '1.600e+16': str(LOD.VIEW_GUNNER_FIRE_GEOMETRY),
    '1.700e+16': str(LOD.SUBPARTS),
    '1.800e+16': str(LOD.SHADOW_VIEW_CARGO),
    '1.900e+16': str(LOD.SHADOW_VIEW_PILOT),
    '2.000e+16': str(LOD.SHADOW_VIEW_GUNNER),
    '2.100e+16': str(LOD.WRECKAGE)
}


def convert_materials_item(material, cleanup):
    atbx_props = material.armaMatProps
    a3ob_props = material.a3ob_properties_material
    
    texture_type = atbx_props.texType
    
    if texture_type == 'Texture':
        a3ob_props.texture_type = 'TEX'
        a3ob_props.texture_path = atbx_props.texture
    elif texture_type == 'Color':
        a3ob_props.texture_type = 'COLOR'
        try:
            a3ob_props.color_type = atbx_props.colorType
        except:
            pass
        
        a3ob_props.color_value = (*atbx_props.colorValue, 1.0)
    elif texture_type == 'Custom':
        a3ob_props.texture_type = 'CUSTOM'
        a3ob_props.color_raw = atbx_props.colorString
        
    a3ob_props.material_path = atbx_props.rvMat
    
    if cleanup:
        atbx_props.texType = 'Texture'
        atbx_props.texture = ""
        atbx_props.colorString = ""
        atbx_props.colorValue = (1.0, 1.0, 1.0)
        atbx_props.rvMat = ""


def convert_materials(obj, converted_materials, cleanup, logger):
    count = 0
    for slot in obj.material_slots:
        mat = slot.material
        if not mat or mat.name in converted_materials:
            continue
        
        convert_materials_item(mat, cleanup)
        converted_materials.add(mat.name)
        count += 1
        
    if count > 0:
        logger.step("Materials: %s" % count)
    
    return converted_materials


def convert_proxy_item(obj, selections, cleanup):
    import_p3d.transform_proxy(obj)
    structutils.cleanup_vertex_groups(obj)
    a3ob_props = obj.a3ob_properties_object_proxy
    atbx_props = obj.armaObjProps
    
    atbx_props.isArmaObject = False
    atbx_props.namedProps.clear()
    
    vgroups = [group for group in obj.vertex_groups if group.name in selections]
    while vgroups:
        group = vgroups.pop()        
        proxy_data = selections[group.name]
        a3ob_props.proxy_path = proxy_data[0]
        a3ob_props.proxy_index = proxy_data[1]
        
        if cleanup:
            obj.vertex_groups.remove(group)
    
    obj.data.materials.clear()
            
    a3ob_props.is_a3_proxy = True


def convert_proxies(obj, cleanup, logger):
    proxy_selections = {proxy.name: (proxy.path, proxy.index) for proxy in obj.armaObjProps.proxyArray}
    if cleanup:
        obj.armaObjProps.proxyArray.clear()
    
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')

    for item in proxy_selections:
        group = obj.vertex_groups.get(item)
        if not group:
            continue

        obj.vertex_groups.active = group
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.separate(type='SELECTED')
        obj.vertex_groups.remove(group)
        
    bpy.ops.object.mode_set(mode='OBJECT')
    
    proxy_objects = [proxy for proxy in bpy.context.selected_objects if proxy is not obj]
    
    for proxy in proxy_objects:
        proxy.parent = obj
        convert_proxy_item(proxy, proxy_selections, cleanup)
        
    bpy.ops.object.select_all(action='DESELECT')
    
    if len(proxy_objects) > 0:
        logger.step("Proxies: %s" % len(proxy_objects))


def convert_namedprops(a3ob_props, atbx_props, logger):
    count = 0
    for namedprop in atbx_props.namedProps:
        new_item = a3ob_props.properties.add()
        new_item.name = namedprop.name
        new_item.value = namedprop.value
        count += 1
        
    if count > 0:
        logger.step("Named properties: %d" % count)


def convert_lod_properties(obj, cleanup, logger):
    a3ob_props = obj.a3ob_properties_object
    atbx_props = obj.armaObjProps
    
    try:
        a3ob_props.lod = LOD_TYPE_MAPPING[atbx_props.lod]
    except:
        a3ob_props.lod = str(LOD.UNKNOWN)
        
    a3ob_props.resolution = math.floor(atbx_props.lodDistance)
    a3ob_props.is_a3_lod = True
    
    logger.step("LOD name: %s" % lodutils.format_lod_name(int(a3ob_props.lod), a3ob_props.resolution))
    
    convert_namedprops(a3ob_props, atbx_props, logger)
    
    if cleanup:
        atbx_props.isArmaObject = False
        atbx_props.lod = '-1.0'
        atbx_props.lodDistance = 1.0
        atbx_props.namedProps.clear()
    
    obj.name = a3ob_props.get_name()
    obj.data.name = a3ob_props.get_name()


def convert_vertex_masses(obj, cleanup, logger):

    with utils.edit_bmesh(obj) as bm:    
        layer_atbx = bm.verts.layers.float.get("FHQWeights")
        if layer_atbx:
            layer_a3ob = bm.verts.layers.float.get("a3ob_mass")
            if not layer_a3ob:
                layer_a3ob = bm.verts.layers.float.new("a3ob_mass")
                
            for vertex in bm.verts:
                vertex[layer_a3ob] = vertex[layer_atbx]
                
            if cleanup:
                bm.verts.layers.float.remove(layer_atbx)
                
            logger.step("Vertex masses")


def convert_mesh(obj, converted_materials, cleanup, logger):
    convert_materials(obj, converted_materials, cleanup, logger)        
    convert_proxies(obj, cleanup, logger)
    convert_lod_properties(obj, cleanup, logger)
    convert_vertex_masses(obj, cleanup, logger)


def convert_dtm(obj, cleanup, logger):
    atbx_props = obj.armaHFProps
    a3ob_props = obj.a3ob_properties_object_dtm
    
    a3ob_props.cellsize_source = 'MANUAL'
    a3ob_props.cellsize = atbx_props.cellSize
    a3ob_props.origin = 'CORNER'
    a3ob_props.easting = atbx_props.easting
    a3ob_props.northing = atbx_props.northing
    a3ob_props.nodata = atbx_props.undefVal
    
    if cleanup:
        atbx_props.cellSize = 4
        atbx_props.easting = 0
        atbx_props.northing = 200_000
        atbx_props.undefVal = -9999
        atbx_props.isHeightfield = False


def convert_objects_item(obj, object_type, converted_materials, cleanup, logger):
    logger.level_up()
    
    if object_type == 'LOD':
        convert_mesh(obj, converted_materials, cleanup, logger)
    elif object_type == 'DTM':
        convert_dtm(obj, cleanup, logger)
        
    logger.level_down()


def convert_objects(objects, cleanup):
    logger = ProcessLogger()
    logger.step("Converting ATBX setup to A3OB")
    logger.level_up()
    categories = ('LOD', 'DTM')
    
    converted_materials = set()
    for i, category in enumerate(objects):
        logger.step("Category: %s" % categories[i])
        logger.level_up()
        
        for obj in category:
            logger.step(str(obj.name))
            convert_objects_item(obj, categories[i], converted_materials, cleanup, logger)
            logger.step("")
            
        logger.level_down()
    
    logger.level_down()
    logger.step("Conversion finished")


def start_conversion():
    settings = Settings
    context = bpy.context

    object_pool = []
    if settings.only_selected:
        object_pool = context.selected_objects
    else:
        object_pool = context.scene.objects
    
    objects_lod = []
    if settings.convert_lod:
        objects_lod = [obj for obj in object_pool if obj.visible_get() and obj.type == 'MESH' and hasattr(obj, "armaObjProps") and obj.armaObjProps.isArmaObject]
    objects_dtm = []
    if settings.convert_dtm:
        objects_dtm = [obj for obj in object_pool if obj.visible_get() and obj.type == 'MESH' and hasattr(obj, "armaHFProps") and obj.armaHFProps.isHeightfield]

    objects = [objects_lod, objects_dtm]

    for category in objects:
        for obj in category:
            if obj.mode != 'OBJECT':
                raise Exception("All objects must be in object mode in order to perform the conversion")
    
    bpy.ops.object.select_all(action='DESELECT')
    convert_objects(objects, settings.cleanup)


start_conversion()
