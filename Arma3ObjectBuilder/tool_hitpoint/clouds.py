# Hit point cloud generation functions.


from itertools import product

import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def validate_references(source, target):
    if source or target:
        if source == target and source.users == 2:
            bpy.data.objects.remove(source)
            source, target = None, None
        else:
            if source and source.users == 1:
                bpy.data.objects.remove(source)
                source = None
            if target and target.users == 1:
                bpy.data.objects.remove(target)
                target = None
    
    return source, target


# The method is as proposed at https://salaivv.com/2023/04/12/point-inside-outside.
# If the closest point on the mesh is actually on an edge instead of a face, the
# method yields false positives. This chances of this *edge* case occurring
# can be mitigated by bevelling the edges of the mesh.
def is_inside(obj, point):
    result, closest, normal, _ = obj.closest_point_on_mesh(point)
    
    if not result:
        return False
    
    return (closest - point).dot(normal) > 0


def is_inside_raycast(bvh: BVHTree, origin, point):
    vec = (point - origin).normalized()
    incr = vec * 0.000001
    hits = 0
    while True:
        loc, _, idx, _ = bvh.ray_cast(point, vec)
        if idx is None:
            break
            
        hits += 1
        point = loc + incr

    return hits % 2 != 0


def create_selection(obj, selection):
    group = obj.vertex_groups.get(selection, None)
    if not group:
        group = obj.vertex_groups.new(name=selection.strip())

    group.add([vert.index for vert in obj.data.vertices], 1, 'REPLACE')


def calculate_grid(coord_min, coord_max, spacing):
    dim = coord_max - coord_min
    if dim < spacing:
        return (coord_min + dim/2, )
        
    count = int(dim // spacing)
    padding = (dim - spacing*count) / 2
    points = Vector.Linspace(coord_min + padding, coord_max - padding, count + 1)
    
    return points


def generate_hitpoints(operator, context):
    scene_props = context.scene.a3ob_hitpoint_generator
    
    source, target = validate_references(scene_props.source, scene_props.target)
    
    if not source or len(source.data.polygons) == 0:
        return
    
    if source.scale.x == 0 or source.scale.y == 0 or source.scale.z == 0:
        return
    
    source_object = source
        
    modifier_bevel = source_object.modifiers.new("A3OB_HitPointBevel", 'BEVEL')
    modifier_bevel.segments = 1
    modifier_bevel.width = 0.001
    modifier_bevel.limit_method = 'NONE'

    modifier_triangulate = source_object.modifiers.new("A3OB_HitPointTris", 'TRIANGULATE')

    source_object_eval = source_object.evaluated_get(context.evaluated_depsgraph_get())

    bbox = source_object_eval.bound_box
    scale = source_object_eval.scale
    
    point_min = bbox[0]
    point_max = bbox[6]

    points_x = calculate_grid(point_min[0], point_max[0], scene_props.spacing[0] / scale.x)
    points_y = calculate_grid(point_min[1], point_max[1], scene_props.spacing[1] / scale.y)
    points_z = calculate_grid(point_min[2], point_max[2], scene_props.spacing[2] / scale.z)

    bm = bmesh.new()

    for X in points_x:
        for Y in points_y:
            for Z in points_z:
                if is_inside(source_object_eval, Vector((X ,Y, Z))):
                    bm.verts.new((X, Y, Z))
                
    mesh = bpy.data.meshes.new("Point cloud")
    bm.to_mesh(mesh)
    bm.free()
    
    collection = source_object.users_collection
    
    if not target:
        target_object = bpy.data.objects.new("Point cloud", mesh)
        if len(collection) > 0:
            collection = collection[0]
        else:
            collection = context.scene.collection
        
        collection.objects.link(target_object)
    else:
        target_object = target
        target_object.data = mesh
        
    target_object.matrix_world = source_object.matrix_world
    target_object.modifiers.clear()

    source_object.modifiers.remove(modifier_triangulate)
    source_object.modifiers.remove(modifier_bevel)
    
    if scene_props.selection.strip() != "" and len(target_object.data.vertices) > 0:
        create_selection(target_object, scene_props.selection)


def generate_volume_grid(obj, spacing):
    obj_eval = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    bbox = obj_eval.bound_box
    scale = obj_eval.scale
    if scale.x == 0 or scale.y == 0 or scale.z == 0:
        return []

    point_min = bbox[0]
    point_max = bbox[6]

    points_x = calculate_grid(point_min[0], point_max[0], spacing[0] / scale.x)
    points_y = calculate_grid(point_min[1], point_max[1], spacing[1] / scale.y)
    points_z = calculate_grid(point_min[2], point_max[2], spacing[2] / scale.z)

    bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    points = product(points_x, points_y, points_z)
    inside = list(filter(lambda co: is_inside_raycast(bvh, obj.location, Vector(co)), points))

    return inside


def generate_volume_grid_tris(obj, tris, spacing):
    bbox = obj.bound_box
    mesh = obj.data
    scale = obj.scale
    if scale.x == 0 or scale.y == 0 or scale.z == 0:
        return []

    point_min = bbox[0]
    point_max = bbox[6]

    points_x = calculate_grid(point_min[0], point_max[0], spacing[0] / scale.x)
    points_y = calculate_grid(point_min[1], point_max[1], spacing[1] / scale.y)
    points_z = calculate_grid(point_min[2], point_max[2], spacing[2] / scale.z)

    verts = [v.co for v in mesh.vertices]
    bvh = BVHTree.FromPolygons(verts, [tri.vertices for tri in tris])
    points = product(points_x, points_y, points_z)
    inside = list(filter(lambda co: is_inside_raycast(bvh, obj.location, Vector(co)), points))

    return inside
