import bpy
import bpy_extras
from bpy.app.handlers import persistent

from . import props_object, props_scene, props_mat
from . import ui_object, ui_mat
from . import importer, exporter
from .. import get_prefs
from .. import utils
from .. import utils_io


class A3OB_OT_import_p3d(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """Import Arma 3 MLOD P3D"""
    
    bl_idname = "a3ob.import_p3d"
    bl_label = "Import P3D"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}
    filename_ext = ".p3d"
    
    filter_glob: bpy.props.StringProperty(
        default = "*.p3d",
        options = {'HIDDEN'}
    )
    absolute_paths: bpy.props.BoolProperty(
        name = "Absolute Paths",
        description = "Try to restore absolute paths by appending the read path to the project root",
        default = True
    )
    enclose: bpy.props.BoolProperty(
        name = "Enclose In Collection",
        description = "Enclose LODs in collection named after the original file",
        default = True
    )
    groupby: bpy.props.EnumProperty(
        name = "Group By",
        description = "Include LODs in collections according to the selection",
        default = 'TYPE',
        items = (
            ('NONE', "None", "Import LODs without collections"),
            ('TYPE', "Type", "Group LODs by logical type (eg.: visuals, geometries, etc.)"),
            # ('CONTEXT', "Context", "Group LODs by use context (eg.: 1st person, 3rd person, etc.)")
        )
    )
    additional_data_allowed: bpy.props.BoolProperty(
        name = "Allow Additinal Data",
        description = "Import data in addition to the LOD geometries themselves",
        default = True
    )
    additional_data: bpy.props.EnumProperty(
        name = "Data",
        options = {'ENUM_FLAG'},
        items = (
            ('NORMALS', "Custom Normals", "WARNING: may not work properly on certain files"),
            ('FLAGS', "Flags", "Vertex and face flags"),
            ('PROPS', "Named Properties", ""),
            ('MASS', "Vertex Mass", "Mass of individual vertices (in Geometry LODs)"),
            ('SELECTIONS', "Selections", ""),
            ('UV', "UV Sets", ""),
            ('MATERIALS', "Materials", "")
        ),
        description = "Data to import in addition to the LOD meshes themselves",
        default = {'NORMALS', 'PROPS', 'MASS', 'SELECTIONS', 'UV', 'MATERIALS'}
    )
    validate_meshes: bpy.props.BoolProperty(
        name = "Validate Meshes",
        description = "Validate LOD meshes after creation, and clean up duplicate faces and other problematic geometry"
    )
    proxy_action: bpy.props.EnumProperty(
        name = "Proxy Action",
        description = "Post-import handling of proxies",
        items = (
            ('NOTHING', "Nothing", "Leave proxies embedded into the LOD meshes\n(the actual file paths will be lost because of Blender limitations)"),
            ('SEPARATE', "Separate", "Separate the proxies into proxy objects parented to the LOD mesh they belong to"),
            ('CLEAR', "Purge", "Remove all proxies")
        ),
        default = 'SEPARATE'
    )
    first_lod_only: bpy.props.BoolProperty(
        name = "First LOD Only",
        description = "Import only the first LOD found in the file"
    )
    translate_selections: bpy.props.BoolProperty(
        name = "Translate Selections",
        description = "Try to translate czech selection names to english"
    )
    cleanup_empty_selections: bpy.props.BoolProperty(
        name = "Cleanup Selections",
        description = "Remove empty selections\nIMPORTANT: certain model.cfg animations may depend on even empty selections in order to display correctly"
    )
    sections: bpy.props.EnumProperty(
        name = "Sections",
        items = (
            ('PRESERVE', "Preserve", "Preserve model sections as they are"),
            ('MERGE', "Merge", "Merge sections with identical texture-material pair")
        ),
        default = 'PRESERVE'
    )
    
    def draw(self, context):
        pass
    
    def execute(self, context):        
        with open(self.filepath, "rb") as file:
            lod_objects = importer.read_file(self, context, file)
            utils.op_report(self, {'INFO'}, "Successfully imported %d LODs (check the logs in the system console)" % len(lod_objects))
        
        return {'FINISHED'}


class A3OB_PT_import_p3d_main(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Main"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'HIDE_HEADER'}
    
    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        
        return operator.bl_idname == "A3OB_OT_import_p3d"
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        sfile = context.space_data
        operator = sfile.active_operator
        
        layout.prop(operator, "first_lod_only")
        layout.prop(operator, "validate_meshes")


class A3OB_PT_import_p3d_collections(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Collections"
    bl_parent_id = "FILE_PT_operator"
    
    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        
        return operator.bl_idname == "A3OB_OT_import_p3d"
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        sfile = context.space_data
        operator = sfile.active_operator
        
        layout.prop(operator, "enclose")
        layout.prop(operator, "groupby")


class A3OB_PT_import_p3d_data(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Data"
    bl_parent_id = "FILE_PT_operator"
    
    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        
        return operator.bl_idname == "A3OB_OT_import_p3d"
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        sfile = context.space_data
        operator = sfile.active_operator
        
        layout.prop(operator, "absolute_paths")
        col = layout.column(heading="Additional data")
        col.prop(operator, "additional_data_allowed", text="")
        
        col_enum = col.column()
        col_enum.enabled = operator.additional_data_allowed
        col_enum.prop(operator, "additional_data", text=" ") # text=" " otherwise the enum is stretched accross the panel
        row_sections = layout.row(align=True)
        row_sections.prop(operator, "sections", expand=True)
        if not operator.additional_data_allowed or 'MATERIALS' not in operator.additional_data:
            row_sections.enabled = False


class A3OB_PT_import_p3d_post(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Postprocess"
    bl_parent_id = "FILE_PT_operator"
    
    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        
        return operator.bl_idname == "A3OB_OT_import_p3d"
        
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        sfile = context.space_data
        operator = sfile.active_operator

        
        if 'SELECTIONS' not in operator.additional_data or not operator.additional_data_allowed:
            layout.alert = True
            layout.label(text="Enable selection data")
            col = layout.column(align=True)

            col.prop(operator, "translate_selections")
            col.prop(operator, "cleanup_empty_selections")
            col.separator()
            col.prop(operator, "proxy_action", expand=True)
            col.enabled = False
        else:
            col = layout.column(align=True)

            col.prop(operator, "translate_selections")
            col.prop(operator, "cleanup_empty_selections")
            col.separator()
            col.prop(operator, "proxy_action", expand=True)


class A3OB_OT_export_p3d(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    """Export to Arma 3 MLOD P3D"""
    
    bl_idname = "a3ob.export_p3d"
    bl_label = "Export P3D"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}
    filename_ext = ".p3d"
    
    filter_glob: bpy.props.StringProperty(
        default = "*.p3d",
        options = {'HIDDEN'}
    )
    relative_paths: bpy.props.BoolProperty(
        name = "Relative Paths",
        description = "Try to make file paths relative to the project root (at the very least, the drive letter is stripped)",
        default = True
    )
    preserve_normals: bpy.props.BoolProperty(
        name = "Custom Normals",
        description = "Export the custom split edge normals",
        default = True
    )
    validate_meshes: bpy.props.BoolProperty(
        name = "Validate Meshes",
        description = "Clean up invalid geometry before export (eg.: duplicate faces, edges, vertices)"
    )
    use_selection: bpy.props.BoolProperty(
        name = "Selected Only",
        description = "Export only selected objects"
    )
    visible_only: bpy.props.BoolProperty(
        name = "Visible",
        description = "Only export visible LOD objects (necessary, only shown for indication)",
        default = True
    )
    apply_transforms: bpy.props.BoolProperty(
        name = "Apply Transforms",
        description = "Apply space transformations to the exported model data",
        default = True
    )
    apply_modifiers: bpy.props.BoolProperty(
        name = "Apply Modifiers",
        description = "Apply the assigned modifiers to the LOD objects during export",
        default = True
    )
    sort_sections: bpy.props.BoolProperty(
        name = "Sort Sections",
        description = "Sort faces in LODs by the assigned materials (prevents fragmentation in the face list, and allows proper sorting of alpha faces)",
        default = True
    )
    lod_collisions: bpy.props.EnumProperty(
        name = "Collisions",
        description = "Action to take when detecting LODs with identical signatures",
        items = (
            ('IGNORE', "Ignore", "Ignore and proceed with the export"),
            ('SKIP', "Skip", "Skip LODs with signatures that have already been exported"),
            ('FAIL', "Fail", "Fail the export process")
        ),
        default = 'FAIL'
    )
    validate_lods: bpy.props.BoolProperty(
        name = "Validate LODs",
        description = "Validate LOD objects, and skip the export of invalid ones"
    )
    validate_lods_warning_errors: bpy.props.BoolProperty(
        name = "Warnings Are Errors",
        description = "Treat warnings as errors",
        default = True
    )
    renumber_components: bpy.props.BoolProperty(
        name = "Renumber Components",
        description = "Renumber the \"component##\" selections to make sure they are unique (only use if necessary\neg.: geometry type LODs have sub-objects)"
    )
    force_lowercase: bpy.props.BoolProperty(
        name = "Force Lowercase",
        description = "Export all paths and selection names as lowercase",
        default = True
    )
    translate_selections: bpy.props.BoolProperty(
        name = "Translate Selections",
        description = "Try to translate english selection names to czech"
    )
    generate_components: bpy.props.BoolProperty(
        name = "Generate Components",
        description = "Generate Component## selections if none are already defined",
        default = True
    )

    def draw(self, context):
        pass
    
    def execute(self, context):        
        if not exporter.can_export(self, context):
            utils.op_report(self, {'ERROR'}, "There are no LODs to export")
            return {'FINISHED'}
        
        temp_collection = exporter.create_temp_collection(context)

        with utils_io.ExportFileHandler(self.filepath, "wb") as file:
            # The export needs to be put inside a try-catch block in order to do the temporary object cleanup.
            try:
                lod_count, exported_count = exporter.write_file(self, context, file, temp_collection)

                if lod_count == exported_count:
                    utils.op_report(self, {'INFO'}, "Successfully exported all %d LODs (check the logs in the system console)" % exported_count)
                else:
                    utils.op_report(self, {'WARNING'}, "Only exported %d/%d LODs (check the logs in the system console)" % (exported_count, lod_count))

            finally:
                if not get_prefs().preserve_preprocessed_lods:
                    exporter.cleanup_temp_collection(temp_collection) 
        
        return {'FINISHED'}


class A3OB_PT_export_p3d_main(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Include"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'HIDE_HEADER'}
    
    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        
        return operator.bl_idname == "A3OB_OT_export_p3d"
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "relative_paths")


class A3OB_PT_export_p3d_include(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Include"
    bl_parent_id = "FILE_PT_operator"
    
    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        
        return operator.bl_idname == "A3OB_OT_export_p3d"
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        sfile = context.space_data
        operator = sfile.active_operator
        
        col = layout.column(heading="Limit To", align=True)
        col.prop(operator, "use_selection")
        row_visible = col.row(align=True)
        row_visible.prop(operator, "visible_only")
        row_visible.enabled = False


class A3OB_PT_export_p3d_meshes(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Mesh Data"
    bl_parent_id = "FILE_PT_operator"
    
    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        
        return operator.bl_idname == "A3OB_OT_export_p3d"
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        sfile = context.space_data
        operator = sfile.active_operator
        
        col = layout.column(align=True)
        col.prop(operator, "validate_meshes")
        col.prop(operator, "apply_modifiers")
        col.prop(operator, "apply_transforms")
        col.prop(operator, "preserve_normals")
        col.prop(operator, "sort_sections")
        col.prop(operator, "generate_components")


class A3OB_PT_export_p3d_validate(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "LODs"
    bl_parent_id = "FILE_PT_operator"
    
    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        
        return operator.bl_idname == "A3OB_OT_export_p3d"
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        sfile = context.space_data
        operator = sfile.active_operator
        
        col = layout.column(align=True)
        col.prop(operator, "lod_collisions")
        col.prop(operator, "validate_lods")
        row = col.row(align=True)
        row.prop(operator, "validate_lods_warning_errors")
        row.enabled = operator.validate_lods


class A3OB_PT_export_p3d_post(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Postprocess"
    bl_parent_id = "FILE_PT_operator"
    
    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        
        return operator.bl_idname == "A3OB_OT_export_p3d"
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        sfile = context.space_data
        operator = sfile.active_operator
        col = layout.column(align=True)
        col.prop(operator, "renumber_components")
        col.prop(operator, "force_lowercase")
        col.prop(operator, "translate_selections")


classes = (
    A3OB_OT_import_p3d,
    A3OB_PT_import_p3d_main,
    A3OB_PT_import_p3d_collections,
    A3OB_PT_import_p3d_data,
    A3OB_PT_import_p3d_post,
    A3OB_OT_export_p3d,
    A3OB_PT_export_p3d_main,
    A3OB_PT_export_p3d_include,
    A3OB_PT_export_p3d_meshes,
    A3OB_PT_export_p3d_validate,
    A3OB_PT_export_p3d_post
)


if bpy.app.version >= (4, 1, 0):
    class A3OB_FH_import_p3d(bpy.types.FileHandler):
        bl_label = "File handler for P3D import"
        bl_import_operator = "a3ob.import_p3d"
        bl_file_extensions = ".p3d"
    
        @classmethod
        def poll_drop(cls, context):
            return context.area and context.area.type == 'VIEW_3D'

    classes = (*classes, A3OB_FH_import_p3d)


def menu_func_import(self, context):
    self.layout.operator(A3OB_OT_import_p3d.bl_idname, text="Arma 3 model (.p3d)")


def menu_func_export(self, context):
    self.layout.operator(A3OB_OT_export_p3d.bl_idname, text="Arma 3 model (.p3d)")


@persistent
def depsgraph_update_post_handler(scene, depsgraph):  
    scene_props = scene.a3ob_proxy_access

    obj = None
    try:
        obj = bpy.context.object
    except:
        pass
    
    if not obj or obj.type != 'MESH' or not obj.a3ob_properties_object.is_a3_lod:
        scene_props.proxies_index = -1
        return

    scene_props.proxies.clear()
    for child in obj.children:
        if child.type != 'MESH' or not child.a3ob_properties_object_proxy.is_a3_proxy:
            continue
        
        item = scene_props.proxies.add()
        item.obj = child.name
        item.name = child.a3ob_properties_object_proxy.get_name()


def register():
    props_object.register_props()
    props_scene.register_props()
    props_mat.register_props()
    ui_object.register_ui()
    ui_mat.register_ui()

    for cls in classes:
        bpy.utils.register_class(cls)

        
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_post_handler)
    
    print("\t" + "IO: P3D")


def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update_post_handler)

    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    ui_mat.unregister_ui()
    ui_object.unregister_ui()
    props_mat.unregister_props()
    props_scene.unregister_props()
    props_object.unregister_props()
    
    print("\t" + "IO: P3D")