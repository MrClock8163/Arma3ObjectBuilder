# Backend functions of the rigging painting tools.


import bpy

from . import generic as utils


# It's easier to prepare a list of the vertex group indices that
# correspond to bones defined in the model.cfg, than to try matching
# everything by name every time.
def get_bone_group_indices(obj, cfgbones):
    cfgbones_names = [item.name.lower() for item in cfgbones]    
    return [group.index for group in obj.vertex_groups if group.name.lower() in cfgbones_names]


def select_vertices_unnormalized(obj, bone_indices):
    with utils.edit_bmesh(obj) as bm:
        bm.verts.ensure_lookup_table()
        deform = bm.verts.layers.deform.verify()
        
        for vert in bm.verts:
            weights = 0
            for key in vert[deform].keys():
                if key not in bone_indices:
                    continue
                
                weights += vert[deform][key]
            
            vert.select_set(abs(weights-1) > 0.01)


def normalize_weights(obj, bone_indices):
    with utils.edit_bmesh(obj) as bm:
        deform = bm.verts.layers.deform.verify()
        bm.verts.ensure_lookup_table()
        
        normalized = 0
        for vert in bm.verts:
            weights = 0
            for key in vert[deform].keys():
                if key not in bone_indices:
                    continue
                
                weights += vert[deform][key]
                
            if abs(weights-1) > 0.01:
                normalized += 1
            
            for key in vert[deform].keys():
                if key not in bone_indices:
                    continue
                
                vert[deform][key] /= weights
    
    return normalized


def select_vertices_overdetermined(obj, bone_indices):
    with utils.edit_bmesh(obj) as bm:
        bm.verts.ensure_lookup_table()
        deform = bm.verts.layers.deform.verify()
        
        for vert in bm.verts:
            bones = 0
            for key in vert[deform].keys():
                if key not in bone_indices:
                    continue
                
                bones += 1
            
            vert.select_set(bones > 4)


# If a vertex has overdetermined weighting (more than 4 bones affecting it),
# we might want to prune the excess bones. For each vertex of the mesh,
# the weights of bone selections are summed up, and the groups are sorted.
# Only the groups with the top 4 influence sum are left, rest are removed.
def prune_overdetermined(obj, bone_indices):
    with utils.edit_bmesh(obj) as bm:
        bm.verts.ensure_lookup_table()
        deform = bm.verts.layers.deform.verify()
        
        pruned = 0
        for vert in bm.verts:
            bones = []
            sections = []
            for key in vert[deform].keys():
                if key not in bone_indices:
                    sections.append((key, vert[deform][key]))
                    continue
                
                bones.append((key, vert[deform][key]))
            
            if len(bones) <= 4:
                continue
            
            pruned += 1
            bones.sort(reverse=True, key=lambda item: item[1])
            
            vert[deform].clear()
            for id, weight in (bones[0:4] + sections):
                vert[deform][id] = weight
    
    return pruned


# Weights are summed for every group for every vertex. Then all groups
# are removed, and only those readded that are above the threshold.
def prune_weights(obj, threshold):
    with utils.edit_bmesh(obj) as bm:
        bm.verts.ensure_lookup_table()
        deform = bm.verts.layers.deform.verify()
        
        pruned = 0
        for vert in bm.verts:
            weights = []
            for key in vert[deform].keys():
                if vert[deform][key] > threshold:
                    weights.append((key, vert[deform][key]))
            
            if len(vert[deform].keys()) > len(weights):
                pruned += 1
            
            vert[deform].clear()
            for id, weight in weights:
                vert[deform][id] = weight

    return pruned


def cleanup(obj, bone_indices, threshold):
    verts_prune_selection = prune_weights(obj, threshold)
    verts_prune_overdetermined = prune_overdetermined(obj, bone_indices)
    verts_normalized = normalize_weights(obj, bone_indices)
    
    return max(verts_prune_selection, verts_prune_overdetermined, verts_normalized)


def bones_from_armature(obj):
    return [(bone.name, bone.parent.name if bone.parent else "") for bone in obj.pose.bones]


def bone_order_from_skeleton(skeleton):
    if len(skeleton.bones) == 0:
        return {}
    
    if len({bone.name.lower() for bone in skeleton.bones}) != len(skeleton.bones):
        return None

    bones = {}
    for bone in skeleton.bones:
        if bone.parent != "" and bone.parent not in bones:
            return None
        
        bones[bone.name] = bone.parent
    
    return bones
    

def pivots_from_armature(obj, bones_parents):    
    bone_map = {item.lower(): item for item in bones_parents}

    mesh = bpy.data.meshes.new("%s pivots" % obj.name)
    pivots = bpy.data.objects.new("%s pivots" % obj.name, mesh)
    pivots.matrix_world = obj.matrix_world

    pivots_coords = {}
    for bone in obj.data.bones:
        if bone.name.lower() not in bone_map:
            continue
        
        pivots_coords[bone_map[bone.name.lower()]] = tuple(bone.head_local)

    mesh.from_pydata(list(pivots_coords.values()), [], [])

    for i, item in enumerate(pivots_coords):
        group = pivots.vertex_groups.new(name=item)
        group.add([i], 1, 'REPLACE')
    
    pivots_props = pivots.a3ob_properties_object
    pivots_props.lod = '9'
    pivots_props.is_a3_lod = True

    prop = pivots_props.properties.add()
    prop.name = "autocenter"
    prop.value = "0"

    return pivots
