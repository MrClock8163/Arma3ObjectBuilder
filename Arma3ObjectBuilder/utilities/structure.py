# Backend functions of the utility functions.


import re

import bpy

from .. import utils
from . import compat as computils


def clear_components(obj):
    re_component = re.compile("component\d+", re.IGNORECASE)
    vgroups = [group for group in obj.vertex_groups if re_component.match(group.name)]
    while vgroups:
        obj.vertex_groups.remove(vgroups.pop())


def find_components(obj):
    utils.force_mode_object()
    
    clear_components(obj)
    
    component_verts, _, no_ignored = utils.get_closed_components(obj)
    
    for i, component in enumerate(component_verts):
        group = obj.vertex_groups.new(name="Component%02d" % (i + 1))
        group.add(component, 1, 'REPLACE')
    
    return len(component_verts), no_ignored


def component_convex_hull(obj):
    utils.force_mode_object()
    
    # Remove pre-existing component selections
    clear_components(obj)
    
    # Split mesh
    bpy.ops.mesh.separate(type='LOOSE')
    
    # Iterate components
    components = bpy.context.selected_objects
    bpy.ops.object.select_all(action='DESELECT')
    component_id = 0
    for component_object in components:
        component_id += 1
        
        bpy.context.view_layer.objects.active = component_object
        
        if len(component_object.data.vertices) < 4: # Ignore proxies
            continue
        
        convex_hull()
        
        group = component_object.vertex_groups.new(name=("Component%02d" % component_id))
        group.add([vert.index for vert in component_object.data.vertices], 1, 'REPLACE')
    
    if len(components) > 0:
        ctx = {
            "selected_objects": components,
            "selected_editable_objects": components,
            "active_object": obj
        }
        computils.call_operator_ctx(bpy.ops.object.join, ctx)
        
    bpy.context.view_layer.objects.active = obj
    
    return component_id


def convex_hull():
    utils.force_mode_edit()
    
    bpy.ops.mesh.select_mode(type='EDGE')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.convex_hull(join_triangles=False)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.reveal()
    bpy.ops.object.mode_set(mode='OBJECT')


def check_closed():
    utils.force_mode_edit()
    
    bpy.ops.mesh.select_mode(type='EDGE')
    bpy.ops.mesh.select_non_manifold()


def check_convexity(obj):
    utils.force_mode_object()
    
    with utils.edit_bmesh(obj) as bm:
        count_concave = 0
        for edge in bm.edges:
            if edge.is_convex:
                continue

            face1 = edge.link_faces[0]
            face2 = edge.link_faces[1]
            dot = face1.normal.dot(face2.normal)
            
            if 0.9999 <= dot <=1.0001:
                continue
            
            edge.select_set(True)
            count_concave += 1
    
    return count_concave


def cleanup_vertex_groups(obj):
    obj.update_from_editmode()
    
    removed = 0
    used_groups = {}
    for vert in obj.data.vertices:
        for group in vert.groups:
            group_index = group.group
            used_groups[group_index] = obj.vertex_groups[group_index]
    
    vgroups = [group for group in obj.vertex_groups]
    while vgroups:
        group = vgroups.pop()
        if group.index not in used_groups:
            obj.vertex_groups.remove(group)
            removed += 1
        
    return removed


def redefine_vertex_group(obj, weight):
    obj.update_from_editmode()
    
    group = obj.vertex_groups.active
    if group is None:
        return
    
    with utils.edit_bmesh(obj) as bm:
        bm.verts.ensure_lookup_table()
        bm.verts.layers.deform.verify()
        deform = bm.verts.layers.deform.active
        
        for vert in bm.verts:
            if vert.select:
                vert[deform][group.index] = weight
            elif group.index in vert[deform]:
                del vert[deform][group.index]
