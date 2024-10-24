import bpy
import bpy_extras

from ..io import import_asc, export_asc
from ..utilities import generic as utils


class A3OB_OP_import_asc(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """Import Esri ASCII grid as DTM"""
    
    bl_idname = "a3ob.import_asc"
    bl_label = "Import ASC"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}
    filename_ext = ".asc"
    
    filter_glob: bpy.props.StringProperty(
        default = "*.asc",
        options = {'HIDDEN'}
    )
    hscale: bpy.props.FloatProperty(
        name = "Horizontal Scale",
        default = 1.0,
        min = -0.001,
        max = 1000
    )
    vscale: bpy.props.FloatProperty(
        name = "Vertical Scale",
        default = 1.0,
        min = -0.001,
        max = 1000
    )

    def draw(self, context):
        pass
    
    def execute(self, context):        
        with open(self.filepath) as file:
            import_asc.read_file(self, context, file)
            utils.op_report(self, {'INFO'}, "Successfully imported DTM")
        
        return {'FINISHED'}


class A3OB_PT_import_asc_main(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Main"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'HIDE_HEADER'}
    
    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        
        return operator.bl_idname == "A3OB_OT_import_asc"
    
    def draw(self, context):
        layout = self.layout
        sfile = context.space_data
        operator = sfile.active_operator

        col = layout.column(align=True, heading="Scale:")
        col.prop(operator, "hscale", text="Horizontal")
        col.prop(operator, "vscale", text="Vertical")


class A3OB_OP_export_asc(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    """Export DTM as Esri ASCII grid"""
    bl_idname = "a3ob.export_asc"
    bl_label = "Export ASC"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}
    filename_ext = ".asc"
    
    filter_glob: bpy.props.StringProperty(
        default = "*.asc",
        options = {'HIDDEN'}
    )
    apply_modifiers: bpy.props.BoolProperty(
        name = "Apply Modifiers",
        description = "Apply the assigned modifiers to the DTM object during export",
        default = True
    )
    dimensions: bpy.props.EnumProperty(
        name = "Dimensions",
        description = "Raster dimensions (the number of vertices must match the calulcated rows x columns size)",
        items = (
            ("SQUARE", "1:1", "Calculate dimensions from 1:1 rows-columns ratio"),
            ("LANDSCAPE", "1:2", "Calculate dimensions from 1:2 rows-columns ratio"),
            ("PORTRAIT", "2:1", "Calculate dimensions from 2:1 rows-columns ratio"),
            ("CUSTOM", "Custom", "Specify custom dimensions")
        ),
        default = 'SQUARE'
    )
    rows: bpy.props.IntProperty(
        name = "Rows",
        default = 1,
        min = 1
    )
    columns: bpy.props.IntProperty(
        name = "Columns",
        default = 1,
        min = 1
    )
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and len(obj.data.vertices) > 0
    
    def draw(self, context):
        pass
    
    def execute(self, context):        
        obj = context.active_object
        
        with utils.ExportFileHandler(self.filepath, "wt") as file:
            export_asc.write_file(self, context, file, obj)
            utils.op_report(self, {'INFO'}, "Successfuly exported DTM")
        
        return {'FINISHED'}


class A3OB_PT_export_asc_main(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Main"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'HIDE_HEADER'}
    
    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        
        return operator.bl_idname == "A3OB_OT_export_asc"
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        sfile = context.space_data
        operator = sfile.active_operator
        
        layout.prop(operator, "apply_modifiers")


class A3OB_PT_export_asc_dimensions(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Dimensions"
    bl_parent_id = "FILE_PT_operator"
    
    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        
        return operator.bl_idname == "A3OB_OT_export_asc"
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        sfile = context.space_data
        operator = sfile.active_operator
        
        layout.prop(operator, "dimensions")
        if operator.dimensions == 'CUSTOM':
            layout.prop(operator, "rows")
            layout.prop(operator, "columns")


classes = (
    A3OB_OP_import_asc,
    A3OB_PT_import_asc_main,
    A3OB_OP_export_asc,
    A3OB_PT_export_asc_main,
    A3OB_PT_export_asc_dimensions
)

if bpy.app.version >= (4, 1, 0):
    class A3OB_FH_import_asc(bpy.types.FileHandler):
        bl_label = "File handler for ASC import"
        bl_import_operator = "a3ob.import_asc"
        bl_file_extensions = ".asc"
    
        @classmethod
        def poll_drop(cls, context):
            return context.area and context.area.type == 'VIEW_3D'

    classes = (*classes, A3OB_FH_import_asc)


def menu_func_import(self, context):
    self.layout.operator(A3OB_OP_import_asc.bl_idname, text="Esri Grid ASCII (.asc)")


def menu_func_export(self, context):
    self.layout.operator(A3OB_OP_export_asc.bl_idname, text="Esri Grid ASCII (.asc)")


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    
    print("\t" + "UI: ASC Import / Export")


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    
    print("\t" + "UI: ASC Import / Export")
