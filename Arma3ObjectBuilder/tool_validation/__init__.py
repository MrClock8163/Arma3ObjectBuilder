import bpy

from . import props
from .. import get_icon
from .. import utils
from ..io_p3d.validator import LODValidator
from ..logger import ProcessLogger


class A3OB_OT_validate_lod(bpy.types.Operator):
    """Validate the selected object for the requirements of the set LOD type"""
    
    bl_idname = "a3ob.validate_for_lod"
    bl_label = "Validate LOD"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        scene_props = context.scene.a3ob_validation
        obj = context.active_object
        return obj and obj.type == 'MESH' and (not scene_props.detect or obj.a3ob_properties_object.is_a3_lod)
        
    def execute(self, context):
        scene_props = context.scene.a3ob_validation
        obj = context.active_object
        if obj.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        if scene_props.detect:
            try:
                scene_props.lod = obj.a3ob_properties_object.lod
            except:
                self.report({'ERROR'}, "No validation rules for detected LOD type")
                return {'FINISHED'}
        
        processor = LODValidator(ProcessLogger())
        processor.setup_lod_specific()
        valid = processor.validate(obj, scene_props.lod, False, scene_props.warning_errors, scene_props.relative_paths)
        for proxy in [item for item in obj.children if item.type == 'MESH' and item.a3ob_properties_object_proxy.is_a3_proxy]:
            valid &= processor.validate(proxy, '1', False, scene_props.warning_errors, scene_props.relative_paths)

            if len(proxy.data.polygons) != 1 or len(proxy.data.polygons[0].vertices) != 3:
                print("\tProxy has more than 1 face or the face is not a triangle")
                valid &= False

        if valid:
            self.report({'INFO'}, "Validation passed")
        else:
            self.report({'ERROR'}, "Validation failed (check the logs in the system console)")

        return {'FINISHED'}


class A3OB_PT_validation(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Object Builder"
    bl_label = "Validation"
    bl_options = {'DEFAULT_CLOSED'}

    doc_url = "https://mrcmodding.gitbook.io/arma-3-object-builder/tools/validation"
    
    @classmethod
    def poll(cls, context):
        return True
        
    def draw_header(self, context):
        utils.draw_panel_header(self)
        
    def draw(self, context):
        layout = self.layout
        scene_props = context.scene.a3ob_validation
        
        layout.prop(scene_props, "detect")
        row_type = layout.row()
        row_type.prop(scene_props, "lod")
        if scene_props.detect:
            row_type.enabled = False
        layout.prop(scene_props, "warning_errors")
        layout.prop(scene_props, "relative_paths")
            
        layout.separator()
        layout.operator("a3ob.validate_for_lod", text="Validate", icon_value=get_icon("op_validate"))
        

classes = (
    A3OB_OT_validate_lod,
    A3OB_PT_validation,
)


def register():
    props.register_props()

    from bpy.utils import register_class
    
    for cls in classes:
        register_class(cls)
    
    print("\t" + "Tool: Validation")


def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)
    
    props.unregister_props()
    
    print("\t" + "Tool: Validation")
