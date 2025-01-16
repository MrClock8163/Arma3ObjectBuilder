import bpy


class A3OB_PG_proxy_access_item(bpy.types.PropertyGroup):
    obj: bpy.props.StringProperty(name="Object Name")
    name: bpy.props.StringProperty(name="Proxy Type")


class A3OB_PG_proxy_access(bpy.types.PropertyGroup):
    proxies: bpy.props.CollectionProperty(type=A3OB_PG_proxy_access_item)
    proxies_index: bpy.props.IntProperty(name="Selection Index")


classes = (
    A3OB_PG_proxy_access_item,
    A3OB_PG_proxy_access
)


def register_props():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.a3ob_proxy_access = bpy.props.PointerProperty(type=A3OB_PG_proxy_access)
    
    
def unregister_props():
    del bpy.types.Scene.a3ob_proxy_access
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
