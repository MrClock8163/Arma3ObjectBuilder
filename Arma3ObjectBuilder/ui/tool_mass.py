import bpy

from ..utilities import generic as utils
from ..utilities import masses as massutils


class A3OB_OT_vertex_mass_set(bpy.types.Operator):
    """Set same mass on all selected vertices"""
    
    bl_idname = "a3ob.vertex_mass_set"
    bl_label = "Set Mass On Each"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return massutils.can_edit_mass(context) and context.scene.a3ob_mass_editor.source == 'MASS'
        
    def execute(self, context):
        obj = context.object
        scene = context.scene
        massutils.set_selection_mass_each(obj, scene.a3ob_mass_editor.mass)
        return {'FINISHED'}


class A3OB_OT_vertex_mass_distribute(bpy.types.Operator):
    """Distribute mass equally to selected vertices"""
    
    bl_idname = "a3ob.vertex_mass_distribute"
    bl_label = "Distribute Mass"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return massutils.can_edit_mass(context) and context.scene.a3ob_mass_editor.source == 'MASS'
        
    def execute(self, context):
        obj = context.object
        scene = context.scene
        massutils.set_selection_mass_distribute(obj, scene.a3ob_mass_editor.mass)
        return {'FINISHED'}


class A3OB_OT_vertex_mass_set_density(bpy.types.Operator):
    """Calculate mass distribution from volumetric density (operates on the entire mesh)"""
    
    bl_idname = "a3ob.vertex_mass_set_density"
    bl_label = "Mass From Density"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return massutils.can_edit_mass(context) and context.scene.a3ob_mass_editor.source == 'DENSITY'
        
    def execute(self, context):
        obj = context.object
        scene = context.scene
        all_closed = massutils.set_selection_mass_density(obj, scene.a3ob_mass_editor.density)
        if not all_closed:
            self.report({'WARNING'}, "Non-closed components were ignored")
        
        return {'FINISHED'}


class A3OB_OT_vertex_mass_clear(bpy.types.Operator):
    """Remove vertex mass data layer"""
    
    bl_idname = "a3ob.vertex_mass_clear"
    bl_label = "Clear Masses"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return massutils.can_edit_mass(context)
        
    def execute(self, context):
        obj = context.object
        massutils.clear_selection_masses(obj)
        return {'FINISHED'}


class A3OB_OT_vertex_mass_visualize(bpy.types.Operator):
    """Generate vertex color layer to visualize mass distribution"""
    
    bl_idname = "a3ob.vertex_mass_visualize"
    bl_label = "Visualize"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return massutils.can_edit_mass(context)
    
    def execute(self, context):
        obj = context.object
        scene_props = context.scene.a3ob_mass_editor
        
        massutils.visualize_mass(obj, scene_props)
        
        return {'FINISHED'}


class A3OB_OT_vertex_mass_center(bpy.types.Operator):
    """Move 3D cursor to the center of gravity"""

    bl_idname = "a3ob.vertex_mass_center"
    bl_label = "Center Of Mass"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return massutils.can_edit_mass(context)
    
    def execute(self, context):
        obj = context.object
        center = massutils.find_center_of_gravity(obj)

        context.scene.cursor.location = center
    
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
        layout.label(text="Overwrite Mass:")
        layout.prop(scene_props, "source", expand=True)
        
        col = layout.column(align=True)
        if scene_props.source == 'MASS':
            col.prop(scene_props, "mass")
            col.operator("a3ob.vertex_mass_set", icon_value=utils.get_icon("op_mass_set"))
            col.operator("a3ob.vertex_mass_distribute", icon_value=utils.get_icon("op_mass_distribute"))
        elif scene_props.source == 'DENSITY':
            col.prop(scene_props, "density")
            col.operator("a3ob.vertex_mass_set_density", icon_value=utils.get_icon("op_mass_set_density"))
        
        col.separator()
        col.operator("a3ob.vertex_mass_clear", icon_value=utils.get_icon("op_mass_clear"))


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
        row_stops.label(text="%.0f" % scene_props.stats.mass_min)
        row_stops.label(text="%.0f" % (scene_props.stats.mass_min * 0.75 + scene_props.stats.mass_max * 0.25))
        row_stops.label(text="%.0f" % (scene_props.stats.mass_min * 0.5 + scene_props.stats.mass_max * 0.5))
        row_stops.label(text="%.0f" % (scene_props.stats.mass_min * 0.25 + scene_props.stats.mass_max * 0.75))
        row_stops.label(text="%.0f" % scene_props.stats.mass_max)
        
        layout.prop(scene_props, "color_layer_name", text="Layer")
        row_method = layout.row(align=True)
        row_method.prop(scene_props, "method", text="Method", expand=True)
        
        layout.operator("a3ob.vertex_mass_visualize", icon_value=utils.get_icon("op_visualize"))
        layout.operator("a3ob.vertex_mass_center", icon_value=utils.get_icon("op_mass_center"))
        
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
