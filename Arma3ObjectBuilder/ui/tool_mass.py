from math import log10, ceil

import bpy

from .. import get_icon
from .. import utils
from ..utilities import masses as massutils


class A3OB_OT_vertex_mass_set(bpy.types.Operator):
    """Set same mass on all selected vertices"""
    
    bl_idname = "a3ob.vertex_mass_set"
    bl_label = "Set Mass On Each"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH' and context.scene.a3ob_mass_editor.value_type == 'MASS'
        
    def execute(self, context):
        obj = context.object
        scene = context.scene
        massutils.set_selection_mass_each(obj, scene.a3ob_mass_editor.value)
        return {'FINISHED'}


class A3OB_OT_vertex_mass_distribute(bpy.types.Operator):
    """Distribute mass equally to selected vertices"""
    
    bl_idname = "a3ob.vertex_mass_distribute"
    bl_label = "Distribute Mass"
    bl_options = {'REGISTER'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH' and context.scene.a3ob_mass_editor.value_type == 'MASS'
            
    def draw(self, context):
        layout = self.layout
        layout.label(text="Volume cell calculations become extremely slow at high mesh resolutions.")
        layout.label(text="Are you sure that you want to proceed?")

    def invoke(self, context, event):
        obj = context.object
        scene_props = context.scene.a3ob_mass_editor
        if len(obj.data.vertices) > 500 and scene_props.distribution != 'UNIFORM':
            return context.window_manager.invoke_props_dialog(self, width=500)
        
        return self.execute(context)
    
    def execute(self, context):
        obj = context.object
        scene = context.scene
        scene_props = scene.a3ob_mass_editor
        
        if scene_props.distribution == 'UNIFORM':
            massutils.set_selection_mass_distribute_uniform(obj, scene.a3ob_mass_editor.value)
        else:
            all_closed = massutils.set_selection_mass_distribute_weighted(obj, scene.a3ob_mass_editor.value)
            if not all_closed:
                if obj.mode == 'OBJECT':
                    self.report({'WARNING'}, "Non-closed or flat components were ignored")
                else:
                    self.report({'WARNING'}, "Non-closed, partially selected or flat components were ignored")

        return {'FINISHED'}


class A3OB_OT_vertex_mass_set_density(bpy.types.Operator):
    """Calculate mass distribution from volumetric density (operates on the entire mesh)"""
    
    bl_idname = "a3ob.vertex_mass_set_density"
    bl_label = "Mass From Density"
    bl_options = {'REGISTER'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH' and context.scene.a3ob_mass_editor.value_type == 'DENSITY'
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="Volume cell calculations become extremely slow at high mesh resolutions.")
        layout.label(text="Are you sure that you want to proceed?")

    def invoke(self, context, event):
        obj = context.object
        scene_props = context.scene.a3ob_mass_editor
        if len(obj.data.vertices) > 500 and scene_props.distribution != 'UNIFORM':
            return context.window_manager.invoke_props_dialog(self, width=500)
        
        return self.execute(context)


    def execute(self, context):
        obj = context.object
        scene = context.scene
        scene_props = scene.a3ob_mass_editor
        if scene_props.distribution == 'UNIFORM':
            all_closed = massutils.set_obj_vmass_density_uniform(obj, scene_props.value)
        else:
            all_closed = massutils.set_obj_vmass_density_weighted(obj, scene_props.value)

        if not all_closed:
            if obj.mode == 'OBJECT':
                self.report({'WARNING'}, "Non-closed or flat components were ignored")
            else:
                self.report({'WARNING'}, "Non-closed, partially selected or flat components were ignored")
        
        return {'FINISHED'}


class A3OB_OT_vertex_mass_clear(bpy.types.Operator):
    """Remove vertex mass data layer"""
    
    bl_idname = "a3ob.vertex_mass_clear"
    bl_label = "Clear All Masses"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH' and context.object.mode == 'OBJECT'
        
    def execute(self, context):
        obj = context.object
        massutils.clear_vmasses(obj)
        return {'FINISHED'}


class A3OB_OT_vertex_mass_selection_clear(bpy.types.Operator):
    """Clear vertex mass from selected vertices"""
    
    bl_idname = "a3ob.vertex_mass_selection_clear"
    bl_label = "Remove Mass"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return massutils.can_edit_mass(context)
        
    def execute(self, context):
        obj = context.object
        massutils.clear_selection_vmass(obj)
        return {'FINISHED'}


class A3OB_OT_vertex_mass_visualize(bpy.types.Operator):
    """Generate vertex color layer to visualize mass distribution"""
    
    bl_idname = "a3ob.vertex_mass_visualize"
    bl_label = "Visualize"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'MESH'
    
    def execute(self, context):
        obj = context.object
        scene_props = context.scene.a3ob_mass_editor
        
        massutils.visualize_mass(obj, scene_props)
        
        return {'FINISHED'}


class A3OB_OT_vertex_mass_center(bpy.types.Operator):
    """Move 3D cursor to the center of gravity"""

    bl_idname = "a3ob.vertex_mass_center"
    bl_label = "Center of Mass"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'MESH'
    
    def execute(self, context):
        obj = context.object
        center = massutils.find_center_of_gravity(obj)
        if center is not None:
            context.scene.cursor.location = obj.matrix_world @ center
    
        return {'FINISHED'}


class A3OB_PT_vertex_mass(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Object Builder"
    bl_label = "Vertex Mass Editing"
    bl_options = {'DEFAULT_CLOSED'}

    doc_url = "https://mrcmodding.gitbook.io/arma-3-object-builder/tools/vertex-mass-editing"
    
    @classmethod
    def poll(cls, context):
        return True
        
    def draw_header(self, context):
        utils.draw_panel_header(self)
        
    def draw(self, context):
        layout = self.layout
        
        scene_props = context.scene.a3ob_mass_editor
        obj = context.object
        
        layout.prop(scene_props, "enabled", text="Live Editing", toggle=True)
        row_dynamic = layout.row(align=True)
        if not massutils.can_edit_mass(context) or not scene_props.enabled:
            row_dynamic.label(text="Live Editing is unavailable")
            row_dynamic.enabled = False
        else:
            row_dynamic.prop(obj, "a3ob_selection_mass")
        
        layout.separator()
        
        col = layout.column(align=True)
        row_type = col.row(align=True)
        row_type.prop(scene_props, "value_type", expand=True)
        col.prop(scene_props, "value")

        box_op_set = col.box()
        box_op_set.operator("a3ob.vertex_mass_set", icon_value=get_icon("op_mass_set"))

        box_op_calc = col.box()
        row_distribution = box_op_calc.row(align=True)
        row_distribution.prop(scene_props, "distribution", expand=True)
        box_op_calc.operator("a3ob.vertex_mass_distribute", icon_value=get_icon("op_mass_distribute"))
        box_op_calc.operator("a3ob.vertex_mass_set_density", icon_value=get_icon("op_mass_set_density"))
        
        col.separator()
        if context.object and context.object.type == 'MESH' and context.object.mode == 'EDIT':
            col.operator("a3ob.vertex_mass_selection_clear", icon_value=get_icon("op_mass_clear"))
        else:
            col.operator("a3ob.vertex_mass_clear", icon_value=get_icon("op_mass_clear"))


class A3OB_PT_vertex_mass_analyze(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Object Builder"
    bl_label = "Analyze"
    bl_parent_id = "A3OB_PT_vertex_mass"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        return True
    
    def draw(self, context):
        layout = self.layout
        scene_props = context.scene.a3ob_mass_editor
        
        layout.label(text="Empty Color:")
        layout.prop(scene_props, "color_0", text="")
        
        layout.label(text="Color Ramp:")
        row_colors = layout.row(align=True)
        row_colors.prop(scene_props, "color_1", text="")
        row_colors.prop(scene_props, "color_2", text="")
        row_colors.prop(scene_props, "color_3", text="")
        row_colors.prop(scene_props, "color_4", text="")
        row_colors.prop(scene_props, "color_5", text="")
        
        row_stops = layout.row(align=True)
        row_stops.enabled = False

        vmass_min = scene_props.stats.mass_min
        vmass_max = scene_props.stats.mass_max

        frm = "%.0f"
        if 0 < vmass_max <= 1:
            frm = ("%." + str(ceil(abs(log10(vmass_max))) + 1) + "f")
        
        row_stops.label(text=frm % vmass_min)
        row_stops.label(text=frm % (vmass_min * 0.75 + vmass_max * 0.25))
        row_stops.label(text=frm % (vmass_min * 0.5 + vmass_max * 0.5))
        row_stops.label(text=frm % (vmass_min * 0.25 + vmass_max * 0.75))
        row_stops.label(text=frm % vmass_max)
        
        layout.prop(scene_props, "color_layer_name", text="Layer")
        row_method = layout.row(align=True)
        row_method.prop(scene_props, "method", text="Method", expand=True)
        
        layout.operator("a3ob.vertex_mass_visualize", icon_value=get_icon("op_visualize"))
        layout.operator("a3ob.vertex_mass_center", icon_value=get_icon("op_mass_center"))
        
        layout.label(text="Stats:")
        col_stats = layout.column(align=True)
        col_stats.enabled = False
        col_stats.prop(scene_props.stats, "mass_min", text="Min")
        col_stats.prop(scene_props.stats, "mass_avg", text="Average")
        col_stats.prop(scene_props.stats, "mass_max", text="Max")
        col_stats.prop(scene_props.stats, "mass_sum", text="Total")
        col_stats.prop(scene_props.stats, "count_item")


classes = (
    A3OB_OT_vertex_mass_set,
    A3OB_OT_vertex_mass_distribute,
    A3OB_OT_vertex_mass_set_density,
    A3OB_OT_vertex_mass_clear,
    A3OB_OT_vertex_mass_selection_clear,
    A3OB_OT_vertex_mass_visualize,
    A3OB_OT_vertex_mass_center,
    A3OB_PT_vertex_mass,
    A3OB_PT_vertex_mass_analyze
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    print("\t" + "UI: Vertex Mass Editing")


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    print("\t" + "UI: Vertex Mass Editing")
