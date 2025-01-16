import os

import bpy
from bpy.app.handlers import persistent

from .. import get_prefs
from .. import utils_io
from ..tool_mass import masses
from ..io_p3d.data import P3D_LOD_Resolution as LODRes
from ..io_p3d import flags as p3d_flags
from ..io_p3d import utils as p3d_utils


bl_version = bpy.app.version


KNOWN_NAMEDPROPS = {
    "animated": [],
    "aicovers": ["0", "1"],
    "armor": [],
    "autocenter": ["0", "1"],
    "buoyancy": ["0", "1"],
    "cratercolor": [],
    "canbeoccluded": ["0", "1"],
    "canocclude": ["0", "1"],
    "class": [
        "breakablehouseanimated",
        "bridge",
        "building",
        "bushhard",
        "bushsoft",
        "church",
        "clutter",
        "forest",
        "house",
        "housesimulated",
        "land_decal",
        "man",
        "none",
        "pond",
        "road",
        "streetlamp",
        "thing",
        "thingx",
        "tower",
        "treehard",
        "treesoft",
        "vehicle",
        "wall"
    ],
    "damage": [
        "building",
        "engine",
        "no",
        "tent",
        "tree",
        "wall",
        "wreck"
    ],
    "destroysound": [
        "treebroadleaf",
        "treepalm"
    ],
    "drawimportance": [],
    "explosionshielding": [],
    "forcenotalpha": ["0", "1"],
    "frequent": ["0", "1"],
    "keyframe": ["0", "1"],
    "loddensitycoef": [],
    "lodnoshadow": ["0", "1"],
    "map": [
        "main road",
        "road",
        "track",
        "trail",
        "building",
        "fence",
        "wall",
        "bush",
        "small tree",
        "tree",
        "rock",
        "bunker",
        "fortress",
        "fuelstation",
        "hospital",
        "lighthouse",
        "quay",
        "view-tower",
        "ruin",
        "busstop",
        "church",
        "chapel",
        "cross",
        "fountain",
        "power lines",
        "powersolar",
        "powerwave",
        "powerwind",
        "railway",
        "shipwreck",
        "stack",
        "tourism",
        "transmitter",
        "watertower",
        "hide"
    ],
    "mass": [],
    "maxsegments": [],
    "minsegments": [],
    "notl": [],
    "placement": [
        "slope",
        "slopez",
        "slopex",
        "slopelandcontact",
        "vertical"
    ],
    "prefershadowvolume": ["0", "1"],
    "reversed": [],
    "sbsource": [
        "explicit",
        "none",
        "shadow",
        "shadowvolume",
        "visual",
        "visualex"
    ],
    "shadow": ["hybrid"],
    "shadowlod": [],
    "shadowvolumelod": [],
    "shadowbufferlod": [],
    "shadowbufferlodvis": [],
    "shadowoffset": [],
    "viewclass": [],
    "viewdensitycoef": [],
    "xcount": [],
    "xsize": [],
    "xstep": [],
    "ycount": [],
    "ysize": []
}


def proxy_name_update(self, context):
    if not self.is_a3_proxy:
        return
    
    name = "proxy: %s" % self.get_name()
    obj = self.id_data
    obj.name = name
    obj.data.name = name


if bl_version >= (3, 3, 0):
    class A3OB_PG_properties_named_property(bpy.types.PropertyGroup):
        name: bpy.props.StringProperty(
            name = "Name",
            description = "Property name",
            maxlen = 63,
            search = lambda self, context, edit_text: [item for item in KNOWN_NAMEDPROPS if item.lower().startswith(edit_text.lower())],
            search_options = {'SORT', 'SUGGESTION'}
        )
        value: bpy.props.StringProperty(
            name = "Value",
            description = "Property value",
            maxlen = 63,
            search = lambda self, context, edit_text: [item for item in KNOWN_NAMEDPROPS.get(self.name.lower(), []) if item.startswith(edit_text.lower())],
            search_options = {'SORT', 'SUGGESTION'}
        )
else:
    class A3OB_PG_properties_named_property(bpy.types.PropertyGroup):
        name: bpy.props.StringProperty(
            name = "Name",
            description = "Property name",
            maxlen = 63
        )
        value: bpy.props.StringProperty(
            name = "Value",
            description = "Property value",
            maxlen = 63
        )


class A3OB_PG_properties_flag_vertex(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name", description="Name of the vertex flag group")
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
    
    def get_flag(self):        
        return p3d_flags.get_flag_vertex(self)
    
    def set_flag(self, value):
        p3d_flags.set_flag_vertex(self, value)


class A3OB_PG_properties_flag_face(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name", description="Name of the face flag group")
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
    shadow: bpy.props.BoolProperty(name="Enable Shadow", default=True) # True: 0x00000000 False: 0x00000010
    merging: bpy.props.BoolProperty(name="Enable Texture Merging", default=True) # True: 0x00000000 False: 0x01000000
    user: bpy.props.IntProperty(
        name = "User Value",
        min = 0,
        max = 127
    )
    
    def get_flag(self):
        return p3d_flags.get_flag_face(self)

    def set_flag(self, value):
        p3d_flags.set_flag_face(self, value)


class A3OB_PG_properties_lod_copy(bpy.types.PropertyGroup):
    lod: bpy.props.EnumProperty(
        name = "LOD Type",
        description = "Type of LOD",
        items = p3d_utils.ENUM_LOD_TYPES,
        default = '0'
    )
    resolution: bpy.props.IntProperty(
        name = "Resolution/Index",
        description = "Resolution or index value of LOD object",
        default = 1,
        min = 0,
        soft_max = 1000,
        step = 1
    )
    resolution_float: bpy.props.FloatProperty(
        name = "Resolution/Index",
        description = "Resolution or index value of LOD object of unknown type",
        default = 1,
        min = 0,
        soft_max = 1000,
        step = 1
    )


class A3OB_PG_properties_object_mesh(bpy.types.PropertyGroup):
    is_a3_lod: bpy.props.BoolProperty(
        name = "Arma 3 LOD",
        description = "This object is a LOD for an Arma 3 P3D"
    )
    lod: bpy.props.EnumProperty(
        name = "LOD Type",
        description = "Type of LOD",
        items = p3d_utils.ENUM_LOD_TYPES,
        default = '0'
    )
    resolution: bpy.props.IntProperty(
        name = "Resolution/Index",
        description = "Resolution or index value of LOD object",
        default = 1,
        min = 0,
        soft_max = 1000,
        step = 1
    )
    resolution_float: bpy.props.FloatProperty(
        name = "Resolution/Index",
        description = "Resolution or index value of LOD object of unknown type",
        default = 1,
        min = 0,
        soft_max = 1000,
        step = 1
    )
    properties: bpy.props.CollectionProperty(
        name = "Named Properties",
        description = "Named properties associated with the LOD",
        type = A3OB_PG_properties_named_property
    )
    property_index: bpy.props.IntProperty(name="Active Property Index", description="Double click to change name and value")
    copies: bpy.props.CollectionProperty(
        name = "Copies",
        description = "LODs to copy the edited LOD to",
        type = A3OB_PG_properties_lod_copy
    )
    copies_index: bpy.props.IntProperty(name="Active Copy Index", description="")

    def get_name(self):
        return LODRes.build_name(int(self.lod), self.resolution)


class A3OB_PG_properties_object_flags(bpy.types.PropertyGroup):
    vertex: bpy.props.CollectionProperty(
        name = "Vertex Flag Groups",
        description = "Vertex flag groups used in the LOD",
        type = A3OB_PG_properties_flag_vertex
    )
    vertex_index: bpy.props.IntProperty(name="Vertex Flag Group Index")
    face: bpy.props.CollectionProperty(
        name = "Active Face Flag Groups",
        description = "Face flag groups used in the LOD",
        type = A3OB_PG_properties_flag_face
    )
    face_index: bpy.props.IntProperty(name="Active Face Flag Group Index")


class A3OB_PG_properties_object_proxy(bpy.types.PropertyGroup):
    is_a3_proxy: bpy.props.BoolProperty(
        name = "Arma 3 Model Proxy",
        description = "This object is a proxy (cannot change manually)",
        update = proxy_name_update
    )
    proxy_path: bpy.props.StringProperty(
        name = "Path",
        description = "File path to the proxy model",
        subtype = 'FILE_PATH',
        update = proxy_name_update
    )
    proxy_index: bpy.props.IntProperty(
        name = "Index",
        description = "Index of proxy",
        default = 1,
        min = 0,
        max = 999,
        update = proxy_name_update
    )
    
    def to_placeholder(self, relative):
        path = utils_io.format_path(utils_io.abspath(self.proxy_path), utils_io.abspath(get_prefs().project_root), relative, False)
        if relative and len(path) > 0 and path[0] != "\\":
            path = "\\" + path
        
        return path, self.proxy_index
    
    def get_name(self):
        name = os.path.basename(os.path.splitext(utils_io.abspath(self.proxy_path))[0]).strip()
        if name == "":
            name = "unknown"
            
        name = "%s %d" % (name, self.proxy_index)

        return name


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


classes = (
    A3OB_PG_properties_named_property,
    A3OB_PG_properties_flag_vertex,
    A3OB_PG_properties_flag_face,
    A3OB_PG_properties_lod_copy,
    A3OB_PG_properties_object_mesh,
    A3OB_PG_properties_object_flags,
    A3OB_PG_properties_object_proxy
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Object.a3ob_properties_object = bpy.props.PointerProperty(type=A3OB_PG_properties_object_mesh)
    bpy.types.Object.a3ob_properties_object_flags = bpy.props.PointerProperty(type=A3OB_PG_properties_object_flags)
    bpy.types.Object.a3ob_properties_object_proxy = bpy.props.PointerProperty(type=A3OB_PG_properties_object_proxy)

    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_post_handler)
    
    print("\t" + "Properties: object")


def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update_post_handler)

    del bpy.types.Object.a3ob_properties_object_proxy
    del bpy.types.Object.a3ob_properties_object_flags
    del bpy.types.Object.a3ob_properties_object
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    print("\t" + "Properties: object")
