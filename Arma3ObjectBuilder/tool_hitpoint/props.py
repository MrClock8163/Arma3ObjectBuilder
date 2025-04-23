import bpy


def mesh_object_poll(self, object):
    return object.type == 'MESH'


class A3OB_PG_hitpoint_generator(bpy.types.PropertyGroup):
    source: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name = "Source",
        description = "Mesh object to use as source for point cloud generation",
        poll = mesh_object_poll
    )
    target: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name = "Target",
        description = "Mesh object to write generate point cloud to\n(leave empty to create new object)",
        poll = mesh_object_poll
    )
    spacing: bpy.props.FloatVectorProperty(
        name = "Spacing",
        description = "Space between generated points",
        subtype = 'XYZ',
        unit = 'LENGTH',
        min = 0.01,
        default = (0.2, 0.2, 0.2),
        size = 3
    )
    selection: bpy.props.StringProperty(name="Selection", description="Vertex group to add the generated points to")


classes = (
    A3OB_PG_hitpoint_generator,
)


def register_props():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.a3ob_hitpoint_generator = bpy.props.PointerProperty(type=A3OB_PG_hitpoint_generator)


def unregister_props():
    del bpy.types.Scene.a3ob_hitpoint_generator

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
