from math import floor, ceil

import bpy
import bpy_extras

from . import props, importer, exporter
from ..io_mcfg.validator import SkeletonValidator
from .. import utils
from .. import utils_io
from ..logger import ProcessLoggerNull


def get_action(obj):
    if not obj or obj.type != 'ARMATURE' or not obj.animation_data:
        return None
    
    return obj.animation_data.action


class A3OB_OT_rtm_frames_add(bpy.types.Operator):
    """Add current frame to list of RTM frames"""
    
    bl_idname = "a3ob.rtm_frames_add"
    bl_label = "Add Frame"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return get_action(context.object)
        
    def execute(self, context):
        action = get_action(context.object)
        action_props = action.a3ob_properties_action
        
        for frame in action_props.frames:
            if frame.index == context.scene.frame_current:
                self.report({'INFO'}, "The current frame is already in the list")
                return {'FINISHED'}
        
        item = action_props.frames.add()
        item.index = context.scene.frame_current
            
        return {'FINISHED'}


class A3OB_OT_rtm_frames_remove(bpy.types.Operator):
    """Remove selected frame from list of RTM frames"""
    
    bl_idname = "a3ob.rtm_frames_remove"
    bl_label = "Remove Frame"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        action = get_action(context.object)
        if not action:
            return False
        
        action_props = action.a3ob_properties_action
        return utils.is_valid_idx(action_props.frames_index, action_props.frames)
        
    def execute(self, context):
        action_props = get_action(context.object).a3ob_properties_action
        
        action_props.frames.remove(action_props.frames_index)
        if len(action_props.frames) == 0:
            action_props.frames_index = -1
        else:
            action_props.frames_index = len(action_props.frames) - 1
            
        return {'FINISHED'}


class A3OB_OT_rtm_frames_clear(bpy.types.Operator):
    """Clear all frames from list of RTM frames"""
    
    bl_idname = "a3ob.rtm_frames_clear"
    bl_label = "Clear Frames"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        action = get_action(context.object)
        return action and len(action.a3ob_properties_action.frames) > 0
        
    def execute(self, context):
        action_props = get_action(context.object).a3ob_properties_action
        
        action_props.frames.clear()
        action_props.frames_index = -1
            
        return {'FINISHED'}


class A3OB_OT_rtm_frames_add_range(bpy.types.Operator):
    """Add range of frames to list of RTM frames"""
    
    bl_idname = "a3ob.rtm_frames_add_range"
    bl_label = "Add Frame Range"
    bl_options = {'REGISTER', 'UNDO'}

    clear: bpy.props.BoolProperty(
        name = "Clear Existing",
        description = "Clear existing frames before adding the range",
        default = True
    )
    start: bpy.props.IntProperty(
        name = "Start",
        description = "First frame to add",
        default = 1,
        min = 0
    )
    step: bpy.props.IntProperty(
        name = "Step",
        description = "Step between frames",
        default = 5,
        min = 1
    )
    end: bpy.props.IntProperty(
        name = "End",
        description = "Last frame to add",
        default = 10,
        min = 0
    )
    
    @classmethod
    def poll(cls, context):
        return get_action(context.object)

    def invoke(self, context, event):
        action = get_action(context.object)
        frame_range = action.frame_range
        self.start = floor(frame_range[0])
        self.end = ceil(frame_range[1])

        return context.window_manager.invoke_props_dialog(self)
        
    def execute(self, context):
        action = get_action(context.object)
        action_props = action.a3ob_properties_action

        current_frames = [frame.index for frame in action_props.frames]

        action_props.frames.clear()

        new_frames = list(range(self.start, self.end + 1, self.step))
        if not self.clear:
            new_frames.extend(current_frames)

        new_frames.append(self.end)
        new_frames = list(set(new_frames))
        
        for idx in new_frames:
            item = action_props.frames.add()
            item.index = idx
            
        return {'FINISHED'}


class A3OB_OT_rtm_props_add(bpy.types.Operator):
    """Add property at current frame to RTM properties"""
    
    bl_idname = "a3ob.rtm_props_add"
    bl_label = "Add Property"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return get_action(context.object)
        
    def execute(self, context):
        action = get_action(context.object)
        action_props = action.a3ob_properties_action
        
        item = action_props.props.add()
        item.index = context.scene.frame_current
            
        return {'FINISHED'}


class A3OB_OT_rtm_props_remove(bpy.types.Operator):
    """Remove selected property from list of RTM properties"""
    
    bl_idname = "a3ob.rtm_props_remove"
    bl_label = "Remove Property"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        action = get_action(context.object)
        if not action:
            return False
        
        action_props = action.a3ob_properties_action
        return utils.is_valid_idx(action_props.props_index, action_props.props)
        
    def execute(self, context):
        action_props = get_action(context.object).a3ob_properties_action
        
        action_props.props.remove(action_props.props_index)
        if len(action_props.props) == 0:
            action_props.props_index = -1
        else:
            action_props.props_index = len(action_props.props) - 1
            
        return {'FINISHED'}


class A3OB_OT_rtm_props_clear(bpy.types.Operator):
    """Clear all properties from list of RTM properties"""
    
    bl_idname = "a3ob.rtm_props_clear"
    bl_label = "Clear Properties"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        action = get_action(context.object)
        return action and len(action.a3ob_properties_action.props) > 0
        
    def execute(self, context):
        action_props = get_action(context.object).a3ob_properties_action
        
        action_props.props.clear()
        action_props.props_index = -1
            
        return {'FINISHED'}


class A3OB_OT_rtm_props_move(bpy.types.Operator):
    """Move active property to selected frame index"""
    
    bl_idname = "a3ob.rtm_props_move"
    bl_label = "Move Property"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        action = get_action(context.object)
        if not action:
            return False
        
        action_props = action.a3ob_properties_action
        return utils.is_valid_idx(action_props.props_index, action_props.props)
        
    def execute(self, context):
        action = get_action(context.object)
        action_props = action.a3ob_properties_action
        
        item = action_props.props[action_props.props_index]
        item.index = context.scene.frame_current
            
        return {'FINISHED'}

 
class A3OB_UL_rtm_frames(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        index = item.index
        split = layout.split(factor=0.3)
        split.label(text=str(index))
        
        frame_range = context.scene.frame_end - context.scene.frame_start
        if frame_range > 0:
            phase = (index - context.scene.frame_start) / frame_range
            split.label(text="{:.6f}".format(phase))
        
    def filter_items(self, context, data, propname):
        helper_funcs = bpy.types.UI_UL_list
        flt_flags = []
        flt_neworder = []
        
        sorter = [(index, frame) for index, frame in enumerate(getattr(data, propname))]
        flt_neworder = helper_funcs.sort_items_helper(sorter, lambda f: f[1].index, False)
        
        return flt_flags, flt_neworder

 
class A3OB_UL_rtm_props(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        index = item.index
        layout.alignment = 'LEFT'
        
        layout.label(text=" %d" % item.index)
        layout.prop(item, "name", text="", emboss=False)
        layout.prop(item, "value", text="", emboss=False)
        
    def filter_items(self, context, data, propname):
        helper_funcs = bpy.types.UI_UL_list
        flt_flags = []
        flt_neworder = []
        
        sorter = [(index, frame) for index, frame in enumerate(getattr(data, propname))]
        flt_neworder = helper_funcs.sort_items_helper(sorter, lambda f: f[1].index, False)
        
        return flt_flags, flt_neworder


class A3OB_PT_action(bpy.types.Panel, utils.PanelHeaderLinkMixin):
    bl_region_type = 'UI'
    bl_space_type = 'DOPESHEET_EDITOR'
    bl_label = "RTM Properties"
    bl_context = "data"
    bl_category = "Object Builder"

    doc_url = "https://mrcmodding.gitbook.io/arma-3-object-builder/properties/rtm"
    
    @classmethod
    def poll(cls, context):
        return get_action(context.object)
        
    def draw(self, context):
        action = get_action(context.object)
        action_props = action.a3ob_properties_action
        
        layout = self.layout
        col = layout.column()
        col.use_property_split = True
        col.use_property_decorate = False
        row_enum = col.row()
        row_enum.prop(action_props, "motion_source", expand=True)
        
        if action_props.motion_source == 'MANUAL':
            col.prop(action_props, "motion_vector", text=" ")
        else:
            obj = context.object
            if obj and obj.type == 'ARMATURE':
                col.prop_search(action_props, "motion_bone", obj.data, "bones",  text="Reference")
            else:
                col.prop(action_props, "motion_bone", icon='BONE_DATA')


class A3OB_PT_action_frames(bpy.types.Panel):
    bl_region_type = 'UI'
    bl_space_type = 'DOPESHEET_EDITOR'
    bl_label = "Frames"
    bl_context = "data"
    bl_parent_id = "A3OB_PT_action"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        return get_action(context.object)
        
    def draw(self, context):
        action = get_action(context.object)
        action_props = action.a3ob_properties_action
        
        layout = self.layout
        
        row = layout.row()
        col_list = row.column()
        split_header = col_list.split(factor=0.3)
        split_header.label(text="Index")
        split_header.label(text="Phase")
        col_list.template_list("A3OB_UL_rtm_frames", "A3OB_rtm_frames", action_props, "frames", action_props, "frames_index")
        
        col_operators = row.column(align=True)
        col_operators.operator("a3ob.rtm_frames_add", text="", icon = 'ADD')
        col_operators.operator("a3ob.rtm_frames_remove", text="", icon = 'REMOVE')
        col_operators.separator()
        col_operators.operator("a3ob.rtm_frames_add_range", text="", icon = 'ARROW_LEFTRIGHT')
        col_operators.separator()
        col_operators.operator("a3ob.rtm_frames_clear", text="", icon = 'TRASH')


class A3OB_PT_action_props(bpy.types.Panel):
    bl_region_type = 'UI'
    bl_space_type = 'DOPESHEET_EDITOR'
    bl_label = "Properties"
    bl_context = "data"
    bl_parent_id = "A3OB_PT_action"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        return get_action(context.object)
    
    def draw(self, context):
        action = get_action(context.object)
        action_props = action.a3ob_properties_action

        layout = self.layout

        row = layout.row()
        col_list = row.column()
        row_header = col_list.row()
        row_header.label(text="Index")
        row_header.label(text="Name")
        row_header.label(text="Value")
        col_list.template_list("A3OB_UL_rtm_props", "A3OB_rtm_props", action_props, "props", action_props, "props_index")
        
        col_operators = row.column(align=True)
        col_operators.operator("a3ob.rtm_props_add", text="", icon = 'ADD')
        col_operators.operator("a3ob.rtm_props_remove", text="", icon = 'REMOVE')
        col_operators.separator()
        col_operators.operator("a3ob.rtm_props_move", text="", icon = 'NEXT_KEYFRAME')
        col_operators.separator()
        col_operators.operator("a3ob.rtm_props_clear", text="", icon = 'TRASH')


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
    A3OB_OT_rtm_frames_add,
    A3OB_OT_rtm_frames_remove,
    A3OB_OT_rtm_frames_clear,
    A3OB_OT_rtm_frames_add_range,
    A3OB_OT_rtm_props_add,
    A3OB_OT_rtm_props_remove,
    A3OB_OT_rtm_props_clear,
    A3OB_OT_rtm_props_move,
    A3OB_UL_rtm_frames,
    A3OB_UL_rtm_props,
    A3OB_PT_action,
    A3OB_PT_action_frames,
    A3OB_PT_action_props,
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
    props.register_props()

    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    
    print("\t" + "IO: RTM")


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    
    props.unregister_props()
    
    print("\t" + "IO: RTM")
