import bpy
import bpy_extras

from ..io_paa import importer
from .. import utils


class A3OB_OP_import_paa(bpy.types.Operator,  bpy_extras.io_utils.ImportHelper):
    """Import Arma 3 PAA"""

    bl_idname = "a3ob.import_paa"
    bl_label = "Import Texture"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}
    filename_ext = ".paa"
    
    filter_glob: bpy.props.StringProperty(
        default = "*.paa",
        options = {'HIDDEN'}
    )
    color_space: bpy.props.EnumProperty(
        name = "Mode",
        description = "How to interpret the color data in the imported texture",
        items = (
            ('SRGB', "sRGB", "File contains a color texture (CO, CA, MC, etc.)"),
            ('DATA', "Data", "File contains non-color data (NOHQ, SMDI, AS, etc.)")
        ),
        default='SRGB'
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(self, "color_space", expand=True)
    
    def execute(self, context):
        with open(self.filepath, "rb") as file:
            img, tex = importer.import_file(self, context, file)
        
        if img is not None:
            utils.op_report(self, {'INFO'}, "Texture successfully imported as %s" % img.name)
        else:
            utils.op_report(self, {'WARNING'}, "Unsupported texture format: %s" % tex.type.name)

        return {'FINISHED'}


classes = (
    A3OB_OP_import_paa,
)


def menu_func_import(self, context):
    self.layout.operator(A3OB_OP_import_paa.bl_idname, text="Arma 3 texture (.paa)")


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    
    print("\t" + "UI: PAA Import / Export")


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    
    print("\t" + "UI: PAA Import / Export")
