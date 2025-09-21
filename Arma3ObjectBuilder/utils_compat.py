# Helper functions to handle API compatibility issues between different versions of Blender

from typing import Callable, Any, Generator


import bpy
from mathutils import Vector


# Blender 4.0.0 removed the traditional bpy.ops.xyz.xyz(ctx, **kwargs) type operator calling,
# and since the new temp_override method was only introduced late in the 3.x.x versions,
# to maintain compatibility with older releases, the operator call has to be version dependent
# https://developer.blender.org/docs/release_notes/4.0/python_api/#blender-operators-bpyops
# TODO: Move to utils
def call_operator_ctx(
    op: Callable[..., Any],
    ctx: dict[str, Any] | None = None,
    **kwargs: Any
) -> None:
    if not ctx:
        op(**kwargs)
        return

    with bpy.context.temp_override(**ctx):
        op(**kwargs)


# https://developer.blender.org/docs/release_notes/4.1/python_api/#breaking-changes
# TODO: Remove
def mesh_auto_smooth(mesh: bpy.types.Mesh) -> None:
    pass


# TODO: Move to inline in P3D IO
def mesh_static_normals_iterator(
    mesh: bpy.types.Mesh
) -> Generator[tuple[int, Vector], None, None]:
    for i, normal_value in enumerate(mesh.corner_normals):
        yield i, normal_value.vector.copy().freeze()
