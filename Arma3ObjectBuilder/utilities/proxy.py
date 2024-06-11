# Utility functions for proxy transformations,
# and proxy creation.


import bpy
import mathutils


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


def create_proxy():
    mesh = bpy.data.meshes.new("proxy")
    mesh.from_pydata([(0, 0, 0), (0, 0, 2), (0, 1, 0)], [], [(0, 1, 2)])
    mesh.update(calc_edges=True)
    
    obj = bpy.data.objects.new("proxy", mesh)
    obj.a3ob_properties_object_proxy.is_a3_proxy = True
    
    return obj
