import bpy


class A3OB_PG_renamable(bpy.types.PropertyGroup):
    path: bpy.props.StringProperty(name = "From", description = "File path")


class A3OB_PG_renaming(bpy.types.PropertyGroup):
    source_filter: bpy.props.EnumProperty(
        name = "Filter",
        description = "",
        items = (
            ('TEX', "Texture", "Show paths to textures"),
            ('RVMAT', "RVMAT", "Show paths to RVMATs"),
            ('PROXY', "Proxy", "Show paths to proxies")
        ),
        options = {'ENUM_FLAG'},
        default = {'TEX','RVMAT', 'PROXY'}
    )
    path_list: bpy.props.CollectionProperty(type=A3OB_PG_renamable)
    path_list_index: bpy.props.IntProperty(name="Selection Index")
    new_path: bpy.props.StringProperty(
        name = "To",
        description = "New file path",
        subtype = 'FILE_PATH'
    )
    root_old: bpy.props.StringProperty(
        name = "From",
        description = "Path root to change",
        subtype = 'FILE_PATH'
    )
    root_new: bpy.props.StringProperty(
        name = "To",
        description = "Path to change root to",
        subtype = 'FILE_PATH'
    )
    vgroup_old: bpy.props.StringProperty(name="From", description="Vertex group to rename")
    vgroup_new: bpy.props.StringProperty(name = "To", description = "New vertex group name")
    vgroup_match_whole: bpy.props.BoolProperty(
        name = "Whole Name",
        description = "Only replace if the whole name matches",
        default = True
    )


classes = (
    A3OB_PG_renamable,
    A3OB_PG_renaming
)


def register_props():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.a3ob_renaming = bpy.props.PointerProperty(type=A3OB_PG_renaming)


def unregister_props():
    del bpy.types.Scene.a3ob_renaming

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
