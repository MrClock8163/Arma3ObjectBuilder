import bpy

from .. import utils


class A3OB_OT_paste_common_material(bpy.types.Operator):
    """Paste a common material path"""
    
    bl_label = "Paste Common Material"
    bl_idname = "a3ob.paste_common_material"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return hasattr(context, "material") and context.material
    
    def invoke(self, context, event):
        utils.load_common_data(context.scene)
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        scene_props = context.scene.a3ob_commons
        layout = self.layout
        layout.template_list("A3OB_UL_common_data_materials", "A3OB_common_materials", scene_props, "items", scene_props, "items_index", item_dyntip_propname="value")


    def execute(self, context):
        mat = context.material
        scene_props = context.scene.a3ob_commons

        if utils.is_valid_idx(scene_props.items_index, scene_props.items):
            new_item = scene_props.items[scene_props.items_index]
            mat_props = mat.a3ob_properties_material
            mat_props.material_path = new_item.value
        
        return {'FINISHED'}


class A3OB_OT_paste_common_procedural(bpy.types.Operator):
    """Paste a common procedural texture"""
    
    bl_label = "Paste Common Procedural"
    bl_idname = "a3ob.paste_common_procedural"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return hasattr(context, "material") and context.material
    
    def invoke(self, context, event):
        utils.load_common_data(context.scene)
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        scene_props = context.scene.a3ob_commons
        layout = self.layout
        layout.template_list("A3OB_UL_common_data_procedurals", "A3OB_common_procedurals", scene_props, "items", scene_props, "items_index", item_dyntip_propname="value")

    def execute(self, context):
        mat = context.material
        scene_props = context.scene.a3ob_commons

        if utils.is_valid_idx(scene_props.items_index, scene_props.items):
            new_item = scene_props.items[scene_props.items_index]
            mat_props = mat.a3ob_properties_material
            mat_props.color_raw = new_item.value
        
        return {'FINISHED'}


class A3OB_UL_common_procedurals(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.label(text=item.name)


class A3OB_PT_material(bpy.types.Panel):
    bl_region_type = 'WINDOW'
    bl_space_type = 'PROPERTIES'
    bl_label = "Object Builder: Material Properties"
    bl_context = "material"

    doc_url = "https://mrcmodding.gitbook.io/arma-3-object-builder/properties/material"
    
    @classmethod
    def poll(cls, context):
        return hasattr(context, "material") and context.material
        
    def draw_header(self, context):
        utils.draw_panel_header(self)
        
    def draw(self, context):
        material = context.material
        material_props = material.a3ob_properties_material
        
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        row = layout.row()
        row.prop(material_props, "texture_type", expand=True)
        layout.separator()
        
        texture_type = material_props.texture_type
        if texture_type == 'TEX':
            layout.prop(material_props, "texture_path", text="", icon='TEXTURE')
        elif texture_type == 'COLOR':
            row_color = layout.row(align=True)
            row_color.prop(material_props, "color_value", icon='COLOR')
            row_color.prop(material_props, "color_type", text="")
        elif texture_type == 'CUSTOM':
            row_raw = layout.row(align=True)
            row_raw.operator("a3ob.paste_common_procedural", text="", icon='PASTEDOWN')
            row_raw.prop(material_props, "color_raw", text="", icon='TEXT')
        
        row_material = layout.row(align=True)
        row_material.operator("a3ob.paste_common_material", text="", icon='PASTEDOWN')
        row_material.prop(material_props, "material_path", text="", icon='MATERIAL')


classes = (
    A3OB_OT_paste_common_material,
    A3OB_OT_paste_common_procedural,
    A3OB_UL_common_procedurals,
    A3OB_PT_material,
)


def register_ui():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_ui():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
