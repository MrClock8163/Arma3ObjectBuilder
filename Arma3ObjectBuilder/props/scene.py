import bpy

from ..io_p3d.utils import ENUM_LOD_TYPES


def mesh_object_poll(self, object):
    return object.type == 'MESH'


class A3OB_PG_outliner_proxy(bpy.types.PropertyGroup):
    obj: bpy.props.StringProperty(name="Object Name")
    name: bpy.props.StringProperty(name="Proxy Type")


class A3OB_PG_outliner_lod(bpy.types.PropertyGroup):
    obj: bpy.props.StringProperty(name="Object Name")
    name: bpy.props.StringProperty(name="LOD Type")
    priority: bpy.props.FloatProperty(name="LOD Priority")
    proxy_count: bpy.props.IntProperty(name="Proxy Count")
    subobject_count: bpy.props.IntProperty(name="Sub-object Count")


class A3OB_PG_outliner(bpy.types.PropertyGroup):
    show_hidden: bpy.props.BoolProperty(name="Show Hidden Objects")
    lods: bpy.props.CollectionProperty(type=A3OB_PG_outliner_lod)
    lods_index: bpy.props.IntProperty(name="Selection Index")
    proxies: bpy.props.CollectionProperty(type=A3OB_PG_outliner_proxy)
    proxies_index: bpy.props.IntProperty(name="Selection Index")

    def clear(self):
        self.lods.clear()
        self.lods_index = -1
        self.proxies.clear()
        self.proxies_index = -1


class A3OB_PG_proxy_access(bpy.types.PropertyGroup):
    proxies: bpy.props.CollectionProperty(type=A3OB_PG_outliner_proxy)
    proxies_index: bpy.props.IntProperty(name="Selection Index")


class A3OB_PG_lod_object(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Object Name")
    lod: bpy.props.StringProperty(name="LOD type")
    enabled: bpy.props.BoolProperty(name="Enabled")


class A3OB_PG_proxies(bpy.types.PropertyGroup):
    lod_objects: bpy.props.CollectionProperty(type=A3OB_PG_lod_object)
    lod_objects_index: bpy.props.IntProperty(name="Selection Index")


class A3OB_PG_common_data_item(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name", description="Descriptive name of the common item")
    value: bpy.props.StringProperty(name="Value", description="Value of the common item")
    type: bpy.props.StringProperty(name="Type", description="Context type of the common item")


class A3OB_PG_common_data(bpy.types.PropertyGroup):
    items: bpy.props.CollectionProperty(type=A3OB_PG_common_data_item)
    items_index: bpy.props.IntProperty(name="Selection Index")


class A3OB_PG_mass_editor_stats(bpy.types.PropertyGroup):
    mass_max: bpy.props.FloatProperty(
        name = "Max Mass",
        description = "Highest vertex/component mass value on the mesh",
        default = 0,
        min = 0
    )
    mass_min: bpy.props.FloatProperty(
        name = "Min Mass",
        description = "Lowest non-zero vertex/component mass value on the mesh",
        default = 0,
        min = 0
    )
    mass_avg: bpy.props.FloatProperty(
        name = "Average Mass",
        description = "Average non-zero vertex/component mass value on the mesh",
        default = 0,
        min = 0
    )
    mass_sum: bpy.props.FloatProperty(
        name = "Total Mass",
        description = "Total vertex/component mass on the mesh",
        default = 0,
        min = 0
    )
    count_item: bpy.props.IntProperty(
        name = "Count",
        description = "Number of vertices/components in the mesh",
        default = 0,
        min = 0
    )


class A3OB_PG_mass_editor(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(
        name = "Enable Vertex Mass Tools",
        description = "Dynamic calculation of the vertex masses can be performace heavy on large meshes"
    )
    value_type: bpy.props.EnumProperty(
        name = "Value Type",
        description = "Type of the given value",
        items = (
            ('MASS', "Mass", "Value is mass, given in kg units"),
            ('DENSITY', "Density", "Value is volumetric density, given in kg/m3 units")
        ),
        default = 'MASS'
    )
    value: bpy.props.FloatProperty(
        name = "Value",
        description = "Value to operate with",
        default = 1,
        min = 0,
        max = 1000000,
        soft_max = 100000,
        precision = 3
    )
    distribution: bpy.props.EnumProperty(
        name = "Distribution",
        description = "Mass distribution between vertices",
        items = (
            ('UNIFORM', "Uniform", "Distribute mass equally among vertices"),
            ('WEIGHTED', "Weighted", "Distribute mass weighted by the cell volumes (3D Voronoi) around vertices of closed components")
        ),
        default = 'UNIFORM'
    )
    method: bpy.props.EnumProperty(
        name = "Visualization Method",
        description = "",
        items = (
            ('VERT', "Vertex", "Show per vertex mass"),
            ('COMP', "Component", "Show per component mass")
        ),
        default = 'COMP'
    )
    color_0: bpy.props.FloatVectorProperty(
        name = "NULL Color",
        description = "Color used where no vertex mass is defined",
        size = 4,
        subtype = 'COLOR',
        default = (0, 0, 0, 1),
        min = 0,
        max = 1
    )
    color_1: bpy.props.FloatVectorProperty(
        name = "Color 1",
        description = "1st element of the color ramp",
        size = 4,
        subtype = 'COLOR',
        default = (0, 0, 1, 1),
        min = 0,
        max = 1
    )
    color_2: bpy.props.FloatVectorProperty(
        name = "Color 2",
        description = "2nd element of the color ramp",
        size = 4,
        subtype = 'COLOR',
        default = (0, 1, 1, 1),
        min = 0,
        max = 1
    )
    color_3: bpy.props.FloatVectorProperty(
        name = "Color 3",
        description = "3rd element of the color ramp",
        size = 4,
        subtype = 'COLOR',
        default = (0, 1, 0, 1),
        min = 0,
        max = 1
    )
    color_4: bpy.props.FloatVectorProperty(
        name = "Color 4",
        description = "4th element of the color ramp",
        size = 4,
        subtype = 'COLOR',
        default = (1, 1, 0, 1),
        min = 0,
        max = 1
    )
    color_5: bpy.props.FloatVectorProperty(
        name = "Color 5",
        description = "5th element of the color ramp",
        size = 4,
        subtype = 'COLOR',
        default = (1, 0, 0, 1),
        min = 0,
        max = 1
    )
    color_layer_name: bpy.props.StringProperty(
        name = "Vertex Color Layer",
        description = "Name of the vertex color layer to use/create for visualization",
        default = "Vertex Masses"
    )
    stats: bpy.props.PointerProperty(type=A3OB_PG_mass_editor_stats)


class A3OB_PG_hitpoint_generator(bpy.types.PropertyGroup):
    source: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name = "Source",
        description = "Mesh object to use as source for point cloud generation",
        poll = mesh_object_poll
    )
    target: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name = "Target",
        description = "Mesh object to write generate point cloud to\n(leave empty to create new object)",
        poll = mesh_object_poll
    )
    spacing: bpy.props.FloatVectorProperty(
        name = "Spacing",
        description = "Space between generated points",
        subtype = 'XYZ',
        unit = 'LENGTH',
        min = 0.01,
        default = (0.2, 0.2, 0.2),
        size = 3
    )
    selection: bpy.props.StringProperty(name="Selection", description="Vertex group to add the generated points to")


class A3OB_PG_validation(bpy.types.PropertyGroup):
    detect: bpy.props.BoolProperty(
        name="Detect Type",
        description="Detect LOD type when set",
        default=True
    )
    lod: bpy.props.EnumProperty(
        name = "Type",
        description = "Type of LOD",
        items = ENUM_LOD_TYPES,
        default = '0'
    )
    warning_errors: bpy.props.BoolProperty(
        name = "Warnings Are Errors",
        description = "Treat warnings as errors during validation",
        default = True
    )
    relative_paths: bpy.props.BoolProperty(
        name = "Relative Paths",
        description = "Make file paths relative to the project root for validation",
        default = True
    )

 
class A3OB_PG_conversion(bpy.types.PropertyGroup):
    use_selection: bpy.props.BoolProperty(name="Selected Only", description="Convert only selected objects")
    types: bpy.props.EnumProperty(
        name = "Object Types",
        description = "Only convert object of the selected types",
        items = (
            ('MESH', "LOD", ""),
            ('DTM', "DTM", "")
        ),
        options = {'ENUM_FLAG'},
        default = {'MESH', 'DTM'}
    )
    cleanup: bpy.props.BoolProperty(
        name = "Cleanup",
        description = "Cleanup the ArmaToolbox-style settings and properties",
        default = True
    )


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


class A3OB_PG_rigging_bone(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name", description="Name of the bone item")
    parent: bpy.props.StringProperty(name="Parent", description="Name of the parent bone")


class A3OB_PG_rigging_skeleton(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name", description="Name of the skeleton")
    protected: bpy.props.BoolProperty(name="Protected", description="Skeleton is protected and cannot be modified")
    bones: bpy.props.CollectionProperty(type=A3OB_PG_rigging_bone)
    bones_index: bpy.props.IntProperty(name="Selection Index")


class A3OB_PG_rigging(bpy.types.PropertyGroup):
    skeletons: bpy.props.CollectionProperty(type=A3OB_PG_rigging_skeleton)
    skeletons_index: bpy.props.IntProperty(name="Active Skeleton Index", description="Double click to rename")
    bones: bpy.props.CollectionProperty(type=A3OB_PG_rigging_bone) # empty collection to show when no skeleton is selected
    bones_index: bpy.props.IntProperty(name="Selection Index", description="Double click to rename or change parent") # empty collection to show when no skeleton is selected
    prune_threshold: bpy.props.FloatProperty(
        name = "Threshold",
        description = "Weight threshold for pruning selections",
        min = 0.0,
        max = 1.0,
        default = 0.001,
        precision = 3
    )


classes = (
    A3OB_PG_outliner_proxy,
    A3OB_PG_outliner_lod,
    A3OB_PG_outliner,
    A3OB_PG_lod_object,
    A3OB_PG_proxies,
    A3OB_PG_common_data_item,
    A3OB_PG_common_data,
    A3OB_PG_mass_editor_stats,
    A3OB_PG_mass_editor,
    A3OB_PG_hitpoint_generator,
    A3OB_PG_validation,
    A3OB_PG_conversion,
    A3OB_PG_renamable,
    A3OB_PG_renaming,
    A3OB_PG_rigging_bone,
    A3OB_PG_rigging_skeleton,
    A3OB_PG_rigging,
    A3OB_PG_proxy_access
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.a3ob_outliner = bpy.props.PointerProperty(type=A3OB_PG_outliner)
    bpy.types.Scene.a3ob_proxies = bpy.props.PointerProperty(type=A3OB_PG_proxies)
    bpy.types.Scene.a3ob_commons = bpy.props.PointerProperty(type=A3OB_PG_common_data)
    bpy.types.Scene.a3ob_mass_editor = bpy.props.PointerProperty(type=A3OB_PG_mass_editor)
    bpy.types.Scene.a3ob_hitpoint_generator = bpy.props.PointerProperty(type=A3OB_PG_hitpoint_generator)
    bpy.types.Scene.a3ob_validation = bpy.props.PointerProperty(type=A3OB_PG_validation)
    bpy.types.Scene.a3ob_conversion = bpy.props.PointerProperty(type=A3OB_PG_conversion)
    bpy.types.Scene.a3ob_renaming = bpy.props.PointerProperty(type=A3OB_PG_renaming)
    bpy.types.Scene.a3ob_rigging = bpy.props.PointerProperty(type=A3OB_PG_rigging)
    bpy.types.Scene.a3ob_proxy_access = bpy.props.PointerProperty(type=A3OB_PG_proxy_access)
    
    print("\t" + "Properties: scene")
    
    
def unregister():
    del bpy.types.Scene.a3ob_proxy_access
    del bpy.types.Scene.a3ob_rigging
    del bpy.types.Scene.a3ob_renaming
    del bpy.types.Scene.a3ob_conversion
    del bpy.types.Scene.a3ob_validation
    del bpy.types.Scene.a3ob_hitpoint_generator
    del bpy.types.Scene.a3ob_mass_editor
    del bpy.types.Scene.a3ob_commons
    del bpy.types.Scene.a3ob_proxies
    del bpy.types.Scene.a3ob_outliner
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    print("\t" + "Properties: scene")
