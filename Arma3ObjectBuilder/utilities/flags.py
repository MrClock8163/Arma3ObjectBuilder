# Helper functions to handle vertex and face flag values.


from . import data
from . import generic as utils


def get_layer_flags_vertex(bm, create = True):
    layer = bm.verts.layers.int.get("a3ob_flags_vertex")
    if not layer and create:
        layer = bm.verts.layers.int.new("a3ob_flags_vertex")
    
    return layer


def get_layer_flags_face(bm, create = True):
    layer = bm.faces.layers.int.get("a3ob_flags_face")
    if not layer and create:
        layer = bm.faces.layers.int.new("a3ob_flags_face")
    
    return layer


def clear_layer_flags_vertex(bm):
    layer = bm.verts.layers.int.get("a3ob_flags_vertex")
    if not layer:
        return

    bm.verts.layers.int.remove(layer)


def clear_layer_flags_face(bm):
    layer = bm.faces.layers.int.get("a3ob_flags_face")
    if not layer:
        return

    bm.faces.layers.int.remove(layer)


def get_flag_vertex(props):
        flag = 0
        flag += data.flags_vertex_surface[props.surface]
        flag += data.flags_vertex_fog[props.fog]
        flag += data.flags_vertex_decal[props.decal]
        flag += data.flags_vertex_lighting[props.lighting]
        flag += data.flags_vertex_normals[props.normals]
        
        if props.hidden:
            flag += data.flag_vertex_hidden
        
        return flag


def get_flag_face(props):
        flag = 0
        flag += data.flags_face_lighting[props.lighting]
        flag += data.flags_face_zbias[props.zbias]
        
        if not props.shadow:
            flag += data.flag_face_noshadow
        
        if not props.merging:
            flag += data.flag_face_merging

        flag += (props.user << 25)
        
        return flag


def set_flag_vertex(props, value):        
        for name in data.flags_vertex_surface:
            if value & data.flags_vertex_surface[name]:
                props.surface = name
                break
                
        for name in data.flags_vertex_fog:
            if value & data.flags_vertex_fog[name]:
                props.fog = name
                break
                
        for name in data.flags_vertex_lighting:
            if value & data.flags_vertex_lighting[name]:
                props.lighting = name
                break
                
        for name in data.flags_vertex_decal:
            if value & data.flags_vertex_decal[name]:
                props.decal = name
                break
                
        for name in data.flags_vertex_normals:
            if value & data.flags_vertex_normals[name]:
                props.normals = name
                break
        
        if value & data.flag_vertex_hidden:
            props.hidden = True


def set_flag_face(props, value):
        for name in data.flags_face_lighting:
            if value & data.flags_face_lighting[name]:
                props.lighting = name
                break

        for name in data.flags_face_zbias:
            if value & data.flags_face_zbias[name]:
                props.zbias = name
                break
        
        if value & data.flag_face_noshadow:
            props.shadow = False
        
        if value & data.flag_face_merging:
            props.merging = False
        
        props.user = (value & data.flag_face_user_mask) >> 25


def remove_group_vertex(obj, group_id):
    with utils.edit_bmesh(obj) as bm:
        bm.verts.ensure_lookup_table()
        layer = get_layer_flags_vertex(bm)
        for vertex in bm.verts:
            if vertex[layer] >= group_id:
                vertex[layer] -= 1


def assign_group_vertex(obj, group_id):
    with utils.edit_bmesh(obj) as bm:
        bm.verts.ensure_lookup_table()
        
        layer = get_layer_flags_vertex(bm)
        
        for vertex in bm.verts:
            if vertex.select:
                vertex[layer] = group_id


def select_group_vertex(obj, group_id, select = True):
    with utils.edit_bmesh(obj) as bm:
        bm.verts.ensure_lookup_table()
        
        layer = get_layer_flags_vertex(bm)
        
        for vertex in bm.verts:
            if vertex[layer] == group_id:
                vertex.select = select


def clear_groups_vertex(obj):
    with utils.edit_bmesh(obj) as bm:
        flag_props = obj.a3ob_properties_object_flags
        flag_props.vertex.clear()
        flag_props.vertex_index = -1

        clear_layer_flags_vertex(bm)


def remove_group_face(obj, group_id):
    with utils.edit_bmesh(obj) as bm:
        bm.verts.ensure_lookup_table()
        layer = get_layer_flags_vertex(bm)
        for vertex in bm.verts:
            if vertex[layer] >= group_id:
                vertex[layer] -= 1


def assign_group_face(obj, group_id):
    with utils.edit_bmesh(obj) as bm:
        bm.faces.ensure_lookup_table()
        
        layer = get_layer_flags_face(bm)
        
        for face in bm.faces:
            if face.select:
                face[layer] = group_id


def select_group_face(obj, group_id, select = True):
    with utils.edit_bmesh(obj) as bm:
        bm.faces.ensure_lookup_table()
        
        layer = get_layer_flags_face(bm)
        
        for face in bm.faces:
            if face[layer] == group_id:
                face.select = select


def clear_groups_face(obj):
    with utils.edit_bmesh(obj) as bm:
        flag_props = obj.a3ob_properties_object_flags
        flag_props.face.clear()
        flag_props.face_index = -1

        clear_layer_flags_face(bm)
