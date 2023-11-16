import os

import bpy

from ..utilities import generic as utils
from ..utilities import lod as lodutils


def update_outliner(scene):
    context = bpy.context
    scene_props = scene.a3ob_outliner
    
    scene_props.lods.clear()
    
    lod_count = 0
    for obj in [obj for obj in scene.objects if obj.visible_get() or scene_props.show_hidden]:
        if obj.type != 'MESH' or not obj.a3ob_properties_object.is_a3_lod or obj.parent != None:
            continue
        
        if obj == context.active_object:
            scene_props.lods_index = lod_count
        
        object_props = obj.a3ob_properties_object
        
        item = scene_props.lods.add()
        item.name = obj.name
        item.lod = lodutils.format_lod_name(int(object_props.lod), object_props.resolution)
        
        lod_count += 1
    
    scene_props.proxies.clear()
    scene_props.sub_objects.clear()
    
    if scene_props.lods_index not in range(len(scene_props.lods)):
        return
    
    children = scene.objects[scene_props.lods[scene_props.lods_index].name].children
    
    sublod_count = 0
    proxy_count = 0
    for child in [obj for obj in children if obj.visible_get() or scene_props.show_hidden]:
        proxy_props = child.a3ob_properties_object_proxy
        
        if child.type == 'MESH' and not proxy_props.is_a3_proxy:
            new_sub = scene_props.sub_objects.add()
            new_sub.name = child.name
            
            if child == context.active_object:
                scene_props.sub_objects_index = sublod_count
        
            sublod_count += 1
                
        elif child.type == 'MESH':
            new_proxy = scene_props.proxies.add()
            new_proxy.name = child.name
            new_proxy.path = os.path.basename(os.path.splitext(utils.abspath(proxy_props.proxy_path))[0]).strip()
            new_proxy.index = proxy_props.proxy_index
            
            if child == context.active_object:
                scene_props.proxies_index = proxy_count
            
            proxy_count += 1


def update_selection():
    pass