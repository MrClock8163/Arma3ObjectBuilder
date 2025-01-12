import os

import bpy

from .. import get_prefs, get_icon
from .. import utils
from ..utilities import materials as matutils


class A3OB_OT_materials_templates_generate(bpy.types.Operator):
    """Generate RVMAT from selected template"""

    bl_idname = "a3ob.materials_templates_generate"
    bl_label = "Generate"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        scene_props = context.scene.a3ob_materials
        return utils.is_valid_idx(scene_props.templates_index, scene_props.templates)

    def execute(self, context):
        scene_props = context.scene.a3ob_materials

        if os.path.isfile(os.path.join(scene_props.folder, scene_props.basename + ".rvmat")) and not scene_props.overwrite_existing:
            self.report({'ERROR'}, "RVMAT already exists")
            return {'FINISHED'}

        path = scene_props.templates[scene_props.templates_index].path
        template = matutils.RVMATTemplate(path)
        success = template.write_output(get_prefs().project_root, scene_props.folder, scene_props.basename, scene_props.check_files_exist)

        if success:
            self.report({'INFO'}, "Successfully generated %s.rvmat" % scene_props.basename)
        else:
            self.report({'ERROR'}, "RVMAT could not be generated")

        return {'FINISHED'}


class A3OB_OT_materials_templates_reload(bpy.types.Operator):
    """Load/Reload material templates"""
    
    bl_idname = "a3ob.materials_templates_reload"
    bl_label = "Refresh Templates"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        utils.load_common_data(context.scene)
        scene_props_common = context.scene.a3ob_commons
        scene_props_mats = context.scene.a3ob_materials

        scene_props_mats.templates.clear()
        for item in scene_props_common.items:
            if item.type != 'RVMAT_TEMPLATES':
                continue

            new_item = scene_props_mats.templates.add()
            new_item.name = item.name
            new_item.path = item.value
            
        return {'FINISHED'}


class A3OB_UL_materials_templates(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.label(text=item.name, icon='TEXT')


class A3OB_PT_materials(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Object Builder"
    bl_label = "Materials"
    bl_options = {'DEFAULT_CLOSED'}

    doc_url = "https://mrcmodding.gitbook.io/arma-3-object-builder/tools/materials"
    
    def draw_header(self, context):
        utils.draw_panel_header(self)

    def draw(self, context):
        pass


class A3OB_PT_materials_colors(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Object Builder"
    bl_label = "Colors"
    bl_parent_id = "A3OB_PT_materials"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene_props = context.scene.a3ob_colors
        
        layout.label(text="Input:")
        
        row_input_type = layout.row(align=True)
        row_input_type.prop(scene_props, "input_type", expand=True)
        
        col_input = layout.column(align=True)
        if scene_props.input_type == 'S8':
            col_input.prop(scene_props, "input_red_int")
            col_input.prop(scene_props, "input_green_int")
            col_input.prop(scene_props, "input_blue_int")
        else:
            col_input.prop(scene_props, "input_red_float")
            col_input.prop(scene_props, "input_green_float")
            col_input.prop(scene_props, "input_blue_float")
            
        layout.label(text="Output:")
            
        row_output_type = layout.row(align=True)
        row_output_type.prop(scene_props, "output_type", expand=True)
        
        col_output = layout.column(align=True)
        
        if scene_props.output_type == 'S8':
            col_output.prop(scene_props, "output_red_int")
            col_output.prop(scene_props, "output_green_int")
            col_output.prop(scene_props, "output_blue_int")
        else:
            col_output.prop(scene_props, "output_red_float")
            col_output.prop(scene_props, "output_green_float")
            col_output.prop(scene_props, "output_blue_float")
        
        if scene_props.output_type in {'S8', 'S'}:
            layout.prop(scene_props, "output_srgb", text="")
        else:
            layout.prop(scene_props, "output_linear", text="")


class A3OB_PT_materials_templates(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Object Builder"
    bl_label = "Templates"
    bl_parent_id = "A3OB_PT_materials"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene_props = context.scene.a3ob_materials

        col_list = layout.column(align=True)
        col_list.template_list("A3OB_UL_materials_templates", "A3OB_materials_templates", scene_props, "templates", scene_props, "templates_index", item_dyntip_propname="path")
        col_list.operator("a3ob.materials_templates_reload", icon_value=get_icon("op_refresh"))

        layout.prop(scene_props, "folder")
        layout.prop(scene_props, "basename")
        layout.prop(scene_props, "check_files_exist")
        layout.prop(scene_props, "overwrite_existing")

        layout.operator("a3ob.materials_templates_generate", icon='EXPORT')


classes = (
    A3OB_OT_materials_templates_generate,
    A3OB_OT_materials_templates_reload,
    A3OB_UL_materials_templates,
    A3OB_PT_materials,
    A3OB_PT_materials_colors,
    A3OB_PT_materials_templates
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    print("\t" + "UI: Materials")


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    print("\t" + "UI: Materials")
