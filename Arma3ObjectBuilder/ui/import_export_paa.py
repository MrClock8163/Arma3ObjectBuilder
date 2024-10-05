import bpy
import bpy_extras

from ..io import import_paa
from ..utilities import generic as utils


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

    def draw(self, context):
        pass
    
    def execute(self, context):
        with open(self.filepath, "rb") as file:
            img, tex = import_paa.import_file(self, context, file)
        
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
