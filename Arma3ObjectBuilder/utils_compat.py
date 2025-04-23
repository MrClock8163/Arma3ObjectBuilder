# Helper functions to handle API compatibility issues between different versions of Blender


import bpy


bl_version = bpy.app.version


def call_operator_ctx(op, ctx = None, **kwargs):
    if not ctx:
        op(**kwargs)
        return
    
    op(ctx, **kwargs)


def mesh_auto_smooth(mesh):
    mesh.use_auto_smooth = True
    mesh.auto_smooth_angle = 3.141592654


def mesh_static_normals_iterator(mesh):
    mesh.calc_normals_split()
    for i, loop in enumerate(mesh.loops):
        yield i, loop.normal.copy().freeze()


# Blender 4.0.0 removed the traditional bpy.ops.xyz.xyz(ctx, **kwargs) type operator calling,
# and since the new temp_override method was only introduced late in the 3.x.x versions,
# to maintain compatibility with older releases, the operator call has to be version dependent
# https://developer.blender.org/docs/release_notes/4.0/python_api/#blender-operators-bpyops
if bl_version > (3, 6, 0):
    def call_operator_ctx(op, ctx = None, **kwargs):
        if not ctx:
            op(**kwargs)
            return

        with bpy.context.temp_override(**ctx):
            op(**kwargs)


# https://developer.blender.org/docs/release_notes/4.1/python_api/#breaking-changes
if bl_version >= (4, 1, 0):
    def mesh_auto_smooth(mesh):
        pass
    
    def mesh_static_normals_iterator(mesh):
        for i, normal_value in enumerate(mesh.corner_normals):
            yield i, normal_value.vector.copy().freeze()
