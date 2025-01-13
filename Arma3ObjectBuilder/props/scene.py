import bpy


class A3OB_PG_proxy_access_item(bpy.types.PropertyGroup):
    obj: bpy.props.StringProperty(name="Object Name")
    name: bpy.props.StringProperty(name="Proxy Type")


class A3OB_PG_proxy_access(bpy.types.PropertyGroup):
    proxies: bpy.props.CollectionProperty(type=A3OB_PG_proxy_access_item)
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


classes = (
    A3OB_PG_proxy_access_item,
    A3OB_PG_proxy_access,
    A3OB_PG_lod_object,
    A3OB_PG_proxies,
    A3OB_PG_common_data_item,
    A3OB_PG_common_data,
    A3OB_PG_mass_editor_stats,
    A3OB_PG_mass_editor,
    A3OB_PG_conversion
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.a3ob_proxies = bpy.props.PointerProperty(type=A3OB_PG_proxies)
    bpy.types.Scene.a3ob_commons = bpy.props.PointerProperty(type=A3OB_PG_common_data)
    bpy.types.Scene.a3ob_mass_editor = bpy.props.PointerProperty(type=A3OB_PG_mass_editor)
    bpy.types.Scene.a3ob_conversion = bpy.props.PointerProperty(type=A3OB_PG_conversion)
    bpy.types.Scene.a3ob_proxy_access = bpy.props.PointerProperty(type=A3OB_PG_proxy_access)
    
    print("\t" + "Properties: scene")
    
    
def unregister():
    del bpy.types.Scene.a3ob_proxy_access
    del bpy.types.Scene.a3ob_conversion
    del bpy.types.Scene.a3ob_mass_editor
    del bpy.types.Scene.a3ob_commons
    del bpy.types.Scene.a3ob_proxies
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    print("\t" + "Properties: scene")
