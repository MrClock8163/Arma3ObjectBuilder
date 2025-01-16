import bpy


class A3OB_PG_rtm_keyframe(bpy.types.PropertyGroup):
    index: bpy.props.IntProperty(name="Frame Index", description="Index of frame to export")


class A3OB_PG_rtm_property(bpy.types.PropertyGroup):
    index: bpy.props.IntProperty(name="Frame Index", description="Property frame index")
    name: bpy.props.StringProperty(name="Name", description="Name of frame property")
    value: bpy.props.StringProperty(name="Value", description="Value of frame property")


class A3OB_PG_properties_action(bpy.types.PropertyGroup):
    motion_source: bpy.props.EnumProperty(
        name = "Motion Source",
        description = "Source of motion vector",
        items = (
            ('MANUAL', "Manual", "The motion vector is explicitly set"),
            ('CALCULATED', "Calculated", "The motion vector is calculated from the motion of a specific bone during the animation")
        ),
        default = 'MANUAL'
    )
    motion_vector: bpy.props.FloatVectorProperty(
        name = "Motion Vector",
        description = "Total motion done during the animation",
        default = (0, 0, 0),
        subtype = 'XYZ',
        unit = 'LENGTH'
    )
    motion_bone: bpy.props.StringProperty(name="Reference Bone", description="Bone to track for motion calculation")
    frames: bpy.props.CollectionProperty(
        name = "RTM frames",
        description = "List of frames to export to RTM",
        type = A3OB_PG_rtm_keyframe
    )
    frames_index: bpy.props.IntProperty(name="Active Frame Index")
    props: bpy.props.CollectionProperty(
        name = "RTM frame properties",
        description = "List of frame properties to export to RTM",
        type = A3OB_PG_rtm_property
    )
    props_index: bpy.props.IntProperty(name="Active Property Index")


classes = (
    A3OB_PG_rtm_keyframe,
    A3OB_PG_rtm_property,
    A3OB_PG_properties_action
)


def register_props():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Action.a3ob_properties_action = bpy.props.PointerProperty(type=A3OB_PG_properties_action)


def unregister_props():
    del bpy.types.Action.a3ob_properties_action

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)