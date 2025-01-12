import traceback
import os
import struct

import bpy
import mathutils

from .. import get_icon
from .. import utils
from .. import utils_io
from ..utilities import lod as lodutils
from ..utilities import compat as computils
from ..io_p3d import importer


class A3OB_OT_proxy_realign_ocs(bpy.types.Operator):
    """Realign the proxy object coordinate system with proxy directions"""
    
    bl_idname = "a3ob.proxy_realign_ocs"
    bl_label = "Realign Coordinate System"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.mode == 'OBJECT' and len(context.selected_objects) == 1 and obj.type == 'MESH' and obj.a3ob_properties_object_proxy.is_a3_proxy
    
    def execute(self, context):
        obj = context.active_object
        importer.transform_proxy(obj)
            
        return {'FINISHED'}


class A3OB_OT_proxy_align(bpy.types.Operator):
    """Align the proxy object to another selected object"""
    
    bl_idname = "a3ob.proxy_align"
    bl_label = "Align To Object"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        selected = context.selected_objects
        
        if not obj or len(selected) != 2:
            return False
            
        selected.remove(obj)
        return obj.mode == 'OBJECT' and selected[0] and selected[0].mode == 'OBJECT' and selected[0].a3ob_properties_object_proxy.is_a3_proxy
    
    def execute(self, context):
        obj = context.active_object
        selected = context.selected_objects.copy()
        selected.remove(obj)
        proxy = selected[0]
        
        proxy.matrix_world = obj.matrix_world
        proxy.scale = mathutils.Vector((1, 1, 1))
                    
        return {'FINISHED'}


class A3OB_OT_proxy_align_object(bpy.types.Operator):
    """Align an object to a selected proxy object"""
    
    bl_idname = "a3ob.proxy_align_object"
    bl_label = "Align To Proxy"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        selected = context.selected_objects
        
        if not obj or len(selected) != 2:
            return False
            
        selected.remove(obj)
        return obj.mode == 'OBJECT' and obj.a3ob_properties_object_proxy.is_a3_proxy and selected[0] and selected[0].mode == 'OBJECT'
    
    def execute(self, context):
        proxy = context.active_object
        selected = context.selected_objects.copy()
        selected.remove(proxy)
        obj = selected[0]
        
        obj.matrix_world = proxy.matrix_world
        obj.scale = mathutils.Vector((1, 1, 1))
                    
        return {'FINISHED'}


class A3OB_OT_proxy_extract(bpy.types.Operator):
    """Import 1st LOD of proxy model in place of proxy object"""
    
    bl_idname = "a3ob.proxy_extract"
    bl_label = "Extract Proxy"
    bl_options = {'REGISTER', 'UNDO'}
    
    enclose: bpy.props.BoolProperty()
    groupby: bpy.props.EnumProperty(default='NONE', items=(('NONE', "", ""),))
    additional_data_allowed: bpy.props.BoolProperty(default=True)
    additional_data: bpy.props.EnumProperty(
        options = {'ENUM_FLAG'},
        items = (
            ('NORMALS', "", ""),
            ("FLAGS", "", ""),
            ('PROPS', "", ""),
            ('MASS', "", ""),
            ('SELECTIONS', "", ""),
            ('UV', "", ""),
            ('MATERIALS', "", "")
        ),
        default = {'NORMALS', 'PROPS', 'MASS', 'SELECTIONS', 'UV', 'MATERIALS'}
    )
    validate_meshes: bpy.props.BoolProperty(default=True)
    proxy_action: bpy.props.EnumProperty(items=(('SEPARATE', "", ""),), default='SEPARATE')
    first_lod_only: bpy.props.BoolProperty(default=True)
    translate_selections: bpy.props.BoolProperty()
    cleanup_empty_selections: bpy.props.BoolProperty()
    sections: bpy.props.EnumProperty(items=(("PRESERVE", "", ""),), default="PRESERVE")
    absolute_paths: bpy.props.BoolProperty(default=True)
    filepath: bpy.props.StringProperty()
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not obj:
            return False
            
        path = utils_io.abspath(obj.a3ob_properties_object_proxy.proxy_path)
        return obj.type == 'MESH' and len(context.selected_objects) == 1 and obj.a3ob_properties_object_proxy.is_a3_proxy and os.path.exists(path) and os.path.splitext(path)[1].lower() == '.p3d'
    
    def execute(self, context):
        proxy_object = context.active_object
        self.filepath = utils_io.abspath(proxy_object.a3ob_properties_object_proxy.proxy_path)
        with open(self.filepath, "rb") as file:
            try:
                lod_objects = importer.read_file(self, context, file)
                imported_object = lod_objects[0]
                imported_object.matrix_world = proxy_object.matrix_world
                imported_object.name = os.path.basename(self.filepath)
                imported_object.data.name = os.path.basename(self.filepath)
                bpy.data.meshes.remove(proxy_object.data)
                self.report({'INFO'}, "Successfully extracted proxy (check the logs in the system console)")
            except struct.error as ex:
                self.report({'ERROR'}, "Unexpected EndOfFile (check the system console)")
                traceback.print_exc()
            except Exception as ex:
                self.report({'ERROR'}, "%s (check the system console)" % ex)
                traceback.print_exc()
        
        return {'FINISHED'}


class A3OB_OT_proxy_copy(bpy.types.Operator):
    """Copy proxy to LOD objects"""
    
    bl_idname = "a3ob.proxy_copy"
    bl_label = "Copy Proxy"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.mode == 'OBJECT' and len(context.selected_objects) == 1 and obj.type == 'MESH' and obj.a3ob_properties_object_proxy.is_a3_proxy
    
    def invoke(self, context, event):
        scene_props = context.scene.a3ob_proxies
        scene_props.lod_objects.clear()
        
        object_pool = context.scene.objects
        
        proxy_object = context.active_object
        parent_object = proxy_object.parent
        
        for obj in context.scene.objects:
            if obj.type != 'MESH' or not obj.a3ob_properties_object.is_a3_lod or obj.parent != None or obj == parent_object:
                continue
            
            object_props = obj.a3ob_properties_object
            
            item = scene_props.lod_objects.add()
            item.name = obj.name
            item.lod = lodutils.format_lod_name(int(object_props.lod), object_props.resolution)
            
            scene_props.lod_objects_index = len(scene_props.lod_objects) - 1
            
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        scene_props = context.scene.a3ob_proxies
        layout = self.layout
        split = layout.split(factor=0.5)
        split.label(text="Object Name")
        split.label(text="LOD Type")
        layout.template_list("A3OB_UL_lod_objects_selector", "A3OB_proxies_copy", scene_props, "lod_objects", scene_props, "lod_objects_index")
    
    def execute(self, context):
        proxy_object = context.active_object
        scene = context.scene
        scene_props = scene.a3ob_proxies
        
        target_objects = [scene.objects[item.name] for item in scene_props.lod_objects if item.enabled]
        
        for obj in target_objects:
            new_proxy = proxy_object.copy()
            new_proxy.data = proxy_object.data.copy()
            
            obj.users_collection[0].objects.link(new_proxy)
            new_proxy.matrix_parent_inverse = obj.matrix_world.inverted()
            new_proxy.parent = obj
        
        return {'FINISHED'}


class A3OB_OT_proxy_copy_all(bpy.types.Operator):
    """Copy all proxies from a LOD object to another"""
    
    bl_idname = "a3ob.proxy_copy_all"
    bl_label = "Copy Proxies"
    bl_options = {'REGISTER', 'UNDO'}
    
    keep_transform: bpy.props.BoolProperty(
        name = "Keep Transformation",
        description = "Keep the visual world space transformations",
        default = True
    )
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        selected = [item for item in context.selected_objects if item.type == 'MESH' and item.mode == 'OBJECT' and item != obj and item.a3ob_properties_object.is_a3_lod]
        
        return obj and obj.type == 'MESH' and obj.mode == 'OBJECT' and obj.a3ob_properties_object.is_a3_lod and len(selected) == 1
    
    def execute(self, context):
        target = context.active_object
        source = [item for item in context.selected_objects if item.type == 'MESH' and item.mode == 'OBJECT' and item != target][0]
        proxies = [item for item in source.children if item.type == 'MESH' and item.a3ob_properties_object_proxy.is_a3_proxy]
        
        for item in proxies:
            new_proxy = item.copy()
            new_proxy.data = item.data.copy()
            target.users_collection[0].objects.link(new_proxy)
            ctx = {
                "selected_editable_objects": [new_proxy]
            }
            if self.keep_transform:
                computils.call_operator_ctx(bpy.ops.object.parent_clear, ctx, type='CLEAR_KEEP_TRANSFORM')
                ctx.update({
                    "active_object": target,
                    "selected_objects": [target, new_proxy],
                    "selected_editable_objects": [target, new_proxy]
                })
                computils.call_operator_ctx(bpy.ops.object.parent_set, ctx, type='OBJECT', keep_transform=True)
            else:
                computils.call_operator_ctx(bpy.ops.object.parent_clear, ctx)
                ctx.update({
                    "active_object": target,
                    "selected_objects": [target, new_proxy],
                    "selected_editable_objects": [target, new_proxy]
                })
                computils.call_operator_ctx(bpy.ops.object.parent_set, ctx, type='OBJECT')
        
        return {'FINISHED'}


class A3OB_OT_proxy_transfer(bpy.types.Operator):
    """Transfer proxies to a different LOD object"""
    
    bl_idname = "a3ob.proxy_transfer"
    bl_label = "Transfer Proxies"
    bl_options = {'REGISTER', 'UNDO'}
    
    keep_transform: bpy.props.BoolProperty(
        name = "Keep Transformation",
        description = "Keep the visual world space transformations",
        default = True
    )
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        selected = [item for item in context.selected_objects if item.type == 'MESH' and item.mode == 'OBJECT' and item != obj and item.a3ob_properties_object.is_a3_lod]
        
        return obj and obj.type == 'MESH' and obj.mode == 'OBJECT' and obj.a3ob_properties_object.is_a3_lod and len(selected) == 1
    
    def execute(self, context):
        target = context.active_object
        source = [item for item in context.selected_objects if item.type == 'MESH' and item.mode == 'OBJECT' and item != target][0]
        proxies = [item for item in source.children if item.type == 'MESH' and item.a3ob_properties_object_proxy.is_a3_proxy]
        
        for item in proxies:
            ctx = {
                "selected_editable_objects": [item]
            }
            if self.keep_transform:
                computils.call_operator_ctx(bpy.ops.object.parent_clear, ctx, type='CLEAR_KEEP_TRANSFORM')
                ctx.update({
                    "active_object": target,
                    "selected_objects": [target, item],
                    "selected_editable_objects": [target, item]
                })
                computils.call_operator_ctx(bpy.ops.object.parent_set, ctx, type='OBJECT', keep_transform=True)
            else:
                computils.call_operator_ctx(bpy.ops.object.parent_clear, ctx)
                ctx.update({
                    "active_object": target,
                    "selected_objects": [target, item],
                    "selected_editable_objects": [target, item]
                })
                computils.call_operator_ctx(bpy.ops.object.parent_set, ctx, type='OBJECT')
        
        return {'FINISHED'}
    

class A3OB_PT_proxies(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Object Builder"
    bl_label = "Proxies"
    bl_options = {'DEFAULT_CLOSED'}

    doc_url = "https://mrcmodding.gitbook.io/arma-3-object-builder/tools/proxies"
    
    @classmethod
    def poll(cls, context):
        return True
        
    def draw_header(self, context):
        utils.draw_panel_header(self)
        
    def draw(self, context):
        layout = self.layout
        
        col_align = layout.column(align=True)
        col_align.operator("a3ob.proxy_align", icon_value=get_icon("op_proxy_align"))
        col_align.operator("a3ob.proxy_align_object", icon_value=get_icon("op_proxy_align_object"))
        layout.operator("a3ob.proxy_realign_ocs", icon_value=get_icon("op_proxy_realign"))
        layout.operator("a3ob.proxy_extract", icon_value=get_icon("op_proxy_extract"))
        col_move = layout.column(align=True)
        col_move.operator("a3ob.proxy_copy", icon_value=get_icon("op_proxy_copy"))
        col_move.operator("a3ob.proxy_copy_all", icon_value=get_icon("op_proxy_copy_all"))
        col_move.operator("a3ob.proxy_transfer", icon_value=get_icon("op_proxy_transfer"))


class A3OB_UL_lod_objects_selector(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        row = layout.row(align=True)
        row.prop(item, "enabled", text="")
        row.label(text=item.name)
        row.label(text=item.lod)


classes = (
    A3OB_OT_proxy_align,
    A3OB_OT_proxy_align_object,
    A3OB_OT_proxy_realign_ocs,
    A3OB_OT_proxy_extract,
    A3OB_OT_proxy_copy,
    A3OB_OT_proxy_copy_all,
    A3OB_OT_proxy_transfer,
    A3OB_PT_proxies,
    A3OB_UL_lod_objects_selector
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    print("\t" + "UI: Proxies")


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    print("\t" + "UI: Proxies")
