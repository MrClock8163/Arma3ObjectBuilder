import bpy
import bpy_extras

from ..io_rtm import importer, exporter
from ..io_mcfg.validator import SkeletonValidator
from .. import utils
from .. import utils_io
from ..logger import ProcessLoggerNull


class A3OB_OP_export_rtm(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    """Export keyframes to Arma 3 RTM"""
    
    bl_idname = "a3ob.export_rtm"
    bl_label = "Export RTM"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}
    filename_ext = ".rtm"
    
    filter_glob: bpy.props.StringProperty(
        default = "*.rtm",
        options = {'HIDDEN'}
    )
    static_pose: bpy.props.BoolProperty(
        name = "Static Pose",
        description = "Export current frame as static pose"
    )
    frame_start: bpy.props.IntProperty(
        name = "Start",
        description = "Starting frame of animation",
        min = 0
    )
    frame_end: bpy.props.IntProperty(
        name = "End",
        description = "Ending frame of animation",
        default = 100,
        min = 0
    )
    frame_step: bpy.props.IntProperty(
        name = "Step",
        description = "Sampling step",
        default = 2,
        min = 1
    )
    frame_count: bpy.props.IntProperty(
        name = "Count",
        description = "Number of frames to sample (including start and end)",
        default = 20,
        min = 2
    )
    force_lowercase: bpy.props.BoolProperty(
        name = "Force Lowercase",
        description = "Export all bone names as lowercase",
        default = True
    )
    frame_source: bpy.props.EnumProperty(
        name = "Source",
        description = "Source of frames to export to RTM",
        items = (
            ('LIST', "List", "Export frames added to the RTM frame list of the active action"),
            ('SAMPLE_STEP', "Sample With Step", "Export frames sampled with the given step between the start and end frames"),
            ('SAMPLE_COUNT', "Sample With Count", "Export frames sampled with the given count (fractional frames will be rounded to the nearest integer, so the actual exported frame count will be less than desired)")
        ),
        default = 'SAMPLE_STEP'
    )
    skeleton_index: bpy.props.IntProperty(
        name = "Skeleton",
        description = "Skeleton to use to filter out control bones from armature",
        default = 0
    )
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'ARMATURE' and len(obj.pose.bones) > 0 and len(context.scene.a3ob_rigging.skeletons) > 0
        
    def draw(self, context):
        pass
        
    def invoke(self, context, event):
        self.frame_start = context.scene.frame_start
        self.frame_end = context.scene.frame_end
        
        return super().invoke(context, event)
        
    def execute(self, context):        
        obj = context.object
        action = None
        if obj.animation_data:
            action = obj.animation_data.action

        # Prevent cases where the start might be higher than the end due to user error
        start = min(self.frame_start, self.frame_end)
        end = max(self.frame_start, self.frame_end)

        self.frame_start = start
        self.frame_end = end
        
        scene_props = context.scene.a3ob_rigging
        skeleton = scene_props.skeletons[self.skeleton_index]
        validator = SkeletonValidator(ProcessLoggerNull())
        if not validator.validate(skeleton, True, True):
            utils.op_report(self, {'ERROR'}, "Invalid skeleton definiton, run skeleton validation for RTM for more info")
            return {'FINISHED'}

        with utils_io.ExportFileHandler(self.filepath, "wb") as file:
            static, frame_count = exporter.write_file(self, context, file, obj, action)
        
            if not self.static_pose and static:
                utils.op_report(self, {'INFO'}, "Exported as static pose")
            else:
                utils.op_report(self, {'INFO'}, "Exported %d frame(s)" % frame_count)
            
        return {'FINISHED'}
        

class A3OB_PT_export_rtm_main(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Main"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'HIDE_HEADER'}
    
    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        
        return operator.bl_idname == "A3OB_OT_export_rtm"
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        sfile = context.space_data
        operator = sfile.active_operator
        scene_props = context.scene.a3ob_rigging
        
        layout.prop(operator, "static_pose")
        layout.prop(operator, "force_lowercase")
        layout.template_list("A3OB_UL_rigging_skeletons_noedit", "A3OB_rtm_skeletons", scene_props, "skeletons", operator, "skeleton_index", rows=3)


class A3OB_PT_export_rtm_frames(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Frames"
    bl_parent_id = "FILE_PT_operator"
    
    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        
        return operator.bl_idname == "A3OB_OT_export_rtm"
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        sfile = context.space_data
        operator = sfile.active_operator
        
        layout.enabled = not operator.static_pose
        layout.prop(operator, "frame_start")
        layout.prop(operator, "frame_end")
        layout.prop(operator, "frame_source")
        if operator.frame_source == 'SAMPLE_STEP':
            layout.prop(operator, "frame_step")
        elif operator.frame_source == 'SAMPLE_COUNT':
            layout.prop(operator, "frame_count")


class A3OB_OP_import_rtm(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """Import action from Arma 3 RTM"""

    bl_idname = "a3ob.import_rtm"
    bl_label = "Import RTM"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}
    filename_ext = '*.rtm'

    filter_glob: bpy.props.StringProperty(
        default = "*.rtm",
        options = {'HIDDEN'}
    )
    apply_motion: bpy.props.BoolProperty(
        name = "Apply Motion",
        description = "Bake the motion vector into the keyframes",
        default = True
    )
    mute_constraints: bpy.props.BoolProperty(
        name = "Mute Constraints",
        description = "Mute constraints on affected pose bones",
        default = True
    )
    make_active: bpy.props.BoolProperty(
        name = "Make Active",
        description = "Make the imported animation the active action",
        default = True
    )
    frame_start: bpy.props.IntProperty(
        name = "Start",
        description = "Starting frame of animation",
        min = 0
    )
    frame_end: bpy.props.IntProperty(
        name = "End",
        description = "Ending frame of animation",
        default = 100,
        min = 0
    )
    time: bpy.props.FloatProperty(
        name = "Time",
        description = "Length of animation in secods",
        default = 1,
        min = 0.1
    )
    fps: bpy.props.IntProperty(
        name = "FPS",
        description = "",
        default = 24,
        min = 1
    )
    fps_base: bpy.props.FloatProperty(
        name = "FPS Base",
        description = "",
        default = 1.0,
        min = 0.1
    )
    round_frames: bpy.props.BoolProperty(
        name = "Round Frames",
        description = "Round fractional frames to the nearest whole number",
        default = True
    )
    mapping_mode: bpy.props.EnumProperty(
        name = "Frame Calculation Mode",
        description = "Method to map RTM phases to frames",
        items = (
            ('RANGE', "Range", "Map phases to specified start-end range"),
            ('FPS', "FPS", "Map phases to specified range starting at 1, with the length of FPS * time"),
            ('DIRECT', "Direct", "Map each phase to new frame\n(ensures that no frames are lost to rounding, but might distort animation if RTM frames are not evenly spaced)"),
        ),
        default = 'DIRECT'
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'ARMATURE' and len(obj.pose.bones) > 0
    
    def draw(self, context):
        pass

    def invoke(self, context, event):
        self.frame_start = context.scene.frame_start
        self.frame_end = context.scene.frame_end
        self.fps = context.scene.render.fps
        self.fps_base = context.scene.render.fps_base
        
        return super().invoke(context, event)
    
    def execute(self, context):
        with open(self.filepath, "rb") as file:
            count_frames = importer.import_file(self, context, file)
        
        if count_frames > 0:
            utils.op_report(self, {'INFO'}, "Successfully imported %d frame(s)" % count_frames)

        return {'FINISHED'}


class A3OB_PT_import_rtm_main(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Main"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'HIDE_HEADER'}
    
    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        
        return operator.bl_idname == "A3OB_OT_import_rtm"
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "make_active")
        layout.prop(operator, "apply_motion")
        layout.prop(operator, "mute_constraints")
        

class A3OB_PT_import_rtm_mapping(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Frame Mapping"
    bl_parent_id = "FILE_PT_operator"
    
    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        
        return operator.bl_idname == "A3OB_OT_import_rtm"
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "round_frames")
        layout.prop(operator, "mapping_mode", text="Method")

        if operator.mapping_mode == 'RANGE':
            layout.prop(operator, "frame_start")
            layout.prop(operator, "frame_end")
        elif operator.mapping_mode == 'FPS':
            layout.prop(operator, "fps")
            layout.prop(operator, "fps_base")
            layout.prop(operator, "time")


classes = (
    A3OB_OP_export_rtm,
    A3OB_PT_export_rtm_main,
    A3OB_PT_export_rtm_frames,
    A3OB_OP_import_rtm,
    A3OB_PT_import_rtm_main,
    A3OB_PT_import_rtm_mapping
)

if bpy.app.version >= (4, 1, 0):
    class A3OB_FH_import_rtm(bpy.types.FileHandler):
        bl_label = "File handler for RTM import"
        bl_import_operator = "a3ob.import_rtm"
        bl_file_extensions = ".rtm"
    
        @classmethod
        def poll_drop(cls, context):
            return context.area and context.area.type == 'VIEW_3D'

    classes = (*classes, A3OB_FH_import_rtm)


def menu_func_export(self, context):
    self.layout.operator(A3OB_OP_export_rtm.bl_idname, text="Arma 3 animation (.rtm)")


def menu_func_import(self, context):
    self.layout.operator(A3OB_OP_import_rtm.bl_idname, text="Arma 3 animation (.rtm)")


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    
    print("\t" + "UI: RTM Import / Export")


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    
    print("\t" + "UI: RTM Import / Export")
