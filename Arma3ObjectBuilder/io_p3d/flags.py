# Helper functions to handle vertex and face flag values.


from .. import utils


flags_vertex_surface = {
    'NORMAL': 0x00000000,
    'SURFACE_ON': 0x00000001,
    'SURFACE_ABOVE': 0x00000002,
    'SURFACE_UNDER': 0x00000004,
    'KEEP_HEIGHT': 0x00000008
}


flags_vertex_fog = {
    'NORMAL': 0x00000000,
    'SKY': 0x00002000,
    'NONE': 0x00001000
}


flags_vertex_decal = {
    'NORMAL': 0x00000000,
    'DECAL': 0x00000100
}


flags_vertex_lighting = {
    'NORMAL': 0x00000000,
    'SHINING': 0x00000010,
    'SHADOW': 0x00000020,
    'LIGHTED_HALF': 0x00000080,
    'LIGHTED_FULL': 0x00000040
}


flags_vertex_normals = {
    'AREA': 0x00000000,
    'ANGLE': 0x04000000,
    'FIXED': 0x02000000
}


flag_vertex_hidden = 0x01000000


flags_face_lighting = {
    'NORMAL': 0x00000000,
    'BOTH': 0x00000020,
    'POSITION': 0x00000080,
    'FLAT': 0x00100000,
    'REVERSED': 0x00200000
}


flags_face_zbias = {
    'NONE': 0x00000000,
    'LOW': 0x00000100,
    'MIDDLE': 0x00000200,
    'HIGH': 0x00000300
}


flag_face_noshadow = 0x00000010
flag_face_merging = 0x01000000
flag_face_user_mask = 0xfe000000


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
        flag += flags_vertex_surface[props.surface]
        flag += flags_vertex_fog[props.fog]
        flag += flags_vertex_decal[props.decal]
        flag += flags_vertex_lighting[props.lighting]
        flag += flags_vertex_normals[props.normals]
        
        if props.hidden:
            flag += flag_vertex_hidden
        
        return flag


def get_flag_face(props):
        flag = 0
        flag += flags_face_lighting[props.lighting]
        flag += flags_face_zbias[props.zbias]
        
        if not props.shadow:
            flag += flag_face_noshadow
        
        if not props.merging:
            flag += flag_face_merging

        flag += (props.user << 25)
        
        return flag


def set_flag_vertex(props, value):        
        for name in flags_vertex_surface:
            if value & flags_vertex_surface[name]:
                props.surface = name
                break
                
        for name in flags_vertex_fog:
            if value & flags_vertex_fog[name]:
                props.fog = name
                break
                
        for name in flags_vertex_lighting:
            if value & flags_vertex_lighting[name]:
                props.lighting = name
                break
                
        for name in flags_vertex_decal:
            if value & flags_vertex_decal[name]:
                props.decal = name
                break
                
        for name in flags_vertex_normals:
            if value & flags_vertex_normals[name]:
                props.normals = name
                break
        
        if value & flag_vertex_hidden:
            props.hidden = True


def set_flag_face(props, value):
        for name in flags_face_lighting:
            if value & flags_face_lighting[name]:
                props.lighting = name
                break

        for name in flags_face_zbias:
            if value & flags_face_zbias[name]:
                props.zbias = name
                break
        
        if value & flag_face_noshadow:
            props.shadow = False
        
        if value & flag_face_merging:
            props.merging = False
        
        props.user = (value & flag_face_user_mask) >> 25


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
    group_count = len(obj.a3ob_properties_object_flags.vertex)
    with utils.edit_bmesh(obj) as bm:
        bm.verts.ensure_lookup_table()
        
        layer = get_layer_flags_vertex(bm)
        for vertex in bm.verts:
            value = vertex[layer]
            if value == group_id or (group_id == 0 and not (0 <= value < group_count)):
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
    group_count = len(obj.a3ob_properties_object_flags.face)
    with utils.edit_bmesh(obj) as bm:
        bm.faces.ensure_lookup_table()
        
        layer = get_layer_flags_face(bm)
        for face in bm.faces:
            value = face[layer]
            if value == group_id or (group_id == 0 and not (0 <= value < group_count)):
                face.select = select


def clear_groups_face(obj):
    with utils.edit_bmesh(obj) as bm:
        flag_props = obj.a3ob_properties_object_flags
        flag_props.face.clear()
        flag_props.face_index = -1

        clear_layer_flags_face(bm)
