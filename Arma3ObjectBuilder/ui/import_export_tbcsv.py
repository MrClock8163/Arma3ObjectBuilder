import bpy
import bpy_extras

from ..tbcsv import importer, exporter
from ..utilities import generic as utils


class A3OB_OP_import_tbcsv(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """Import Arma 3 map object positions"""
    
    bl_idname = "a3ob.import_tbcsv"
    bl_label = "Import Positions"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}
    filename_ext = ".txt"
    
    filter_glob: bpy.props.StringProperty(
        default = "*.txt",
        options = {'HIDDEN'}
    )
    name_source: bpy.props.EnumProperty(
        name = "Name Source",
        description = "Name to match to the imported object names",
        items = (
            ('OBJECT', "Object", "Import name is the object name without the automatic index suffix (eg.: .001)"),
            ('PROPERTY', "Property", "Import name is taken from custom string property")
        ),
        default = 'OBJECT'
    )
    name_prop: bpy.props.StringProperty(
        name = "Name Property",
        description = "Name of the custom string property containing the import name"
    )
    cleanup_templates: bpy.props.BoolProperty(
        name = "Cleanup Templates",
        description = "Remove template objects after the import process finished",
        default = True
    )
    coord_shift: bpy.props.FloatVectorProperty(
        name = "Shift",
        description = "Shift imported coordinate to recenter them in the scene",
        subtype = 'XYZ',
        size = 2,
        default = (-200000, 0)
    )
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(self, "name_source")
        if self.name_source == 'PROPERTY':
            layout.prop(self, "name_prop")
        
        layout.prop(self, "cleanup_templates")
        layout.prop(self, "coord_shift")

    def execute(self, context):
        with open(self.filepath, "rt") as file:
            count_read, count_found = importer.read_file(self, context, file)

        if count_found > 0:
            utils.op_report(self, {'INFO'}, "Successfully imported %d/%d object positions (check the logs in the system console)" % (count_found, count_read))
        else:
            utils.op_report(self, {'WARNING'}, "Could not spawn any objects, template objects were not found (check the logs in the system console)")

        return {'FINISHED'}


class A3OB_OP_export_tbcsv(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    """Export Arma 3 map object positions"""
    
    bl_idname = "a3ob.export_tbcsv"
    bl_label = "Export Positions"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}
    filename_ext = ".txt"
    
    filter_glob: bpy.props.StringProperty(
        default = "*.txt",
        options = {'HIDDEN'}
    )
    collection: bpy.props.StringProperty(
        name = "Source Collection",
        description = "Export only objects from this collection (and its children)",
        default = "",
    )
    targets: bpy.props.EnumProperty(
        name = "Source",
        description = "Scope of objects to set positions on (NOT APPLICABLE TO COLLECTION EXPORTS!)",
        items = (
            ('ALL', "All", "All objects in the project"),
            ('SCENE', "Scene", "Objects in active scene"),
            ('SELECTION', "Selection", "Objects in active selection"),
        ),
        default = 'SCENE'
    )
    only_lods: bpy.props.BoolProperty(
        name = "Only LOD Objects",
        description = "Inlcude only those meshes that are marked as LOD objects"
    )
    name_source: bpy.props.EnumProperty(
        name = "Name Source",
        description = "Method to determine under what name to export the objects",
        items = (
            ('COLLECTION', "Collection", "Export objects with the name of the containing collection (ONLY AVAILABLE ON COLLECTION EXPORTS!)"),
            ('OBJECT', "Object", "Export name is the object name without the automatic index suffix (eg.: .001)"),
            ('PROPERTY', "Property", "Export name is taken from custom string property")
        ),
        default = 'OBJECT'
    )
    name_prop: bpy.props.StringProperty(
        name = "Name Property",
        description = "Name of the custom string property containing the export name"
    )
    coord_shift: bpy.props.FloatVectorProperty(
        name = "Shift",
        description = "Shift exported coordinates",
        subtype = 'XYZ',
        size = 2,
        default = (200000, 0)
    )
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        col.prop(self, "targets", expand=True)

        layout.prop(self, "only_lods")
        layout.prop(self, "name_source")
        if self.name_source == 'PROPERTY':
            layout.prop(self, "name_prop")
            
        layout.prop(self, "coord_shift")

    def execute(self, context):
        if not self.collection and self.name_source == 'COLLECTION':
            utils.op_report(self, {'ERROR'}, "Collection name can only be used when exporting a collection")
            return {'FINISHED'}
        
        with utils.ExportFileHandler(self.filepath, "wt") as file:
            count = exporter.write_file(self, context, file)

        if count > 0:
            utils.op_report(self, {'INFO'}, "Successfully exported %d object positions (check the logs in the system console)" % count)
        else:
            utils.op_report(self, {'WARNING'}, "Could not export any object positions (check the logs in the system console)")

        return {'FINISHED'}


classes = (
    A3OB_OP_import_tbcsv,
    A3OB_OP_export_tbcsv
)


if bpy.app.version >= (4, 1, 0):
    class A3OB_FH_tbcsv(bpy.types.FileHandler):
        bl_label = "Arma 3 map objects list"
        bl_import_operator = "a3ob.import_tbcsv"
        bl_export_operator = "a3ob.export_tbcsv"
        bl_file_extensions = ".txt"
    
        @classmethod
        def poll_drop(cls, context):
            return context.area and context.area.type == 'VIEW_3D'

    classes = (*classes, A3OB_FH_tbcsv)


def menu_func_import(self, context):
    self.layout.operator(A3OB_OP_import_tbcsv.bl_idname, text="Arma 3 map objects (.txt)")


def menu_func_export(self, context):
    self.layout.operator(A3OB_OP_export_tbcsv.bl_idname, text="Arma 3 map objects (.txt)")


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    
    print("\t" + "UI: TB TXT Import / Export")


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    
    print("\t" + "UI: TB TXT Import / Export")
