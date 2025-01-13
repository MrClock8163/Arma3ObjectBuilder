import re

import bpy

from .. import get_prefs
from .. import utils_io


class A3OB_PG_properties_material(bpy.types.PropertyGroup):
    texture_type: bpy.props.EnumProperty( 
        name = "Texture Source",
        description = "Source of face texture",
        items = (
            ('TEX', "File", "Texture file"),
            ('COLOR', "Color", "Procedural color"),
            ('CUSTOM', "Custom", "Raw custom input")
        ),
        default = 'TEX'
    )
    texture_path: bpy.props.StringProperty(
        name = "Texture",
        description = "Path to texture file",
        subtype = 'FILE_PATH',
    )
    color_value: bpy.props.FloatVectorProperty(
        name = "Color",
        description = "Color used to generate procedural texture string",
        subtype = 'COLOR_GAMMA',
        min = 0.0,
        max = 1.0,
        default = (1, 1, 1, 1),
        size = 4
    )
    color_type: bpy.props.EnumProperty(
        name = "Type",
        description = "Procedural texture type",
        items = (
            ('CO', "CO", "Color Value"),
            ('CA', "CA", "Texture with Alpha"),
            ('LCO', "LCO", "Terrain Texture Layer Color"),
            ('SKY', "SKY", "Sky texture"),
            ('NO', "NO", "Normal Map"),
            ('NS', "NS", "Normal map specular with Alpha"),
            ('NOF', "NOF", "Normal map faded"),
            ('NON', "NON", "Normal map noise"),
            ('NOHQ', "NOHQ", "Normal map High Quality"),
            ('NOPX', "NOPX", "Normal Map with paralax"),
            ('NOVHQ', "NOVHQ", "two-part DXT5 compression"),
            ('DT', "DT", "Detail Texture"),
            ('CDT', "CDT", "Colored detail texture"),
            ('MCO', "MCO", "Multiply color"),
            ('DTSMDI', "DTSMDI", "Detail SMDI map"),
            ('MC', "MC", "Macro Texture"),
            ('AS', "AS", "Ambient Shadow texture"),
            ('ADS', "ADS", "Ambient Shadow in Blue"),
            ('PR', "PR", "Ambient shadow from directions"),
            ('SM', "SM", "Specular Map"),
            ('SMDI', "SMDI", "Specular Map, optimized"),
            ('MASK', "MASK", "Mask for multimaterial"),
            ('TI', "TI", "Thermal imaging map")
        ),
        default = 'CO'
    )
    color_raw: bpy.props.StringProperty(
        name = "Raw Input",
        description = "Raw string intput that will be directly copied into the exported model"
    )
    material_path: bpy.props.StringProperty(
        name = "Material",
        description = "Path to RVMAT file",
        subtype = 'FILE_PATH'
    )
    # hidden_selection: bpy.props.StringProperty(
        # name = "Create Selection",
        # description = "Name of the selection to create for the material (leave empty to not create selection)"
    # )
    
    def from_p3d(self, texture, material, absolute):
        regex_procedural = "#\(.*?\)\w+\(.*?\)"
        regex_procedural_color = "#\(argb,\d+,\d+,\d+\)color\((\d+.?\d*),(\d+.?\d*),(\d+.?\d*),(\d+.?\d*),([a-zA-Z]+)\)"
        
        if re.match(regex_procedural, texture):
            texture = texture.replace(" ", "") # remove spaces to simplify regex parsing
            tex = re.match(regex_procedural_color, texture)
            if tex:
                self.texture_type = 'COLOR'
                data = tex.groups()
                
                try:
                    self.color_type = data[4].upper()
                    self.color_value = (float(data[0]), float(data[1]), float(data[2]), float(data[3]))
                except:
                    self.texture_type = 'CUSTOM'
                    self.color_raw = texture
                
            else:
                self.texture_type = 'CUSTOM'
                self.color_raw = texture
            
        else:
            self.texture_path = utils_io.restore_absolute(texture) if absolute else texture
        
        self.material_path = utils_io.restore_absolute(material) if absolute else material
    
    def to_p3d(self, relative):
        addon_prefs = get_prefs()
        texture = ""
        material = ""

        if self.texture_type == 'TEX':
            texture = utils_io.format_path(utils_io.abspath(self.texture_path), utils_io.abspath(addon_prefs.project_root), relative)
        elif self.texture_type == 'COLOR':
            color = self.color_value
            texture = "#(argb,8,8,3)color(%.3f,%.3f,%.3f,%.3f,%s)" % (color[0], color[1], color[2], color[3], self.color_type)
        else:
            texture = self.color_raw
        
        material = utils_io.format_path(utils_io.abspath(self.material_path), utils_io.abspath(addon_prefs.project_root), relative)

        return texture, material


classes = (
    A3OB_PG_properties_material,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Material.a3ob_properties_material = bpy.props.PointerProperty(type=A3OB_PG_properties_material)
    
    print("\t" + "Properties: material")


def unregister():
    del bpy.types.Material.a3ob_properties_material
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    print("\t" + "Properties: material")
