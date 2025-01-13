import bpy


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
    A3OB_PG_rigging_bone,
    A3OB_PG_rigging_skeleton,
    A3OB_PG_rigging
)


def register_props():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.a3ob_rigging = bpy.props.PointerProperty(type=A3OB_PG_rigging)


def unregister_props():
    del bpy.types.Scene.a3ob_rigging

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)