# Utility functions not exclusively related to a specific tool.


import os
import json
from datetime import datetime
from contextlib import contextmanager

import bpy
import bpy_extras.mesh_utils as meshutils
import bmesh

from .. import __package__ as addon_name
from . import data


def print_context():
    print("=======================")
    for attr in dir(bpy.context):
        print(attr, eval('bpy.context.%s' %  attr))
    print("=======================")


def show_info_box(message, title = "", icon = 'INFO'):
    def draw(self, context):
        self.layout.label(text=message)
        
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


# For some reason, not all operator reports are printed to the console. The behavior seems to be context dependent,
# but not certain.
def op_report(operator, mode, message):
    operator.report(mode, message)
    print("%s: %s\n" % (tuple(mode)[0].title(), message))


def abspath(path):
    if not path.startswith("//"):
        return path
    
    return os.path.abspath(bpy.path.abspath(path))


def strip_extension(path):
    return os.path.splitext(path)[0]


def get_addon_preferences():
    return bpy.context.preferences.addons[addon_name].preferences


def is_valid_idx(index, subscriptable):
    return len(subscriptable) > 0 and 0 <= index < len(subscriptable)


def draw_panel_header(panel):
    if not get_addon_preferences().show_info_links:
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


class OutputManager():
    def __init__(self, filepath, mode = "w"):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.filepath = filepath
        self.temppath = "%s.%s.temp" % (filepath, timestamp)
        self.backup = "%s.%s.bak" % (filepath, timestamp)
        self.mode = mode
        self.file = None
        self.success = False

    def __enter__(self):
        file = open(self.temppath, self.mode)
        self.file = file

        return file

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.file.close()
        addon_prefs = get_addon_preferences()

        if self.success:
            if os.path.isfile(self.filepath) and addon_prefs.create_backups:
                self.force_rename(self.filepath, self.filepath + ".bak")

            self.force_rename(self.temppath, self.filepath)
        
        elif not addon_prefs.preserve_faulty_output:
            os.remove(self.temppath)
        
        return False
    
    @staticmethod
    def force_rename(old, new):
        if os.path.isfile(new):
            os.remove(new)
        
        os.rename(old, new)
    
    # Very dirty check, but works for now
    @staticmethod
    def can_access_path(path):
        try:
            open(path, "ab").close()
            os.rename(path, path)
            return True
        except:
            return False


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


def get_closed_components(obj):
    def is_contiguous_chunk(bm, chunk):
        if len(chunk) < 4:
            return False
        
        face_indices = set([tri.polygon_index for tri in chunk])
        for idx in face_indices:
            for edge in bm.faces[idx].edges:
                if not edge.is_contiguous:
                    return False

        return True
    
    mesh = obj.data
    mesh.calc_loop_triangles()
    chunks = meshutils.mesh_linked_triangles(mesh)

    component_verts = []
    component_tris = []
    no_ignored = True

    with query_bmesh(obj) as bm:
        bm.faces.ensure_lookup_table()

        chunk: list[bpy.types.MeshLoopTriangle]
        for chunk in chunks:
            if not is_contiguous_chunk(bm, chunk):
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
    addon_prefs = get_addon_preferences()
    
    if path == "":
        return ""
    
    if os.path.splitext(path)[1].lower() != extension:
        path += extension
    
    root = abspath(addon_prefs.project_root).lower()
    if not path.startswith(root):
        abs_path = os.path.join(root, path)
        if os.path.exists(abs_path):
            return abs_path
    
    return path


def make_relative(path, root):
    path = path.lower()
    root = root.lower()
    
    if root != "" and path.startswith(root):
        return os.path.relpath(path, root)
    
    drive = os.path.splitdrive(path)[0]
    if drive:
       path = os.path.relpath(path, drive)
    
    return path


def format_path(path, root = "", to_relative = True, extension = True):
    path = replace_slashes(path.strip())
    
    if to_relative:
        root = replace_slashes(root.strip())
        path = make_relative(path, root)
        
    if not extension:
        path = strip_extension(path)
        
    return path


def get_addon_directory():
    return os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))


def get_cfg_convert():
    return os.path.join(get_addon_preferences().a3_tools, "cfgconvert/cfgconvert.exe")


def load_common_data(scene):
    prefs = get_addon_preferences()
    custom_path = abspath(prefs.custom_data)
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


preview_collection = {}


def get_icon(name):
    icon = 0
    try:
        icon = preview_collection[get_addon_preferences().icon_theme.lower()][name].icon_id
    except:
        pass
        
    return icon


def register_icons():
    import bpy.utils.previews
    
    themes_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../icons"))
    for theme in os.listdir(themes_dir):
        theme_icons = bpy.utils.previews.new()
        
        icons_dir = os.path.join(themes_dir, theme)
        for filename in os.listdir(icons_dir):
            theme_icons.load(os.path.splitext(os.path.basename(filename))[0].lower(), os.path.join(icons_dir, filename), 'IMAGE')
        
        preview_collection[theme.lower()] = theme_icons
    

def unregister_icons():
    import bpy.utils.previews
    
    for icon in preview_collection.values():
        bpy.utils.previews.remove(icon)
    
    preview_collection.clear()
