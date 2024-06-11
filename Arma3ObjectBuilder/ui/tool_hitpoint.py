import bpy

from ..utilities import generic as utils
from ..utilities import clouds as cloudutils


class A3OB_OT_hitpoints_generate(bpy.types.Operator):
    """Create hit points cloud from shape"""
    
    bl_idname = "a3ob.hitpoints_generate"
    bl_label = "Generate Hit Point Cloud"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        scene_props = context.scene.a3ob_hitpoint_generator
        return scene_props.source and (scene_props.source != scene_props.target) and scene_props.source.type == 'MESH' and (not scene_props.target or scene_props.target.type == 'MESH')
        
    def execute(self, context):        
        cloudutils.generate_hitpoints(self, context)
        return {'FINISHED'}


class A3OB_PT_hitpoints(bpy.types.Panel):   
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Object Builder"
    bl_label = "Hit Point Cloud"
    bl_options = {'DEFAULT_CLOSED'}

    doc_url = "https://mrcmodding.gitbook.io/arma-3-object-builder/tools/hit-point-cloud"
    
    @classmethod
    def poll(cls, context):
        return True
        
    def draw_header(self, context):
        utils.draw_panel_header(self)
        
    def draw(self, context):
        scene_props = context.scene.a3ob_hitpoint_generator
        scene = context.scene
        
        # SUPER hacky way to get rid of the object if it's only retained in memory because of this property
        if scene_props.source or scene_props.target:
            cloudutils.validate_references(scene_props.source, scene_props.target)
        
        layout = self.layout
        
        layout.prop_search(scene_props, "source", scene, "objects")
        layout.prop_search(scene_props, "target", scene, "objects")
        
        col = layout.column(align=True)
        col.prop(scene_props,"spacing")
        
        col_bevel = layout.column(align=True, heading="Bevel:")
        col_bevel.prop(scene_props, "bevel_offset", text="Offset")
        col_bevel.prop(scene_props, "bevel_segments", text="Segments")
        col_bevel.separator()
        row_triangulate = col_bevel.row(align=True)
        row_triangulate.use_property_split = True
        row_triangulate.use_property_decorate = False
        row_triangulate.prop(scene_props, "triangulate", text="Triangulate", expand=True)
        
        col_selection = layout.column(align=True, heading="Selection:")
        col_selection.prop(scene_props, "selection", text="", icon='MESH_DATA')
        
        layout.operator("a3ob.hitpoints_generate", text="Generate", icon_value=utils.get_icon("op_hitpoints_generate"))


classes = (
    A3OB_OT_hitpoints_generate,
    A3OB_PT_hitpoints
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    print("\t" + "UI: Hit Point Cloud")


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    print("\t" + "UI: Hit Point Cloud")
