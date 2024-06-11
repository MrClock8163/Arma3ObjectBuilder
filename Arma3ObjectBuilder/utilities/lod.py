# Backend functions mainly used by the P3D I/O.


from . import data


def has_ngons(mesh):
    for face in mesh.polygons:
        if len(face.vertices) > 4:
            return True
    
    return False


def is_contiguous_mesh(bm):
        for edge in bm.edges:
            if not edge.is_contiguous:
                return False
                
        return True


def get_lod_name(index):
    return data.lod_info.get(index, data.lod_info[data.lod_unknown])[0]


def format_lod_name(index, resolution):
    if index in data.lod_has_resolution:
        return "%s %d" % (get_lod_name(index), resolution)
        
    return get_lod_name(index)
