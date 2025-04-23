import bpy

from ..io_p3d.utils import ENUM_LOD_TYPES


class A3OB_PG_validation(bpy.types.PropertyGroup):
    detect: bpy.props.BoolProperty(
        name="Detect Type",
        description="Detect LOD type when set",
        default=True
    )
    lod: bpy.props.EnumProperty(
        name = "Type",
        description = "Type of LOD",
        items = ENUM_LOD_TYPES,
        default = '0'
    )
    warning_errors: bpy.props.BoolProperty(
        name = "Warnings Are Errors",
        description = "Treat warnings as errors during validation",
        default = True
    )
    relative_paths: bpy.props.BoolProperty(
        name = "Relative Paths",
        description = "Make file paths relative to the project root for validation",
        default = True
    )


classes = (
    A3OB_PG_validation,
)


def register_props():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.a3ob_validation = bpy.props.PointerProperty(type=A3OB_PG_validation)


def unregister_props():
    del bpy.types.Scene.a3ob_validation

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)