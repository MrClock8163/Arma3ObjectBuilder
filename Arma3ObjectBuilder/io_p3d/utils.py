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
