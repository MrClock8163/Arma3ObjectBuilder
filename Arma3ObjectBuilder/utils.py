# Utility functions not exclusively related to a specific tool.


import json
from contextlib import contextmanager

import bpy
import bpy_extras.mesh_utils as meshutils
import bmesh

from . import get_prefs
from .customdata import common_data


# For some reason, not all operator reports are printed to the console. The behavior seems to be context dependent,
# but not certain.
def op_report(operator, mode, message):
    operator.report(mode, message)
    print("%s: %s\n" % (tuple(mode)[0].title(), message))


def is_valid_idx(index, subscriptable):
    return len(subscriptable) > 0 and 0 <= index < len(subscriptable)


class PanelHeaderLinkMixin:
    doc_url = ""
    
    def draw_header(self, context):
        if not get_prefs().show_info_links or not self.doc_url:
            return
        
        row = self.layout.row(align=True)
        row.operator("wm.url_open", text="", icon='HELP', emboss=False).url = self.doc_url


@contextmanager
def edit_bmesh(obj, loop_triangles = False, destructive = False):
    mesh = obj.data
    if obj.mode == 'EDIT':
        try:
            yield bmesh.from_edit_mesh(mesh)
        finally:
            bmesh.update_edit_mesh(mesh, loop_triangles=loop_triangles, destructive=destructive)
    else:
        try:
            bm = bmesh.new()
            bm.from_mesh(mesh)
            yield bm
        finally:
            bm.to_mesh(mesh)
            bm.free()


@contextmanager
def query_bmesh(obj):
    mesh = obj.data
    if obj.mode == 'EDIT':
        try:
            bm = bmesh.from_edit_mesh(mesh)
            yield bm
        finally:
            bm.free()
    else:
        try:
            bm = bmesh.new()
            bm.from_mesh(mesh)
            yield bm
        finally:
            bm.free()


def get_loose_components(obj):
    mesh = obj.data
    mesh.calc_loop_triangles()
    chunks = meshutils.mesh_linked_triangles(mesh)

    component_verts = []
    component_tris = []

    for chunk in chunks:
        component_tris.append(chunk)
        component_verts.append(list({vert for tri in chunk for vert in tri.vertices}))
    
    return component_verts, component_tris


def get_closed_components(obj, selected_only = False):
    def is_contiguous_chunk(bm, chunk):
        if len(chunk) < 4:
            return False
        
        face_indices = set([tri.polygon_index for tri in chunk])
        for idx in face_indices:
            for edge in bm.faces[idx].edges:
                if not edge.is_contiguous:
                    return False

        return True
    
    def is_selected(bm: bmesh.types.BMesh, chunk):
        vert_indices = list({vidx for tri in chunk for vidx in tri.vertices})
        for idx in vert_indices:
            if not bm.verts[idx].select:
                return False
        
        return True
    
    mesh = obj.data
    mesh.calc_loop_triangles()
    chunks = meshutils.mesh_linked_triangles(mesh)

    component_verts = []
    component_tris = []
    no_ignored = True

    with query_bmesh(obj) as bm:
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        for chunk in chunks:
            if not is_contiguous_chunk(bm, chunk):
                no_ignored = False
                continue

            if selected_only and obj.mode == 'EDIT' and not is_selected(bm, chunk):
                no_ignored = False
                continue

            component_tris.append(chunk)
            component_verts.append(list({vert_id for tri in chunk for vert_id in tri.vertices}))

    return component_verts, component_tris, no_ignored


def force_mode_object():
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.reveal()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')


def force_mode_edit():
    force_mode_object()
    bpy.ops.object.mode_set(mode='EDIT')


def load_common_data(scene):
    custom_path = bpy.path.abspath(get_prefs().custom_data)
    builtin = common_data
    json_data = {}
    try:
        with open(custom_path) as file:
            json_data = json.load(file)
    except:
        pass

    common = {key: {**builtin[key], **json_data.get(key, {})} for key in builtin}

    scene_props = scene.a3ob_commons
    scene_props.items.clear()
    for category, items in common.items():
        for name, value in items.items():
            item = scene_props.items.add()
            item.name = name
            item.value = value
            item.type = category.upper()
    
    scene_props.items_index = 0
