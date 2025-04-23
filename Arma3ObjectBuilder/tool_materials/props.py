import bpy

from .colors import convert_color


def color_conversion_update(self, context):
    rgb = (0, 0, 0)
    if self.input_type == 'S8':
        rgb = (self.input_red_int, self.input_green_int, self.input_blue_int)
    else:
        rgb = (self.input_red_float, self.input_green_float, self.input_blue_float)
    
    rgb_out = convert_color(rgb, self.input_type, self.output_type)
    if self.output_type == 'S8':
        self.output_red_int = rgb_out[0]
        self.output_green_int = rgb_out[1]
        self.output_blue_int = rgb_out[2]
    else:
        self.output_red_float = rgb_out[0]
        self.output_green_float = rgb_out[1]
        self.output_blue_float = rgb_out[2]
        
    if self.output_type in {'S8', 'S'}:
        self.output_srgb = convert_color(rgb, self.input_type, 'S')
    else:
        self.output_linear = rgb_out


class A3OB_PG_colors(bpy.types.PropertyGroup):
    input_type: bpy.props.EnumProperty(
        name = "Input Type",
        description = "Color space of the input value",
        items = (
            ('S8', "sRGB8", "8-bit sRGB color [0 - 255]"),
            ('S', "sRGB", "Decimal sRGB color [0.0 - 1.0]"),
            ('L', "Linear", "Linear RGB color [0.0 - 1.0]")
        ),
        default = 'S8',
        update = color_conversion_update
    )
    output_type: bpy.props.EnumProperty(
        name = "Output Type",
        description = "Color space of the output value",
        items = (
            ('S8', "sRGB8", "8-bit sRGB color [0 - 255]"),
            ('S', "sRGB", "Decimal sRGB color [0.0 - 1.0]"),
            ('L', "Linear", "Linear RGB color [0.0 - 1.0]")
        ),
        default = 'S',
        update = color_conversion_update
    )
    # Float inputs
    input_red_float: bpy.props.FloatProperty(
        name = "R",
        description = "Input red value",
        min = 0,
        max = 1,
        precision = 3,
        update = color_conversion_update
    )
    input_green_float: bpy.props.FloatProperty(
        name = "G",
        description = "Input green value",
        min = 0,
        max = 1,
        precision = 3,
        update = color_conversion_update
    )
    input_blue_float: bpy.props.FloatProperty(
        name = "B",
        description = "Input blue value",
        min = 0,
        max = 1,
        precision = 3,
        update = color_conversion_update
    )
    # Integer inputs
    input_red_int: bpy.props.IntProperty(
        name = "R",
        description = "Input red value",
        min = 0,
        max = 255,
        update = color_conversion_update
    )
    input_green_int: bpy.props.IntProperty(
        name = "G",
        description = "Input green value",
        min = 0,
        max = 255,
        update = color_conversion_update
    )
    input_blue_int: bpy.props.IntProperty(
        name = "B",
        description = "Input blue value",
        min = 0,
        max = 255,
        update = color_conversion_update
    )
    # Float outputs
    output_red_float: bpy.props.FloatProperty(
        name = "R",
        description = "Output red value",
        min = 0,
        max = 1,
        precision = 3
    )
    output_green_float: bpy.props.FloatProperty(
        name = "G",
        description = "Output green value",
        min = 0,
        max = 1,
        precision = 3
    )
    output_blue_float: bpy.props.FloatProperty(
        name = "B",
        description = "Output blue value",
        min = 0,
        max = 1,
        precision = 3
    )
    # Integer outputs
    output_red_int: bpy.props.IntProperty(
        name = "R",
        description = "Output red value",
        min = 0,
        max = 255
    )
    output_green_int: bpy.props.IntProperty(
        name = "G",
        description = "Output green value",
        min = 0,
        max = 255
    )
    output_blue_int: bpy.props.IntProperty(
        name = "B",
        description = "Output blue value",
        min = 0,
        max = 255
    )
    # Color outputs
    output_srgb: bpy.props.FloatVectorProperty(
        name = "Output Color",
        description = "Color sample of the output color",
        subtype = 'COLOR_GAMMA',
        min = 0,
        max = 1
    )
    output_linear: bpy.props.FloatVectorProperty(
        name = "Output Color",
        description = "Color sample of the output color",
        subtype = 'COLOR',
        min = 0,
        max = 1
    )


class A3OB_PG_materials_template(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    path: bpy.props.StringProperty()


class A3OB_PG_materials(bpy.types.PropertyGroup):
    templates: bpy.props.CollectionProperty(type=A3OB_PG_materials_template)
    templates_index: bpy.props.IntProperty(name="Selection Index", description="")
    folder: bpy.props.StringProperty(
        name = "Folder",
        description = "Source folder of the texture files",
        subtype = 'DIR_PATH'
    )
    basename: bpy.props.StringProperty(
        name = "Name",
        description = "Name of the texture set to be processed"
    )
    check_files_exist: bpy.props.BoolProperty(
        name = "Ensure Files Exist",
        description = "If the textures files do not actually exist on the expected paths, use the default values of the template",
        default = True
    )
    overwrite_existing: bpy.props.BoolProperty(
        name = "Overwrite",
        description = "Overwrite the target RVMAT file if it already exists"
    )


classes = (
    A3OB_PG_colors,
    A3OB_PG_materials_template,
    A3OB_PG_materials
)


def register_props():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.a3ob_colors = bpy.props.PointerProperty(type=A3OB_PG_colors)
    bpy.types.Scene.a3ob_materials = bpy.props.PointerProperty(type=A3OB_PG_materials)


def unregister_props():
    bpy.types.Scene.a3ob_materials
    bpy.types.Scene.a3ob_colors

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
