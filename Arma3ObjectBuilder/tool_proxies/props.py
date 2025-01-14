import bpy


class A3OB_PG_lod_object(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Object Name")
    lod: bpy.props.StringProperty(name="LOD type")
    enabled: bpy.props.BoolProperty(name="Enabled")


class A3OB_PG_proxies(bpy.types.PropertyGroup):
    lod_objects: bpy.props.CollectionProperty(type=A3OB_PG_lod_object)
    lod_objects_index: bpy.props.IntProperty(name="Selection Index")


classes = (
    A3OB_PG_lod_object,
    A3OB_PG_proxies
)


def register_props():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.a3ob_proxies = bpy.props.PointerProperty(type=A3OB_PG_proxies)


def unregister_props():
    del bpy.types.Scene.a3ob_proxies

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)