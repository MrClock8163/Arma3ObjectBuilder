import bpy


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


classes = (
    A3OB_PG_outliner_proxy,
    A3OB_PG_outliner_lod,
    A3OB_PG_outliner
)


def register_props():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.a3ob_outliner = bpy.props.PointerProperty(type=A3OB_PG_outliner)


def unregister_props():
    del bpy.types.Scene.a3ob_outliner

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)