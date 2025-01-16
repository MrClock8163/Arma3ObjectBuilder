import bpy

from . import props
from . import rigging
from . import ofp2_manskeleton
from .. import get_icon
from .. import utils
from ..io_mcfg.validator import SkeletonValidator
from ..logger import ProcessLogger


def get_skeleton(scene_props):
    if not utils.is_valid_idx(scene_props.skeletons_index, scene_props.skeletons):
        return None
    
    return scene_props.skeletons[scene_props.skeletons_index]


class A3OB_UL_rigging_skeletons(bpy.types.UIList):
    use_filter_sort_alpha: bpy.props.BoolProperty(
        name = "Sort By Name",
        description = "Sort items by their name"
    )

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if not item.protected:
            layout.prop(item, "name", text="", icon='ARMATURE_DATA', emboss=False)
            layout.prop(item, "protected", text="", icon='UNLOCKED', emboss=False)
        else:
            layout.label(text=item.name, icon='ARMATURE_DATA')
            layout.prop(item, "protected", text="", icon='LOCKED', emboss=False)
    
    def draw_filter(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "filter_name", text="")
        row.prop(self, "use_filter_invert", text="", icon='ARROW_LEFTRIGHT')
        row.separator()
        row.prop(self, "use_filter_sort_alpha", text="", icon='SORTALPHA')
        row.prop(self, "use_filter_sort_reverse", text="", icon='SORT_DESC' if self.use_filter_sort_reverse else 'SORT_ASC')
    
    def filter_items(self, context, data, propname):
        helper_funcs = bpy.types.UI_UL_list
        flt_flags = []
        flt_neworder = []
        
        skeletons = getattr(data, propname)
        if self.filter_name:
            flt_flags = helper_funcs.filter_items_by_name(self.filter_name, self.bitflag_filter_item, skeletons, "name")

        if self.use_filter_sort_alpha:
            flt_neworder = helper_funcs.sort_items_by_name(skeletons, "name")
        
        return flt_flags, flt_neworder


class A3OB_UL_rigging_skeletons_noedit(bpy.types.UIList):
    use_filter_sort_alpha: bpy.props.BoolProperty(
        name = "Sort By Name",
        description = "Sort items by their name"
    )

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.label(text=item.name, icon='ARMATURE_DATA')
    
    def draw_filter(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "filter_name", text="")
        row.prop(self, "use_filter_invert", text="", icon='ARROW_LEFTRIGHT')
        row.separator()
        row.prop(self, "use_filter_sort_alpha", text="", icon='SORTALPHA')
        row.prop(self, "use_filter_sort_reverse", text="", icon='SORT_DESC' if self.use_filter_sort_reverse else 'SORT_ASC')

    def filter_items(self, context, data, propname):
        helper_funcs = bpy.types.UI_UL_list
        flt_flags = []
        flt_neworder = []
        
        skeletons = getattr(data, propname)
        if self.filter_name:
            flt_flags = helper_funcs.filter_items_by_name(self.filter_name, self.bitflag_filter_item, skeletons, "name")

        if self.use_filter_sort_alpha:
            flt_neworder = helper_funcs.sort_items_by_name(skeletons, "name")
        
        return flt_flags, flt_neworder


class A3OB_UL_rigging_bones(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        if not data.protected:
            layout.alignment = 'LEFT'
            layout.prop(item, "name", text="", icon='BONE_DATA', emboss=False)
            layout.label(text=":")
            layout.prop(item, "parent", text="", emboss=False)
        elif item.parent:
            layout.label(text="%s : %s" % (item.name, item.parent), icon='BONE_DATA')
        else:
            layout.label(text=item.name, icon='BONE_DATA')


class A3OB_OT_rigging_skeletons_add(bpy.types.Operator):
    """Add new skeleton definition"""

    bl_idname = "a3ob.rigging_skeletons_add"
    bl_label = "Add Skeleton"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        scene_props = context.scene.a3ob_rigging
        skeleton = scene_props.skeletons.add()
        skeleton.name = "Skeleton"
        
        if utils.is_valid_idx(scene_props.skeletons_index, scene_props.skeletons) and utils.is_valid_idx(scene_props.skeletons_index + 1, scene_props.skeletons):
            move_to = scene_props.skeletons_index + 1
            scene_props.skeletons.move(len(scene_props.skeletons) - 1, move_to)
            scene_props.skeletons_index = move_to
        else:
            scene_props.skeletons_index = len(scene_props.skeletons) - 1
    
        return {'FINISHED'}


class A3OB_OT_rigging_skeletons_remove(bpy.types.Operator):
    """Remove skeleton definition"""

    bl_idname = "a3ob.rigging_skeletons_remove"
    bl_label = "Remove Skeleton"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        scene_props = context.scene.a3ob_rigging
        return get_skeleton(scene_props)
    
    def execute(self, context):
        scene_props = context.scene.a3ob_rigging
        scene_props.skeletons.remove(scene_props.skeletons_index)
        scene_props.skeletons_index = max(0, scene_props.skeletons_index - 1)
    
        return {'FINISHED'}


class A3OB_OT_rigging_skeletons_from_armature(bpy.types.Operator):
    """Create skeleton definition from active armature object"""

    bl_idname = "a3ob.rigging_skeletons_from_armature"
    bl_label = "Skeleton From Armature"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'ARMATURE'
    
    def execute(self, context):
        obj = context.active_object
        obj.update_from_editmode()
        scene_props = context.scene.a3ob_rigging

        bones = rigging.bones_from_armature(obj)
        skeleton = scene_props.skeletons.add()
        skeleton.name = obj.name
        for name, parent in bones:
            bone = skeleton.bones.add()
            bone.name = name
            bone.parent = parent
        
        return {'FINISHED'}


class A3OB_OT_rigging_skeletons_clear(bpy.types.Operator):
    """Clear skeletons list"""

    bl_idname = "a3ob.rigging_skeletons_clear"
    bl_label = "Clear Skeletons"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        scene_props = context.scene.a3ob_rigging
        return len(scene_props.skeletons) > 0
    
    def execute(self, context):
        scene_props = context.scene.a3ob_rigging
        scene_props.skeletons.clear()
        scene_props.skeletons_index = -1

        return {'FINISHED'}


class A3OB_OT_rigging_skeletons_validate(bpy.types.Operator):
    """Validate the active skeleton definition"""

    bl_idname = "a3ob.rigging_skeletons_validate"
    bl_label = "Validate Skeleton"
    bl_options = {'REGISTER'}

    for_rtm: bpy.props.BoolProperty(
        name = "For RTM",
        description = "Validate skeleton for use with RTM animations"
    )

    @classmethod
    def poll(cls, context):
        scene_props = context.scene.a3ob_rigging
        return utils.is_valid_idx(scene_props.skeletons_index, scene_props.skeletons)
    
    def execute(self, context):
        scene_props = context.scene.a3ob_rigging
        skeleton = scene_props.skeletons[scene_props.skeletons_index]
        validator = SkeletonValidator(ProcessLogger())
        success = validator.validate(skeleton, self.for_rtm)

        if success:
            self.report({'INFO'}, "Validation succeeded")
        else:
            self.report({'ERROR'}, "Validation failed (check the logs in the system console)")

        return {'FINISHED'}


class A3OB_OT_rigging_skeletons_bones_add(bpy.types.Operator):
    """Add new bone to skeleton definition"""

    bl_idname = "a3ob.rigging_skeletons_bones_add"
    bl_label = "Add Bone"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        scene_props = context.scene.a3ob_rigging
        skeleton = get_skeleton(scene_props)
        return skeleton and not skeleton.protected
    
    def execute(self, context):
        scene_props = context.scene.a3ob_rigging
        skeleton = get_skeleton(scene_props)
        bone = skeleton.bones.add()
        bone.name = "Bone"

        if utils.is_valid_idx(skeleton.bones_index, skeleton.bones) and utils.is_valid_idx(skeleton.bones_index + 1, skeleton.bones):
            move_to = skeleton.bones_index + 1
            skeleton.bones.move(len(skeleton.bones) - 1, move_to)
            skeleton.bones_index = move_to
        else:
            skeleton.bones_index = len(skeleton.bones) - 1
    
        return {'FINISHED'}


class A3OB_OT_rigging_skeletons_bones_remove(bpy.types.Operator):
    """Remove bone from skeleton definition"""

    bl_idname = "a3ob.rigging_skeletons_bones_remove"
    bl_label = "Remove Bone"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        scene_props = context.scene.a3ob_rigging
        skeleton = get_skeleton(scene_props)
        
        return skeleton and not skeleton.protected and utils.is_valid_idx(skeleton.bones_index, skeleton.bones)
    
    def execute(self, context):
        scene_props = context.scene.a3ob_rigging
        skeleton = get_skeleton(scene_props)
        skeleton.bones.remove(skeleton.bones_index)
        skeleton.bones_index = max(0, skeleton.bones_index - 1)
    
        return {'FINISHED'}


class A3OB_OT_rigging_skeletons_bones_move(bpy.types.Operator):
    """Move Bone"""
    
    bl_idname = "a3ob.rigging_skeletons_bones_move"
    bl_label = "Move Bone"
    bl_options = {'REGISTER'}

    direction: bpy.props.EnumProperty(
        name = "Direction",
        items = (
            ('UP', "Up", ""),
            ('DOWN', "Down", "")
        )
    )
    
    @classmethod
    def poll(cls, context):
        scene_props = context.scene.a3ob_rigging  
        skeleton = get_skeleton(scene_props)

        return skeleton and not skeleton.protected and utils.is_valid_idx(skeleton.bones_index, skeleton.bones)
    
    def execute(self, context):
        scene_props = context.scene.a3ob_rigging
        skeleton = get_skeleton(scene_props)

        move_from = skeleton.bones_index
        move_to = move_from + (1 if self.direction == 'DOWN' else -1)
        skeleton.bones.move(move_from, move_to)
        skeleton.bones_index = max(min(move_to, len(skeleton.bones) - 1), 0)
        
        return {'FINISHED'}


class A3OB_OT_rigging_skeletons_bones_clear(bpy.types.Operator):
    """Clear bones from skeleton definition"""

    bl_idname = "a3ob.rigging_skeletons_bones_clear"
    bl_label = "Clear Bones"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        scene_props = context.scene.a3ob_rigging        
        skeleton = get_skeleton(scene_props)
        
        return skeleton and not skeleton.protected and len(skeleton.bones) > 0
    
    def execute(self, context):
        scene_props = context.scene.a3ob_rigging
        skeleton = get_skeleton(scene_props)
        skeleton.bones.clear()
        skeleton.bones_index = -1
    
        return {'FINISHED'}


class A3OB_OT_rigging_skeletons_bones_lowercase(bpy.types.Operator):
    """Make all bone names lowercase"""

    bl_idname = "a3ob.rigging_skeletons_bones_lowercase"
    bl_label = "Make Lowercase"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        scene_props = context.scene.a3ob_rigging
        skeleton = get_skeleton(scene_props)
        
        return skeleton and not skeleton.protected and len(skeleton.bones) > 0
    
    def execute(self, context):
        scene_props = context.scene.a3ob_rigging
        skeleton = get_skeleton(scene_props)

        for item in skeleton.bones:
            item.name = item.name.lower()
            item.parent = item.parent.lower()
        
        return {'FINISHED'}


class A3OB_OT_rigging_skeletons_ofp2manskeleton(bpy.types.Operator):
    """Add OFP2_ManSkeleton definition"""
    
    bl_idname = "a3ob.rigging_skeletons_ofp2manskeleton"
    bl_label = "Add OFP2_ManSkeleton"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        scene_props = context.scene.a3ob_rigging
        skeleton = scene_props.skeletons.add()
        skeleton.name = "OFP2_ManSkeleton"
        skeleton.protected = True

        for name, parent in ofp2_manskeleton.bone_hierarchy:
            item = skeleton.bones.add()
            item.name = name
            item.parent = parent
        
        return {'FINISHED'}


class A3OB_OT_rigging_pivots_from_armature(bpy.types.Operator):
    """Generate pivot points memory LOD from armature and skeleton definition"""

    bl_idname = "a3ob.rigging_pivots_from_armature"
    bl_label = "Pivots From Armature"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        scene_props = context.scene.a3ob_rigging
        obj = context.active_object
        skeleton = get_skeleton(scene_props)
        
        return obj and obj.type == 'ARMATURE' and skeleton and len(skeleton.bones) > 0
    
    def execute(self, context):
        scene_props = context.scene.a3ob_rigging
        obj = context.active_object

        bones_parents = rigging.bone_order_from_skeleton(get_skeleton(scene_props))
        if bones_parents is None:
            self.report({'WARNING'}, "Circular dependency detected in skeleton definition")
            return {'FINISHED'}

        obj = rigging.pivots_from_armature(obj, bones_parents)
        context.scene.collection.objects.link(obj)

        return {'FINISHED'}


class A3OB_OT_rigging_weights_select_unnormalized(bpy.types.Operator):
    """Select vertices with not normalized deform weights"""
    
    bl_idname = "a3ob.rigging_weights_select_unnormalized"
    bl_label = "Select Unnormalized"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        scene_props = context.scene.a3ob_rigging
        return obj and len(context.selected_objects) == 1 and obj.type == 'MESH' and obj.mode == 'EDIT' and get_skeleton(scene_props)
        
    def execute(self, context):
        obj = context.active_object
        scene_props = context.scene.a3ob_rigging
        bones = get_skeleton(scene_props).bones
        
        bone_indices = rigging.get_bone_group_indices(obj, bones)
        rigging.select_vertices_unnormalized(obj, bone_indices)
        
        return {'FINISHED'}


class A3OB_OT_rigging_weights_select_overdetermined(bpy.types.Operator):
    """Select vertices with more than 4 deform bones assigned"""
    
    bl_idname = "a3ob.rigging_weights_select_overdetermined"
    bl_label = "Select Overdetermined"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        scene_props = context.scene.a3ob_rigging
        return obj and len(context.selected_objects) == 1 and obj.type == 'MESH' and obj.mode == 'EDIT' and get_skeleton(scene_props)
        
    def execute(self, context):
        obj = context.active_object
        scene_props = context.scene.a3ob_rigging
        bones = get_skeleton(scene_props).bones
        
        bone_indices = rigging.get_bone_group_indices(obj, bones)
        rigging.select_vertices_overdetermined(obj, bone_indices)
        
        return {'FINISHED'}


class A3OB_OT_rigging_weights_normalize(bpy.types.Operator):
    """Normalize weights to deform bones"""
    
    bl_idname = "a3ob.rigging_weights_normalize"
    bl_label = "Normalize Weights"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        scene_props = context.scene.a3ob_rigging
        return obj and len(context.selected_objects) == 1 and obj.type == 'MESH' and obj.mode == 'EDIT' and get_skeleton(scene_props)
        
    def execute(self, context):
        obj = context.active_object
        scene_props = context.scene.a3ob_rigging
        bones = get_skeleton(scene_props).bones
        
        bone_indices = rigging.get_bone_group_indices(obj, bones)
        normalized = rigging.normalize_weights(obj, bone_indices)
        
        self.report({'INFO'}, "Normalized weights on %d vertices" % normalized)
        
        return {'FINISHED'}


class A3OB_OT_rigging_weights_prune_overdetermined(bpy.types.Operator):
    """Prune excess deform bones from vertices with more than 4 assigned bones"""
    
    bl_idname = "a3ob.rigging_weights_prune_overdetermined"
    bl_label = "Prune Overdetermined"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        scene_props = context.scene.a3ob_rigging
        return obj and len(context.selected_objects) == 1 and obj.type == 'MESH' and obj.mode == 'EDIT' and get_skeleton(scene_props)
        
    def execute(self, context):
        obj = context.active_object
        scene_props = context.scene.a3ob_rigging
        bones = get_skeleton(scene_props).bones
        
        bone_indices = rigging.get_bone_group_indices(obj, bones)
        pruned = rigging.prune_overdetermined(obj, bone_indices)
        
        self.report({'INFO'}, "Pruned excess bones from %d vertices" % pruned)
        
        return {'FINISHED'}


class A3OB_OT_rigging_weights_prune(bpy.types.Operator):
    """Prune vertex groups below weight threshold"""
    
    bl_idname = "a3ob.rigging_weights_prune"
    bl_label = "Prune Selections"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and len(context.selected_objects) == 1 and obj.type == 'MESH' and obj.mode == 'EDIT'
        
    def execute(self, context):
        obj = context.active_object
        scene_props = context.scene.a3ob_rigging
        pruned = rigging.prune_weights(obj, scene_props.prune_threshold)
        
        self.report({'INFO'}, "Pruned selection(s) from %d vertices" % pruned)
        
        return {'FINISHED'}


class A3OB_OT_rigging_weights_cleanup(bpy.types.Operator):
    """General weight painting cleanup"""
    
    bl_idname = "a3ob.rigging_weights_cleanup"
    bl_label = "General Cleanup"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        scene_props = context.scene.a3ob_rigging
        return obj and len(context.selected_objects) == 1 and obj.type == 'MESH' and obj.mode == 'EDIT' and get_skeleton(scene_props)
        
    def execute(self, context):
        obj = context.active_object
        scene_props = context.scene.a3ob_rigging
        bones = get_skeleton(scene_props).bones
        
        bone_indices = rigging.get_bone_group_indices(obj, bones)
        cleaned = rigging.cleanup(obj, bone_indices, scene_props.prune_threshold)
        
        self.report({'INFO'}, "Cleaned up weight painting on %d vertices" % cleaned)
        
        return {'FINISHED'}


class A3OB_MT_rigging_skeletons(bpy.types.Menu):
    bl_label = "Skeleton Specials"

    def draw(self, context):
        layout = self.layout

        layout.operator("a3ob.rigging_skeletons_from_armature", icon='OUTLINER_OB_ARMATURE')
        layout.separator()
        layout.operator("a3ob.rigging_skeletons_ofp2manskeleton", icon='ARMATURE_DATA')
        layout.separator()
        layout.operator("a3ob.rigging_skeletons_validate", text="Validate", icon='VIEWZOOM')
        op = layout.operator("a3ob.rigging_skeletons_validate", text="Validate For RTM")
        op.for_rtm = True
        layout.separator()
        layout.operator("a3ob.rigging_skeletons_clear", text="Delete All Skeletons", icon='TRASH')


class A3OB_MT_rigging_bones(bpy.types.Menu):
    bl_label = "Bone Specials"

    def draw(self, context):
        layout = self.layout
        
        layout.operator("a3ob.rigging_skeletons_bones_lowercase", icon='SYNTAX_OFF')
        layout.separator()
        layout.operator("a3ob.rigging_skeletons_bones_clear", text="Delete All Bones", icon='TRASH')


class A3OB_PT_rigging(bpy.types.Panel, utils.PanelHeaderLinkMixin):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Object Builder"
    bl_label = "Rigging"
    bl_options = {'DEFAULT_CLOSED'}

    doc_url = "https://mrcmodding.gitbook.io/arma-3-object-builder/tools/rigging"
    
    @classmethod
    def poll(cls, context):
        return True
    
    def draw(self, context):
        layout = self.layout
        scene_props = context.scene.a3ob_rigging

        row_skeletons = layout.row()
        col_skeletons_list = row_skeletons.column()

        col_skeletons_list.template_list("A3OB_UL_rigging_skeletons", "A3OB_rigging_skeletons", scene_props, "skeletons", scene_props, "skeletons_index", rows=4)

        col_skeletons_operators = row_skeletons.column(align=True)
        col_skeletons_operators.operator("a3ob.rigging_skeletons_add", text="", icon='ADD')
        col_skeletons_operators.operator("a3ob.rigging_skeletons_remove", text="", icon='REMOVE')
        col_skeletons_operators.separator()
        col_skeletons_operators.menu("A3OB_MT_rigging_skeletons", icon='DOWNARROW_HLT', text="")

        row_bones = layout.row()
        col_bones_list = row_bones.column()

        if utils.is_valid_idx(scene_props.skeletons_index, scene_props.skeletons):
            col_bones_list.template_list("A3OB_UL_rigging_bones", "A3OB_rigging_bones", scene_props.skeletons[scene_props.skeletons_index], "bones", scene_props.skeletons[scene_props.skeletons_index], "bones_index", rows=4)
        else:
            col_bones_list.template_list("A3OB_UL_rigging_bones", "A3OB_rigging_bones", scene_props, "bones", scene_props, "bones_index", rows=4)

        col_bones_operators = row_bones.column(align=True)
        col_bones_operators.operator("a3ob.rigging_skeletons_bones_add", text="", icon='ADD')
        col_bones_operators.operator("a3ob.rigging_skeletons_bones_remove", text="", icon='REMOVE')
        col_bones_operators.separator()
        col_bones_operators.menu("A3OB_MT_rigging_bones", icon='DOWNARROW_HLT', text="")
        col_bones_operators.separator()
        col_bones_operators.operator("a3ob.rigging_skeletons_bones_move", text="", icon='TRIA_UP').direction = 'UP'
        col_bones_operators.operator("a3ob.rigging_skeletons_bones_move", text="", icon='TRIA_DOWN').direction = 'DOWN'


        layout.operator("a3ob.rigging_pivots_from_armature", icon_value=get_icon("op_pivots_from_armature"))


class A3OB_PT_rigging_weights(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Object Builder"
    bl_label = "Weight Painting"
    bl_parent_id = "A3OB_PT_rigging"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        scene_props = context.scene.a3ob_rigging
        layout = self.layout

        col_select = layout.column(align=True)
        col_select.operator("a3ob.rigging_weights_select_overdetermined", icon_value=get_icon("op_weights_select_overdetermined"))
        col_select.operator("a3ob.rigging_weights_select_unnormalized", icon_value=get_icon("op_weights_select_unnormalized"))
        
        col_edit = layout.column(align=True)
        col_edit.operator("a3ob.rigging_weights_prune", icon_value=get_icon("op_weights_prune"))
        col_edit.operator("a3ob.rigging_weights_prune_overdetermined", icon_value=get_icon("op_weights_prune_overdetermined"))
        col_edit.operator("a3ob.rigging_weights_normalize", icon_value=get_icon("op_weights_normalize"))

        layout.operator("a3ob.rigging_weights_cleanup", icon_value=get_icon("op_weights_cleanup"))

        layout.prop(scene_props, "prune_threshold")


classes = (
    A3OB_UL_rigging_skeletons,
    A3OB_UL_rigging_skeletons_noedit,
    A3OB_UL_rigging_bones,
    A3OB_OT_rigging_skeletons_add,
    A3OB_OT_rigging_skeletons_remove,
    A3OB_OT_rigging_skeletons_clear,
    A3OB_OT_rigging_skeletons_validate,
    A3OB_OT_rigging_skeletons_from_armature,
    A3OB_OT_rigging_skeletons_bones_add,
    A3OB_OT_rigging_skeletons_bones_remove,
    A3OB_OT_rigging_skeletons_bones_move,
    A3OB_OT_rigging_skeletons_bones_clear,
    A3OB_OT_rigging_skeletons_bones_lowercase,
    A3OB_OT_rigging_skeletons_ofp2manskeleton,
    A3OB_OT_rigging_pivots_from_armature,
    A3OB_OT_rigging_weights_select_unnormalized,
    A3OB_OT_rigging_weights_select_overdetermined,
    A3OB_OT_rigging_weights_normalize,
    A3OB_OT_rigging_weights_prune_overdetermined,
    A3OB_OT_rigging_weights_prune,
    A3OB_OT_rigging_weights_cleanup,
    A3OB_MT_rigging_skeletons,
    A3OB_MT_rigging_bones,
    A3OB_PT_rigging,
    A3OB_PT_rigging_weights
)


def register():
    props.register_props()

    for cls in classes:
        bpy.utils.register_class(cls)
    
    print("\t" + "Tool: Rigging")


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    props.unregister_props()
    
    print("\t" + "Tool: Rigging")
