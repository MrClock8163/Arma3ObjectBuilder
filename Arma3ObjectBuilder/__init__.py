bl_info = {
    "name": "Arma 3 Object Builder",
    "description": "Collection of tools for editing Arma 3 content",
    "author": "MrClock (present add-on), Hans-Joerg \"Alwarren\" Frieden (original ArmaToolbox add-on)",
    "version": (2, 3, 4),
    "blender": (2, 90, 0),
    "location": "Object Builder panels",
    "warning": "",
    "doc_url": "https://mrcmodding.gitbook.io/arma-3-object-builder/home",
    "tracker_url": "https://github.com/MrClock8163/Arma3ObjectBuilder/issues",
    "category": "3D View"
}


if "bpy" in locals():
    import importlib
    
    importlib.reload(props)
    importlib.reload(ui)
    importlib.reload(flagutils)

else:
    from . import props
    from . import ui
    from .utilities import flags as flagutils

import bpy


def outliner_enable_update(self, context):
    if self.outliner == 'ENABLED' and ui.tool_outliner.depsgraph_update_post_handler not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(ui.tool_outliner.depsgraph_update_post_handler)
        ui.tool_outliner.depsgraph_update_post_handler(context.scene, None)
    elif self.outliner == 'DISABLED' and ui.tool_outliner.depsgraph_update_post_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(ui.tool_outliner.depsgraph_update_post_handler)
        context.scene.a3ob_outliner.clear()


class A3OB_OT_prefs_find_a3_tools(bpy.types.Operator):
    """Find the Arma 3 Tools installation through the Windows registry"""
    
    bl_idname = "a3ob.prefs_find_a3_tools"
    bl_label = "Find Arma 3 Tools"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        try:
            from winreg import OpenKey, QueryValueEx, HKEY_CURRENT_USER
            key = OpenKey(HKEY_CURRENT_USER, r"software\bohemia interactive\arma 3 tools")
            value, _type = QueryValueEx(key, "path")
            prefs = context.preferences.addons[__package__].preferences
            prefs.a3_tools = value
            
        except Exception:
            self.report({'ERROR'}, "The Arma 3 Tools installation could not be found, it has to be set manually")
        
        return {'FINISHED'}


class A3OB_OT_prefs_edit_flag_vertex(bpy.types.Operator):
    """Set the default vertex flag value"""

    bl_idname = "a3ob.prefs_edit_flag_vertex"
    bl_label = "Edit"
    bl_options = {'REGISTER', 'UNDO'}

    surface: bpy.props.EnumProperty(
        name = "Surface",
        items = (
            ('NORMAL', "Normal", ""),
            ('SURFACE_ON', "On Surface", ""),
            ('SURFACE_ABOVE', "Above Surface", ""),
            ('SURFACE_UNDER', "Under Surface", ""),
            ('KEEP_HEIGHT', "Keep Height", "")
        ),
        default = 'NORMAL'
    )
    fog: bpy.props.EnumProperty(
        name = "Fog",
        items = (
            ('NORMAL', "Normal", ""),
            ('SKY', "Sky", ""),
            ('NONE', "None", "")
        ),
        default = 'NORMAL'
    )
    decal: bpy.props.EnumProperty(
        name = "Decal",
        items = (
            ('NORMAL', "Normal", ""),
            ('DECAL', "Decal", "")
        ),
        default = 'NORMAL'
    )
    lighting: bpy.props.EnumProperty(
        name = "Lighting",
        items = (
            ('NORMAL', "Normal", ""),
            ('SHINING', "Shining", ""),
            ('SHADOW', "Always in Shadow", ""),
            ('LIGHTED_HALF', "Half Lighted", ""),
            ('LIGHTED_FULL', "Fully Lighted", ""),
        ),
        default = 'NORMAL'
    )
    normals: bpy.props.EnumProperty(
        name = "Normals",
        items = (
            ('AREA', "Face Dimension", ""),
            ('ANGLE', "Impedance Angle", ""),
            ('FIXED', "Fixed", ""),
        ),
        default = 'AREA'
    )
    hidden: bpy.props.BoolProperty(name="Hidden Vertex") # True: 0x00000000 False: 0x01000000
    
    @classmethod
    def poll(cls, context):
        return True
    
    def invoke(self, context, event):
        prefs = context.preferences.addons[__package__].preferences
        flagutils.set_flag_vertex(self, prefs.flag_vertex)

        return context.window_manager.invoke_props_dialog(self)
    
    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        prefs.flag_vertex = flagutils.get_flag_vertex(self)

        return {'FINISHED'}


class A3OB_OT_prefs_edit_flag_face(bpy.types.Operator):
    """Set the default face flag value"""

    bl_idname = "a3ob.prefs_edit_flag_face"
    bl_label = "Edit"
    bl_options = {'REGISTER', 'UNDO'}
    
    lighting: bpy.props.EnumProperty(
        name = "Lighting & Shadows",
        items = (
            ('NORMAL', "Normal", ""),
            ('BOTH', "Both Sides", ""),
            ('POSITION', "Position", ""),
            ('FLAT', "Flat", ""),
            ('REVERSED', "Reversed", "")
        ),
        default = 'NORMAL'
    )
    zbias: bpy.props.EnumProperty(
        name = "Z Bias",
        items = (
            ('NONE', "None", ""),
            ('LOW', "Low", ""),
            ('MIDDLE', "Middle", ""),
            ('HIGH', "High", "")
        )
    )
    shadow: bpy.props.BoolProperty(name = "Enable Shadow", default = True) # True: 0x00000000 False: 0x00000010
    merging: bpy.props.BoolProperty(name = "Enable Texture Merging", default = True) # True: 0x00000000 False: 0x01000000
    user: bpy.props.IntProperty(
        name = "User Value",
        min = 0,
        max = 127
    )

    @classmethod
    def poll(cls, context):
        return True
    
    def invoke(self, context, event):
        prefs = context.preferences.addons[__package__].preferences
        flagutils.set_flag_face(self, prefs.flag_face)

        return context.window_manager.invoke_props_dialog(self)
    
    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        prefs.flag_face = flagutils.get_flag_face(self)

        return {'FINISHED'}


class A3OB_AT_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__
    
    tabs: bpy.props.EnumProperty(
        name = "Tabs",
        default = 'GENERAL',
        items = (
            ('GENERAL', "General", "General and misc settings", 'PREFERENCES', 0),
            ('PATHS', "Paths", "File path related settings", 'FILE_TICK', 1),
            ('DEFAULTS', "Defaults", "Default fallback values", 'RECOVER_LAST', 2),
            ('DEBUG', "Debug", "Debug options", 'ERROR', 4)
        )
    )
    # General
    show_info_links: bpy.props.BoolProperty(
        name = "Show Help Links",
        description = "Display links to the addon documentation in the headers of panels",
        default = True
    )
    create_backups: bpy.props.BoolProperty(
        name = "Create Backups",
        description = "When overwriting an existing output file, create a backup copy (.bak) of the original"
    )
    icon_theme: bpy.props.EnumProperty(
        name = "Icon Theme",
        description = "Color theme of custom icons",
        items = (
            ('DARK', "Dark", "Icons with light main color, ideal for dark themes in Blender"),
            ('LIGHT', "Light", "Icons with dark main color, ideal for light themes in Blender")
        ),
        default = 'DARK'
    )
    outliner: bpy.props.EnumProperty(
        name = "Outliner",
        description = "Enable or disable LOD object outliner panel",
        items = (
            ('ENABLED', "Enabled", ""),
            ('DISABLED', "Disabled", "")
        ),
        default = 'ENABLED',
        update = outliner_enable_update
    )
    # Paths
    a3_tools: bpy.props.StringProperty(
        name = "Arma 3 Tools",
        description = "Install directory of the official Arma 3 Tools",
        subtype = 'DIR_PATH'
    )
    project_root: bpy.props.StringProperty(
        name = "Project Root",
        description = "Root directory of the project (should be P:\ for most cases)",
        default = "P:\\",
        subtype = 'DIR_PATH'
    )
    custom_data: bpy.props.StringProperty(
        name = "Custom Data",
        description = "Path to JSON file containing data for custom preset list items (common named properties and proxies)",
        subtype = 'FILE_PATH'
    )
    # Defaults
    flag_vertex: bpy.props.IntProperty(name="Vertex Flag", default=0x02000000)
    flag_face: bpy.props.IntProperty(name="Face Flag")
    flag_vertex_display: bpy.props.StringProperty(
        name = "Vertex Flag",
        description = "Default vertex flag",
        default = "02000000",
        get = lambda self: "%08x" % self.flag_vertex
    )
    flag_face_display: bpy.props.StringProperty(
        name = "Face Flag",
        description = "Default face flag",
        default = "00000000",
        get = lambda self: "%08x" % self.flag_face
    )
    # Debug
    preserve_faulty_output: bpy.props.BoolProperty(
        name = "Preserve Faulty Output",
        description = "Preserve the .temp files if an export failed (could be useful to attach to a bug report)"
    )
    preserve_preprocessed_lods: bpy.props.BoolProperty(
        name = "Preserve Preprocessed LOD Objects",
        description = "Preserve the preprocessed LOD meshes that were generated during P3D export"
    )

    def draw(self, context):
        layout = self.layout
        
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop_tabs_enum(self, "tabs")
        box = col.box()
        box.use_property_split = True
        box.use_property_decorate = False
        
        if self.tabs == 'GENERAL':
            box.prop(self, "show_info_links")
            box.prop(self, "create_backups")
            row_theme = box.row(align=True)
            row_theme.prop(self, "icon_theme", expand=True)
            row_outliner = box.row(align=True)
            row_outliner.prop(self, "outliner", expand=True)
            
        elif self.tabs == 'PATHS':
            row_a3_tools = box.row(align=True)
            row_a3_tools.prop(self, "a3_tools", icon='TOOL_SETTINGS')
            row_a3_tools.operator("a3ob.prefs_find_a3_tools", text="", icon='VIEWZOOM')
            box.prop(self, "project_root", icon='DISK_DRIVE')
            box.prop(self, "custom_data", icon='PRESET')
        
        elif self.tabs == 'DEFAULTS':
            row_vertex = box.row(align=True)
            row_vertex.prop(self, "flag_vertex_display")
            row_vertex.operator("a3ob.prefs_edit_flag_vertex", text="", icon='GREASEPENCIL')

            row_face = box.row(align=True)
            row_face.prop(self, "flag_face_display")
            row_face.operator("a3ob.prefs_edit_flag_face", text="", icon='GREASEPENCIL')
        
        elif self.tabs == 'DEBUG':
            box.prop(self, "preserve_faulty_output")
            box.prop(self, "preserve_preprocessed_lods")


classes = (
    A3OB_OT_prefs_find_a3_tools,
    A3OB_OT_prefs_edit_flag_vertex,
    A3OB_OT_prefs_edit_flag_face,
    A3OB_AT_preferences
)


modules = (
    props.object,
    props.material,
    props.scene,
    props.action,
    ui.props_action,
    ui.props_object_mesh,
    ui.props_material,
    ui.import_export_p3d,
    ui.import_export_rtm,
    ui.import_export_mcfg,
    ui.import_export_armature,
    ui.import_export_asc,
    ui.tool_outliner,
    ui.tool_mass,
    ui.tool_materials,
    ui.tool_hitpoint,
    ui.tool_paths,
    ui.tool_proxies,
    ui.tool_validation,
    ui.tool_rigging,
    ui.tool_utilities,
    ui.tool_scripts
)


def register():
    from bpy.utils import register_class
    from .utilities import generic
        
    print("Registering Arma 3 Object Builder ( '" + __package__ + "' )")
    
    for cls in classes:
        register_class(cls)
    
    for mod in modules:
        mod.register()
    
    generic.register_icons()
    
    print("Register done")


def unregister():
    from bpy.utils import unregister_class
    from .utilities import generic

    print("Unregistering Arma 3 Object Builder ( '" + __package__ + "' )")
    
    generic.unregister_icons()
    
    for mod in reversed(modules):
        mod.unregister()
    
    for cls in reversed(classes):
        unregister_class(cls)
    
    print("Unregister done")
