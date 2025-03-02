import bpy


class A3OB_PG_mcfg_bone(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name", description="Name of the bone item")
    parent: bpy.props.StringProperty(name="Parent", description="Name of the parent bone")


class A3OB_PG_mcfg_skeleton(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name", description="Name of the skeleton")
    protected: bpy.props.BoolProperty(name="Protected", description="Skeleton is protected and cannot be modified")
    bones: bpy.props.CollectionProperty(type=A3OB_PG_mcfg_bone)
    bones_index: bpy.props.IntProperty(name="Selection Index")


class A3OB_GT_mcfg(bpy.types.PropertyGroup):
    skeletons: bpy.props.CollectionProperty(type=A3OB_PG_mcfg_skeleton)
    skeletons_index: bpy.props.IntProperty(name="Active Skeleton Index", description="Double click to rename")
    bones: bpy.props.CollectionProperty(type=A3OB_PG_mcfg_bone) # empty collection to show when no skeleton is selected
    bones_index: bpy.props.IntProperty(name="Selection Index", description="Double click to rename or change parent") # empty collection to show when no skeleton is selected


classes = (
    A3OB_PG_mcfg_bone,
    A3OB_PG_mcfg_skeleton,
    A3OB_GT_mcfg
)


def register_props():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.a3ob_mcfg = bpy.props.PointerProperty(type=A3OB_GT_mcfg)


def unregister_props():
    del bpy.types.Scene.a3ob_mcfg

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
