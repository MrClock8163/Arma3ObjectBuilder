import mathutils
import re

import bpy
import bmesh

from .data import P3D_LOD_Resolution as LODRes
from .. import utils


ENUM_LOD_TYPES = tuple([(str(idx), name, desc) for idx, (name, desc) in LODRes.INFO_MAP.items()])


def clear_uvs(obj):
    uvs = [uv for uv in obj.data.uv_layers]

    while uvs:
        obj.data.uv_layers.remove(uvs.pop())


def clear_components(obj):
    re_component = re.compile("component\d+", re.IGNORECASE)
    vgroups = [group for group in obj.vertex_groups if re_component.match(group.name)]
    while vgroups:
        obj.vertex_groups.remove(vgroups.pop())


def create_selection(obj, selection):
    group = obj.vertex_groups.get(selection, None)
    if not group:
        group = obj.vertex_groups.new(name=selection.strip())

    group.add([vert.index for vert in obj.data.vertices], 1, 'REPLACE')


def cleanup_vertex_groups(obj):
    obj.update_from_editmode()
    
    removed = 0
    used_groups = {}
    for vert in obj.data.vertices:
        for group in vert.groups:
            group_index = group.group
            used_groups[group_index] = obj.vertex_groups[group_index]
    
    vgroups = [group for group in obj.vertex_groups]
    while vgroups:
        group = vgroups.pop()
        if group.index not in used_groups:
            obj.vertex_groups.remove(group)
            removed += 1
        
    return removed


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


def find_components(obj):
    obj.update_from_editmode()
    clear_components(obj)
    count_groups = len(obj.vertex_groups)

    component_verts, _, no_ignored = utils.get_closed_components(obj)
    with utils.edit_bmesh(obj) as bm:
        bm.verts.ensure_lookup_table()
        bm.verts.layers.deform.verify()
        layer = bm.verts.layers.deform.active

        for i, comp in enumerate(component_verts):
            for idx in comp:
                bm.verts[idx][layer][count_groups + i] = 1
        
    for i in range(len(component_verts)):
        obj.vertex_groups.new(name="Component%02d" % (i + 1))

    return len(component_verts), no_ignored


def find_components_convex_hull(obj):
    obj.update_from_editmode()
    clear_components(obj)
    count_groups = len(obj.vertex_groups)

    comp_verts, comp_tris = utils.get_loose_components(obj)
    with utils.edit_bmesh(obj) as bm:
        bm.verts.ensure_lookup_table()
        bm.verts.layers.deform.verify()
        layer = bm.verts.layers.deform.active
        
        comp_verts_bm = []
        for verts, tris in zip(comp_verts, comp_tris):
            if len(tris) < 2:
                continue

            comp_verts_bm.append([bm.verts[idx] for idx in verts])
        
        for i, verts in enumerate(comp_verts_bm):
            result = bmesh.ops.convex_hull(bm, input=verts, use_existing_faces=True)
            bmesh.ops.delete(bm, geom=result["geom_unused"] + result["geom_interior"])
            for vert in [e for e in result["geom"] if type(e) is bmesh.types.BMVert]:
                vert[layer][count_groups + i] = 1
    
    for i in range(len(comp_verts_bm)):
        obj.vertex_groups.new(name="Component%02d" % (i + 1))

    return len(comp_verts_bm)


def check_convexity(obj):
    obj.update_from_editmode()
    
    with utils.edit_bmesh(obj) as bm:
        count_concave = 0
        for edge in bm.edges:
            if edge.is_convex:
                continue

            face1 = edge.link_faces[0]
            face2 = edge.link_faces[1]
            dot = face1.normal.dot(face2.normal)
            
            if 0.9999 <= dot <=1.0001:
                continue
            
            edge.select_set(True)
            count_concave += 1
    
    return count_concave
