import bpy
import bpy_extras

from ..io_armature import importer
from ..utilities import rigging as riggingutils
from ..utilities import generic as utils


class A3OB_OP_import_armature(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """Import Arma 3 armature"""

    bl_idname = "a3ob.import_armature"
    bl_label = "Import Pivots"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}
    filename_ext = "*.p3d"
    
    filter_glob: bpy.props.StringProperty(
        default = "*.p3d",
        options = {'HIDDEN'}
    )
    skeleton_index: bpy.props.IntProperty(
        name = "Skeleton To Reconstruct",
        default = 0
    )
    ignore_without_pivot: bpy.props.BoolProperty(
        name = "Ignore Without Pivot",
        description = "Only reconstruct bones that have their pivot point defined in the pivots model.\n(Bones without known pivots need to be positioned manually after import)",
        default = True
    )

    @classmethod
    def poll(cls, context):
        scene_props = context.scene.a3ob_rigging
        return len(scene_props.skeletons) > 0

    def draw(self, context):
        pass

    def execute(self, context):
        scene_props = context.scene.a3ob_rigging
        if not utils.is_valid_idx(self.skeleton_index, scene_props.skeletons):
            utils.op_report(self, {'ERROR'}, "No skeleton was selected")
            return {'FINISHED'}
        
        skeleton = scene_props.skeletons[self.skeleton_index]
        if riggingutils.bone_order_from_skeleton(skeleton) is None:
            utils.op_report(self, {'ERROR'}, "Invalid skeleton definiton, run skeleton validation for RTM for more info")
            return {'FINISHED'}

        importer.import_armature(self, skeleton)

        return {'FINISHED'}


class A3OB_PT_import_armature_main(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Main"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'HIDE_HEADER'}
    
    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        
        return operator.bl_idname == "A3OB_OT_import_armature"
    
    def draw(self, context):
        layout = self.layout
        sfile = context.space_data
        operator = sfile.active_operator
        scene_props = context.scene.a3ob_rigging

        layout.template_list("A3OB_UL_rigging_skeletons_noedit", "A3OB_armature_skeletons", scene_props, "skeletons", operator, "skeleton_index", rows=3)
        layout.prop(operator, "ignore_without_pivot")


classes = (
    A3OB_OP_import_armature,
    A3OB_PT_import_armature_main
)


def menu_func_import(self, context):
    self.layout.operator(A3OB_OP_import_armature.bl_idname, text="Arma 3 armature (.p3d)")


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    
    print("\t" + "UI: Armature Import / Export")


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    
    print("\t" + "UI: Armature Import / Export")
