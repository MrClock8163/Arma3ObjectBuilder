import os

import bpy

from . import props
from . import utils as renameutils
from .. import get_icon
from .. import utils


class A3OB_OT_rename_list_refresh(bpy.types.Operator):
    """Refresh list of paths for bulk renaming"""
    
    bl_idname = "a3ob.rename_list_refresh"
    bl_label = "Refresh List"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return True
        
    def execute(self, context):
        renameutils.refresh_rename_list(context)
        
        return {'FINISHED'}


class A3OB_OT_rename_path_item(bpy.types.Operator):
    """Replace selected file path"""
    
    bl_idname = "a3ob.rename_path_item"
    bl_label = "Replace Path"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        scene_props = context.scene.a3ob_renaming
        return utils.is_valid_idx(scene_props.path_list_index, scene_props.path_list)
        
    def execute(self, context):
        renameutils.rename_path(context)
        return {'FINISHED'}


class A3OB_OT_rename_path_root(bpy.types.Operator):
    """Replace file roots"""
    
    bl_idname = "a3ob.rename_path_root"
    bl_label = "Replace Root"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        scene_props = context.scene.a3ob_renaming
        return scene_props.root_old.strip() != ""
        
    def execute(self, context):
        renameutils.rename_root(context)
        return {'FINISHED'}


class A3OB_OT_rename_vertex_groups(bpy.types.Operator):
    """Rename vertex groups of selected objects"""
    
    bl_idname = "a3ob.rename_vertex_groups"
    bl_label = "Rename Groups"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        scene_props = context.scene.a3ob_renaming
        return scene_props.vgroup_old.strip() != "" and scene_props.vgroup_new.strip() != "" and len(context.selected_objects) > 0
        
    def execute(self, context):
        renameutils.rename_vertex_groups(context)
        return {'FINISHED'}


class A3OB_PT_renaming(bpy.types.Panel, utils.PanelHeaderLinkMixin):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Object Builder"
    bl_label = "Renaming"
    bl_options = {'DEFAULT_CLOSED'}

    doc_url = "https://mrcmodding.gitbook.io/arma-3-object-builder/tools/renaming"

    def draw(self, context):
        pass


class A3OB_UL_renamable_paths(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.label(text=item.path, icon='BLANK1' if (os.path.isfile(item.path) or item.path.startswith("#")) else 'ERROR')


class A3OB_PT_renaming_paths_bulk(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Object Builder"
    bl_label = "Bulk Replace"
    bl_parent_id = "A3OB_PT_renaming"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        scene_props = context.scene.a3ob_renaming
        
        col_list = layout.column(align=True)
        
        col_list.template_list("A3OB_UL_renamable_paths", "A3OB_bulk_rename", scene_props, "path_list", scene_props, "path_list_index")
        row_filter = col_list.row(align=True)
        row_filter.operator("a3ob.rename_list_refresh", text="", icon_value=get_icon("op_refresh"))
        row_filter.prop(scene_props, "source_filter")
        
        if utils.is_valid_idx(scene_props.path_list_index, scene_props.path_list):
            col_edit = layout.column(align=True)
            row_path = col_edit.row(align=True)
            row_path.enabled = False
            row_path.prop(scene_props.path_list[scene_props.path_list_index], "path", text="")
            col_edit.prop(scene_props, "new_path", text="")
            col_edit.separator()
            col_edit.operator("a3ob.rename_path_item", icon_value=get_icon("op_replace"))


class A3OB_PT_renaming_paths_root(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Object Builder"
    bl_label = "Root Replace"
    bl_parent_id = "A3OB_PT_renaming"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        scene_props = context.scene.a3ob_renaming
        
        col_edit = layout.column(align=True)
        col_edit.prop(scene_props, "root_old")
        col_edit.prop(scene_props, "root_new")
        
        row_filter = layout.row(align=True)
        row_filter.prop(scene_props, "source_filter")
        
        layout.operator("a3ob.rename_path_root", icon_value=get_icon("op_replace"))


class A3OB_PT_renaming_vertex_groups(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Object Builder"
    bl_label = "Vertex Groups"
    bl_parent_id = "A3OB_PT_renaming"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        scene_props = context.scene.a3ob_renaming
        
        col_edit = layout.column(align=True)
        col_edit.prop(scene_props, "vgroup_old")
        col_edit.prop(scene_props, "vgroup_new")
        layout.prop(scene_props, "vgroup_match_whole")
        layout.operator("a3ob.rename_vertex_groups", icon_value=get_icon("op_replace"))


classes = (
    A3OB_OT_rename_list_refresh,
    A3OB_OT_rename_path_item,
    A3OB_OT_rename_path_root,
    A3OB_OT_rename_vertex_groups,
    A3OB_PT_renaming,
    A3OB_UL_renamable_paths,
    A3OB_PT_renaming_paths_bulk,
    A3OB_PT_renaming_paths_root,
    A3OB_PT_renaming_vertex_groups
)


def register():
    props.register_props()

    for cls in classes:
        bpy.utils.register_class(cls)
    
    print("\t" + "Tool: Renaming")


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    props.unregister_props()
    
    print("\t" + "Tool: Renaming")
