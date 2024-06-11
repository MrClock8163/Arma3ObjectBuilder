# Backend functions of the renaming tools.


import re

import bpy


def refresh_rename_list(context):
    scene_props = context.scene.a3ob_renaming
    scene_props.path_list.clear()
    
    path_list = []
    if 'TEX' in scene_props.source_filter or 'RVMAT' in scene_props.source_filter:
        for mat in bpy.data.materials:
            mat_props = mat.a3ob_properties_material
            if 'TEX' in scene_props.source_filter:
                path_list.append(mat_props.texture_path)
                path_list.append(mat_props.color_raw)
                
            if 'RVMAT' in scene_props.source_filter:
                path_list.append(mat_props.material_path)
                
    if 'PROXY' in scene_props.source_filter:
        for obj in bpy.data.objects:
            if not obj.a3ob_properties_object_proxy.is_a3_proxy:
                continue
                
            path_list.append(obj.a3ob_properties_object_proxy.proxy_path)
            
    path_set = set(path_list)
    if "" in path_set:
        path_set.remove("")
        
    path_list = list(path_set)
    
    for path in path_list:
        new_item = scene_props.path_list.add()
        new_item.path = path


def rename_path(context):
    scene_props = context.scene.a3ob_renaming
    
    path_old = scene_props.path_list[scene_props.path_list_index].path
    path_new = scene_props.new_path
    source_filter = scene_props.source_filter
    
    if 'TEX' in source_filter or 'RVMAT' in source_filter:
        for mat in bpy.data.materials:
            mat_props = mat.a3ob_properties_material
            
            if 'TEX' in source_filter:
                if mat_props.texture_path == path_old:
                    mat_props.texture_path = path_new
                if mat_props.color_raw == path_old:
                    mat_props.color_raw = path_new
                    
            if 'RVMAT' in source_filter:
                if mat_props.material_path == path_old:
                    mat_props.material_path = path_new
                    
    if 'PROXY' in source_filter:
        for obj in bpy.data.objects:
            object_props = obj.a3ob_properties_object_proxy
            if not object_props.is_a3_proxy:
                continue
            
            if object_props.proxy_path == path_old:
                object_props.proxy_path = path_new
    
    refresh_rename_list(context)


def replace_root(path, root_old, root_new):
    if path.lower().startswith(root_old.lower()):
        return root_new + path[len(root_old):]
        
    return path


def rename_root(context):
    scene_props = context.scene.a3ob_renaming
    
    root_old = scene_props.root_old
    root_new = scene_props.root_new
    source_filter = scene_props.source_filter
    
    if 'TEX' in source_filter or 'RVMAT' in source_filter:
        for mat in bpy.data.materials:
            mat_props = mat.a3ob_properties_material
            
            if 'TEX' in source_filter:
                mat_props.texture_path = replace_root(mat_props.texture_path, root_old, root_new)
                mat_props.color_raw = replace_root(mat_props.color_raw, root_old, root_new)
            
            if 'RVMAT' in source_filter:
                mat_props.material_path = replace_root(mat_props.material_path, root_old, root_new)
            
    if 'PROXY' in source_filter:
        for obj in bpy.data.objects:
            object_props = obj.a3ob_properties_object_proxy
            if not object_props.is_a3_proxy:
                continue
                
            object_props.proxy_path = replace_root(object_props.proxy_path, root_old, root_new)


def rename_vertex_groups(context):
    scene_props = context.scene.a3ob_renaming
    name_old = scene_props.vgroup_old
    name_new = scene_props.vgroup_new
    match_whole = scene_props.vgroup_match_whole
    objects = context.selected_objects
    
    if not match_whole:
        pattern = re.compile(re.escape(name_old), re.IGNORECASE)
    
    for obj in objects:
        for group in obj.vertex_groups:
            if not match_whole:
                group.name = pattern.sub(name_new, group.name)
            else:
                if group.name.lower() == name_old.lower():
                    group.name = name_new
