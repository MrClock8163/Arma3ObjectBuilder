import bpy

from ..utilities import generic as utils
from ..utilities import lod as lodutils


class A3OB_OT_validate_lod(bpy.types.Operator):
    """Validate the selected object for the requirements of the set LOD type"""
    
    bl_idname = "a3ob.validate_for_lod"
    bl_label = "Validate LOD"
    bl_options = {'UNDO'}
    
    @classmethod
    def poll(cls, context):
        wm_props = context.window_manager.a3ob_validation
        obj = context.active_object
        return obj and obj.type == 'MESH' and (not wm_props.detect or obj.a3ob_properties_object.is_a3_lod)
        
    def execute(self, context):
        wm_props = context.window_manager.a3ob_validation
        obj = context.active_object
        
        if wm_props.detect:
            try:
                wm_props.lod = obj.a3ob_properties_object.lod
            except:
                self.report({'INFO'}, "No validation rules for detected LOD type")
                return {'FINISHED'}
        
        validator = lodutils.Validator(obj, wm_props.warning_errors)
        valid = validator.validate(wm_props.lod)
        if valid:
            self.report({'INFO'}, "Validation succeeded")
        else:
            self.report({'ERROR'}, "Validation failed (check the logs in the system console)")

        return {'FINISHED'}


class A3OB_PT_validation(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Object Builder"
    bl_label = "Validation"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        return True
        
    def draw_header(self, context):
        if not utils.get_addon_preferences().show_info_links:
            return
            
        layout = self.layout
        row = layout.row(align=True)
        row.operator("wm.url_open", text="", icon='HELP').url = "https://mrcmodding.gitbook.io/arma-3-object-builder/tools/validation"
        
    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        wm_props = wm.a3ob_validation
        
        layout.prop(wm_props, "detect")
        row_type = layout.row()
        row_type.prop(wm_props, "lod")
        if wm_props.detect:
            row_type.enabled = False
        layout.prop(wm_props, "warning_errors")
            
        layout.separator()
        layout.operator("a3ob.validate_for_lod", text="Validate", icon_value=utils.get_icon("op_validate"))
        

classes = (
    A3OB_OT_validate_lod,
    A3OB_PT_validation,
)


def register():
    from bpy.utils import register_class
    
    for cls in classes:
        register_class(cls)
    
    print("\t" + "UI: Validation")


def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)
    
    print("\t" + "UI: Validation")