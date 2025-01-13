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


classes = (
    A3OB_PG_proxy_access_item,
    A3OB_PG_proxy_access,
    A3OB_PG_lod_object,
    A3OB_PG_proxies,
    A3OB_PG_common_data_item,
    A3OB_PG_common_data
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.a3ob_proxies = bpy.props.PointerProperty(type=A3OB_PG_proxies)
    bpy.types.Scene.a3ob_commons = bpy.props.PointerProperty(type=A3OB_PG_common_data)
    bpy.types.Scene.a3ob_proxy_access = bpy.props.PointerProperty(type=A3OB_PG_proxy_access)
    
    print("\t" + "Properties: scene")
    
    
def unregister():
    del bpy.types.Scene.a3ob_proxy_access
    del bpy.types.Scene.a3ob_commons
    del bpy.types.Scene.a3ob_proxies
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    print("\t" + "Properties: scene")
