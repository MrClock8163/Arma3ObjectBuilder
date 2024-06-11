import traceback
import os

import bpy
import bpy_extras

from ..io import import_mcfg, export_mcfg
from ..utilities import generic as utils
from ..utilities.validator import Validator
from ..utilities.logger import ProcessLoggerNull


class A3OB_OP_import_mcfg(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """Import Arma 3 skeleton definition"""

    bl_idname = "a3ob.import_mcfg"
    bl_label = "Import Skeletons"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}
    filename_ext = "model.cfg"
    
    filter_glob: bpy.props.StringProperty(
        default = "*.cfg",
        options = {'HIDDEN'}
    )
    force_lowercase: bpy.props.BoolProperty(
        name = "Force Lowercase",
        description = "Import all bone names as lowercase",
        default = True
    )
    protected: bpy.props.BoolProperty(
        name = "Protected",
        description = "Import skeletons as protected",
        default = True
    )

    @classmethod
    def poll(cls, context):
        return os.path.isfile(utils.get_cfg_convert())

    def draw(self, context):
        pass

    def execute(self, context):
        count_skeletons = 0
        try:
            count_skeletons = import_mcfg.read_file(self, context)
        except import_mcfg.rap.RAP_Error as ex:
            utils.op_report(self, {'ERROR'}, "%s (check the system console)" % ex)
        except Exception as ex:
            utils.op_report(self, {'ERROR'}, "%s (check the system console)" % ex)
            traceback.print_exc()
        
        if count_skeletons > 0:
            utils.op_report(self, {'INFO'}, "Successfully imported %d skeleton(s)" % count_skeletons)
        
        return {'FINISHED'}


class A3OB_PT_import_mcfg_main(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Main"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'HIDE_HEADER'}
    
    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        
        return operator.bl_idname == "A3OB_OT_import_mcfg"
    
    def draw(self, context):
        layout = self.layout
        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "force_lowercase")
        layout.prop(operator, "protected")


class A3OB_OP_export_mcfg(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """Export Arma 3 skeleton definition"""

    bl_idname = "a3ob.export_mcfg"
    bl_label = "Export Skeleton"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}
    filename_ext = "model.cfg"
    
    filter_glob: bpy.props.StringProperty(
        default = "*.cfg",
        options = {'HIDDEN'}
    )
    force_lowercase: bpy.props.BoolProperty(
        name = "Force Lowercase",
        description = "Export all bone names as lowercase",
        default = True
    )
    skeleton_index: bpy.props.IntProperty(
        name = "Skeleton To Export",
        default = 0
    )

    @classmethod
    def poll(cls, context):
        scene_props = context.scene.a3ob_rigging
        return len(scene_props.skeletons) > 0
    
    def draw(self, context):
        pass

    def execute(self, context):
        if not utils.OutputManager.can_access_path(self.filepath):
            utils.op_report(self, {'ERROR'}, "Cannot write to target file (file likely in use by another blocking process)")
            return {'FINISHED'}
        
        scene_props = context.scene.a3ob_rigging
        skeleton = scene_props.skeletons[self.skeleton_index]
        output = utils.OutputManager(self.filepath, "w")

        validator = Validator(ProcessLoggerNull())
        if not validator.validate_skeleton(skeleton, False, True):
            utils.op_report(self, {'ERROR'}, "Invalid skeleton definiton, run skeleton validation for more info")
            return {'FINISHED'}
        
        with output as file:
            try:
                export_mcfg.write_file(self, skeleton, file)
                output.success = True
            except Exception as ex:
                utils.op_report(self, {'ERROR'}, "%s (check the system console)" % ex)
                traceback.print_exc()

        return {'FINISHED'}


class A3OB_PT_export_mcfg_main(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Main"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'HIDE_HEADER'}
    
    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        
        return operator.bl_idname == "A3OB_OT_export_mcfg"

    def draw(self, context):
        layout = self.layout
        sfile = context.space_data
        operator = sfile.active_operator
        scene_props = context.scene.a3ob_rigging

        layout.template_list("A3OB_UL_rigging_skeletons_noedit", "A3OB_armature_skeletons", scene_props, "skeletons", operator, "skeleton_index", rows=3)
        layout.prop(operator, "force_lowercase")


classes = (
    A3OB_OP_import_mcfg,
    A3OB_PT_import_mcfg_main,
    A3OB_OP_export_mcfg,
    A3OB_PT_export_mcfg_main
)

if bpy.app.version >= (4, 1, 0):
    class A3OB_FH_import_mcfg(bpy.types.FileHandler):
        bl_label = "File handler for MCFG import"
        bl_import_operator = "a3ob.import_mcfg"
        bl_file_extensions = ".cfg"
    
        @classmethod
        def poll_drop(cls, context):
            return context.area and context.area.type == 'VIEW_3D'

    classes = (*classes, A3OB_FH_import_mcfg)


def menu_func_import(self, context):
    self.layout.operator(A3OB_OP_import_mcfg.bl_idname, text="Arma 3 skeletons (model.cfg)")


def menu_func_export(self, context):
    self.layout.operator(A3OB_OP_export_mcfg.bl_idname, text="Arma 3 skeleton (model.cfg)")


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    
    print("\t" + "UI: MCFG Import / Export")


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    
    print("\t" + "UI: MCFG Import / Export")
