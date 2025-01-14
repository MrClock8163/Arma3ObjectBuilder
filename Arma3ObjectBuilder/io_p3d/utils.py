import mathutils

import bpy

from .data import P3D_LOD_Resolution as LODRes


ENUM_LOD_TYPES = tuple([(str(idx), name, desc) for idx, (name, desc) in LODRes.INFO_MAP.items()])


def clear_uvs(obj):
    uvs = [uv for uv in obj.data.uv_layers]

    while uvs:
        obj.data.uv_layers.remove(uvs.pop())


def create_selection(obj, selection):
    group = obj.vertex_groups.get(selection, None)
    if not group:
        group = obj.vertex_groups.new(name=selection.strip())

    group.add([vert.index for vert in obj.data.vertices], 1, 'REPLACE')


def create_proxy():
    mesh = bpy.data.meshes.new("proxy")
    mesh.from_pydata([(0, 0, 0), (0, 0, 2), (0, 1, 0)], [], [(0, 1, 2)])
    mesh.update(calc_edges=True)
    
    obj = bpy.data.objects.new("proxy", mesh)
    obj.a3ob_properties_object_proxy.is_a3_proxy = True
    
    return obj


def find_axis_vertices(mesh):
    vert0 = (mesh.vertices[0], (mesh.vertices[1].co - mesh.vertices[0].co).angle(mesh.vertices[2].co - mesh.vertices[0].co))
    vert1 = (mesh.vertices[1], (mesh.vertices[0].co - mesh.vertices[1].co).angle(mesh.vertices[2].co - mesh.vertices[1].co))
    vert2 = (mesh.vertices[2], (mesh.vertices[0].co - mesh.vertices[2].co).angle(mesh.vertices[1].co - mesh.vertices[2].co))
        
    verts = [vert0, vert1, vert2]
    verts.sort(reverse=True, key=lambda vert: vert[1])
        
    return verts[0][0], verts[1][0], verts[2][0]


# https://mrcmodding.gitbook.io/home/documents/proxy-coordinates
def get_transform_rotation(obj):
    vert_center, vert_y, vert_z = find_axis_vertices(obj.data)
    
    y = (vert_y.co - vert_center.co).normalized()
    z = (vert_z.co - vert_center.co).normalized()
    x = y.cross(z).normalized()
    z = x.cross(y).normalized()
    
    return mathutils.Matrix(((*x , 0), (*y, 0), (*z, 0), (0, 0, 0, 1)))
