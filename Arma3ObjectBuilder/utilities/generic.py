# Utility functions not exclusively related to a specific tool.


import os
import json
from contextlib import contextmanager
from datetime import datetime

import bpy
import bpy_extras.mesh_utils as meshutils
import bmesh

from .. import get_prefs
from . import data


# For some reason, not all operator reports are printed to the console. The behavior seems to be context dependent,
# but not certain.
def op_report(operator, mode, message):
    operator.report(mode, message)
    print("%s: %s\n" % (tuple(mode)[0].title(), message))


def abspath(path):
    if not path.startswith("//"):
        return path
    
    return os.path.abspath(bpy.path.abspath(path))


def is_valid_idx(index, subscriptable):
    return len(subscriptable) > 0 and 0 <= index < len(subscriptable)


def draw_panel_header(panel):
    if not get_prefs().show_info_links:
        return
        
    row = panel.layout.row(align=True)
    row.operator("wm.url_open", text="", icon='HELP', emboss=False).url = panel.doc_url


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


def create_selection(obj, selection):
    group = obj.vertex_groups.get(selection, None)
    if not group:
        group = obj.vertex_groups.new(name=selection.strip())

    group.add([vert.index for vert in obj.data.vertices], 1, 'REPLACE')


def clear_uvs(obj):
    uvs = [uv for uv in obj.data.uv_layers]

    while uvs:
        obj.data.uv_layers.remove(uvs.pop())


def replace_slashes(path):
    return path.replace("/", "\\")


# Attempt to restore absolute paths to the set project root (P drive by default).
def restore_absolute(path, extension = ""):
    path = replace_slashes(path.strip().lower())
    
    if path == "":
        return ""
    
    if os.path.splitext(path)[1].lower() != extension:
        path += extension
    
    root = abspath(get_prefs().project_root).lower()
    if not path.startswith(root):
        abs_path = os.path.join(root, path)
        if os.path.exists(abs_path):
            return abs_path
    
    return path


class PBOPrefixError(Exception):
    """Exception raised when $PBOPREFIX$ file is required but not found."""
    pass


def find_pboprefix(source_path):
    """
    Walk up the directory tree from source_path looking for a $PBOPREFIX$ file.
    Returns (prefix_content, pboprefix_directory) if found, or None if not found.
    The search is case-insensitive on Windows.
    """
    if not source_path:
        return None
    
    source_path = abspath(source_path)
    current_dir = os.path.dirname(source_path) if os.path.isfile(source_path) else source_path
    
    # Walk up the directory tree
    while current_dir:
        # Check for $PBOPREFIX$ file (case-insensitive on Windows)
        try:
            for filename in os.listdir(current_dir):
                if filename.lower() == "$pboprefix$":
                    pboprefix_path = os.path.join(current_dir, filename)
                    try:
                        with open(pboprefix_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            # Use first non-empty line
                            for line in content.splitlines():
                                line = line.strip()
                                if line:
                                    return (line, current_dir)
                    except (IOError, OSError):
                        pass
                    break
        except (IOError, OSError):
            pass
        
        # Move up one directory
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            # Reached root
            break
        current_dir = parent_dir
    
    return None


def make_relative(path, root, use_pboprefix=False, source_path=None):
    path = path.lower()
    root = root.lower()
    
    # If using PBOPREFIX, try to find and use it
    if use_pboprefix and source_path:
        pboprefix_result = find_pboprefix(source_path)
        if pboprefix_result:
            prefix, pboprefix_dir = pboprefix_result
            pboprefix_dir = pboprefix_dir.lower()
            # Make path relative to the PBOPREFIX directory and prepend the prefix
            if path.startswith(pboprefix_dir):
                rel_path = os.path.relpath(path, pboprefix_dir)
                # Combine prefix with relative path
                return os.path.join(prefix, rel_path)
        else:
            # PBOPREFIX required but not found - raise error
            raise PBOPrefixError(
                "Use $PBOPREFIX$ is enabled but no $PBOPREFIX$ file was found. "
                "Add a $PBOPREFIX$ file to your addon folder or untick 'Use $PBOPREFIX$' in export settings."
            )
    
    if root != "" and path.startswith(root):
        return os.path.relpath(path, root)
    
    drive = os.path.splitdrive(path)[0]
    if drive:
       path = os.path.relpath(path, drive)
    
    return path


def format_path(path, root = "", to_relative = True, extension = True, use_pboprefix = False, source_path = None):
    path = replace_slashes(path.strip())
    
    if to_relative:
        root = replace_slashes(root.strip())
        path = make_relative(path, root, use_pboprefix, source_path)
        
    if not extension:
        path = os.path.splitext(path)[0]
        
    return path


def load_common_data(scene):
    custom_path = abspath(get_prefs().custom_data)
    builtin = data.common_data
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


class ExportFileHandler():
    def __init__(self, filepath, mode):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.filepath = filepath
        self.temppath = "%s.%s.temp" % (filepath, timestamp)
        self.mode = mode
        self.file = None
        addon_pref = get_prefs()
        self.backup_old = addon_pref.create_backups
        self.preserve_faulty = addon_pref.preserve_faulty_output

    def __enter__(self):
        file = open(self.temppath, self.mode)
        self.file = file

        return file

    def __exit__(self, exc_type, exc_value, traceback):
        self.file.close()

        if exc_type is None:
            if os.path.isfile(self.filepath) and self.backup_old:
                self.force_rename(self.filepath, self.filepath + ".bak")

            self.force_rename(self.temppath, self.filepath)
        
        elif not self.preserve_faulty:
            os.remove(self.temppath)
    
    @staticmethod
    def force_rename(old, new):
        if os.path.isfile(new):
            os.remove(new)
        
        os.rename(old, new)
