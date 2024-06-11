from math import floor, ceil

import bpy

from ..utilities import generic as utils


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


class A3OB_PT_action(bpy.types.Panel):
    bl_region_type = 'UI'
    bl_space_type = 'DOPESHEET_EDITOR'
    bl_label = "RTM Properties"
    bl_context = "data"
    bl_category = "Object Builder"

    doc_url = "https://mrcmodding.gitbook.io/arma-3-object-builder/properties/rtm"
    
    @classmethod
    def poll(cls, context):
        return get_action(context.object)
        
    def draw_header(self, context):
        utils.draw_panel_header(self)
        
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
    A3OB_PT_action_props
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    print("\t" + "UI: action properties")


def unregister():    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    print("\t" + "UI: action properties")
