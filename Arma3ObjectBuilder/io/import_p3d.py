# Processing functions to import multiple LODs as meshes
# from the MLOD P3D format. The actual file handling is implemented
# in the data_p3d module.


import math
import time
import os

import bpy
import bmesh
import mathutils

from . import data_p3d as p3d
from ..utilities import generic as utils
from ..utilities import lod as lodutils
from ..utilities import compat as computils
from ..utilities import proxy as proxyutils
from ..utilities import flags as flagutils
from ..utilities import structure as structutils
from ..utilities import data
from ..utilities.logger import ProcessLogger


def categorize_lods(operator, context, mlod):
    categories = {}
    lods = []

    root = context.scene.collection
    if operator.enclose:
        root = bpy.data.collections.new(name=os.path.basename(operator.filepath))
        bpy.context.scene.collection.children.link(root)
    
    if operator.groupby == 'NONE':
        categories["None"] = [0, root]
        lods = [[*lodutils.get_lod_id(lod.resolution), 0] for lod in mlod.lods]

    else:
        for lod in mlod.lods:
            lod_index, lod_resolution = lodutils.get_lod_id(lod.resolution)
            group_dict = data.lod_groups[operator.groupby]
            group_name = group_dict[lod_index]

            if group_name not in categories:
                new_category = bpy.data.collections.new(name=group_name)
                root.children.link(new_category)
                categories[group_name] = [len(categories), new_category]
            
            lods.append([lod_index, lod_resolution, categories[group_name][0]])

    return [cat[1] for cat in categories.values()], lods


def create_blender_materials(lookup):
    materials = []
    
    for texture, material in lookup.keys():
        material_name = "P3D: %s :: %s" % (os.path.basename(texture), os.path.basename(material))
        if texture == "" and material == "":
            material_name = "P3D: no material"
            
        new_mat = bpy.data.materials.new(material_name)
        new_mat.a3ob_properties_material.from_p3d(texture.strip(), material.strip())
        materials.append(new_mat)
        
    return materials


def process_normals(mesh, lod):
    loop_normals = lod.loop_normals()
    
    if len(mesh.loops) == len(loop_normals):
        mesh.normals_split_custom_set(loop_normals)
        return True

    return False


def process_sharps(bm, lod):
    data = None
    for tagg in lod.taggs:
        if tagg.name == "#SharpEdges#":
            data = tagg.data
            break
    
    if not data:
        return
    
    for edge in bm.edges:
        edge.smooth = True
    
    for item in data.edges:
        edge = bm.edges.get([bm.verts[item[0]], bm.verts[item[1]]])
        if edge:
            edge.smooth = False


def process_uvsets(bm, lod):
    uvsets = lod.uvsets()
        
    for idx in uvsets:
        uvs = uvsets[idx]
        layer_name = "UVSet %d" % idx
        layer = bm.loops.layers.uv.get(layer_name)
        if not layer:
            layer = bm.loops.layers.uv.new(layer_name) 
        
        for face in bm.faces:
            for loop in face.loops:
                loop[layer].uv = uvs[loop.index]
    
    return len(uvsets)


def process_selections(bm, lod):
    bm.verts.layers.deform.verify()
    layer = bm.verts.layers.deform.active
    
    selection_names = []
    count_selections = 0
    for tagg in lod.taggs:
        if tagg.name[0] == tagg.name[-1] == "#":
            continue
        
        weights = tagg.data.weight_verts
        for idx in weights:
            bm.verts[idx][layer][count_selections] = weights[idx]

        count_selections += 1
        
        selection_names.append(tagg.name)
    
    return selection_names


def process_materials(mesh, bm, lod, materials, materials_lookup):
    face_indices, material_indices = lod.get_sections(materials_lookup)
    
    for i, idx in enumerate(face_indices):
        bm.faces[i].material_index = idx
    
    for idx in material_indices:
        mesh.materials.append(materials[idx])


def process_mass(bm, lod):
    data = None
    for tagg in lod.taggs:
        if tagg.name == "#Mass#":
            data = tagg.data
    
    if not data:
        return
    
    layer = bm.verts.layers.float.new("a3ob_mass")
    for vert in bm.verts:
        vert[layer] = data.masses[vert.index]


def process_properties(obj, lod):
    for tagg in lod.taggs:
        if tagg.name != "#Property#":
            continue
        
        new_prop = obj.a3ob_properties_object.properties.add()
        new_prop.name = tagg.data.key
        new_prop.value = tagg.data.value


def process_flag_groups_vertex(obj, bm, lod):
    groups, values = lod.flag_groups_vertex()

    layer = flagutils.get_layer_flags_vertex(bm)
    for vert in bm.verts:
        vert[layer] = values[vert.index]
    
    for i, grp in enumerate(groups):
        new_group = obj.a3ob_properties_object_flags.vertex.add()
        new_group.name = ("Group %d" % i if i > 0 else "Default")
        new_group.set_flag(grp)


def process_flag_groups_face(obj, bm, lod):
    groups, values = lod.flag_groups_face()

    layer = flagutils.get_layer_flags_face(bm)
    for face in bm.faces:
        face[layer] = values[face.index]
    
    for i, grp in enumerate(groups):
        new_group = obj.a3ob_properties_object_flags.face.add()
        new_group.name = ("Group %d" % i if i > 0 else "Default")
        new_group.set_flag(grp)


# Align the object coordinate system with the proxy coordinates.
# https://mrcmodding.gitbook.io/home/documents/proxy-coordinates
def transform_proxy(obj):
    rotation_matrix = proxyutils.get_transform_rotation(obj)
    obj.data.transform(rotation_matrix)
    obj.matrix_world @= rotation_matrix.inverted()
    
    translate = mathutils.Matrix.Translation(-proxyutils.find_axis_vertices(obj.data)[0].co)
    obj.data.transform(translate)
    obj.matrix_world @= translate.inverted()
    
    obj.data.update()


def process_proxies(operator, obj, proxy_lookup, empty_material):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')

    for key in proxy_lookup:
        vgroup = obj.vertex_groups.get(key)
        if not vgroup:
            continue
            
        obj.vertex_groups.active = vgroup
        computils.call_operator_ctx(bpy.ops.object.vertex_group_select)

        try:
            bpy.ops.mesh.separate(type='SELECTED')
            obj.vertex_groups.remove(vgroup)
        except:
            pass

    bpy.ops.object.mode_set(mode='OBJECT')
        
    proxy_objects = [proxy for proxy in bpy.context.selected_objects if proxy != obj]
        
    bpy.ops.object.select_all(action='DESELECT')
    
    if operator.proxy_action == 'CLEAR':
        computils.call_operator_ctx(bpy.ops.object.delete, {"selected_objects": proxy_objects})

    elif operator.proxy_action == 'SEPARATE':
        for i, proxy_obj in enumerate(proxy_objects):
            proxy_obj.a3ob_properties_object.is_a3_lod = False

            transform_proxy(proxy_obj)
            structutils.cleanup_vertex_groups(proxy_obj) # need to remove the unused groups leftover from the separation

            vgroup = proxy_obj.vertex_groups.get("@proxy_%d" % i)
            if not vgroup:
                continue
            
            path, index = proxy_lookup[vgroup.name]
            proxy_obj.vertex_groups.remove(vgroup)
            proxy_obj.a3ob_properties_object_proxy.proxy_path = utils.restore_absolute(path, ".p3d")
            proxy_obj.a3ob_properties_object_proxy.proxy_index = index

            proxy_obj.a3ob_properties_object_flags.vertex.clear()
            proxy_obj.a3ob_properties_object_flags.face.clear()

            bm = bmesh.new()
            bm.from_mesh(proxy_obj.data)

            flagutils.clear_layer_flags_vertex(bm)
            flagutils.clear_layer_flags_face(bm)

            bm.to_mesh(proxy_obj.data)
            bm.free()

            proxy_obj.a3ob_properties_object_proxy.is_a3_proxy = True
            proxy_obj.data.materials.clear()
            proxy_obj.data.materials.append(empty_material)
            proxy_obj.parent = obj
            name = "proxy: %s" % proxy_obj.a3ob_properties_object_proxy.get_name()
            proxy_obj.name = name
            proxy_obj.data.name = name


def process_lod(operator, logger, lod, materials, materials_lookup, categories, lod_links):
    logger.level_up()

    lod_index = lod_links[0]
    lod_resolution = lod_links[1]
    lod_name = lodutils.format_lod_name(lod_index, lod_resolution)

    logger.step("File report:")
    logger.log("Name: %s" % lod_name)
    logger.log("Signature: %d" % lod.resolution)
    logger.log("Type: P3DM")
    logger.log("Version: 28.256")
    logger.log("Vertices: %d" % len(lod.verts))
    logger.log("Normals: %d" % len(lod.normals))
    logger.log("Faces: %d" % len(lod.faces))
    logger.log("Taggs: %d" % (len(lod.taggs) + 1))

    logger.step("Processing data:")
    
    mesh = bpy.data.meshes.new(lod_name)
    mesh.use_auto_smooth = True
    mesh.auto_smooth_angle = math.radians(180)
    
    mesh.from_pydata(*lod.pydata())
    mesh.update(calc_edges=True)
    
    obj = bpy.data.objects.new(lod_name, mesh)

    logger.log("Created raw mesh")

    # Setup LOD properties
    object_props = obj.a3ob_properties_object
    try:
        object_props.lod = str(lod_index)
    except:
        object_props.lod = "30"
        
    object_props.resolution = lod_resolution

    
    for face in mesh.polygons:
        face.use_smooth = True
    
    if 'NORMALS' in operator.additional_data:
        if process_normals(mesh, lod):
            logger.log("Applied split normals")
        else:
            logger.log("Could not apply split normals")
    
    # Process TAGGs
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    
    process_sharps(bm, lod)
    logger.log("Marked sharp edges")
    
    if 'UV' in operator.additional_data:
        count_uv = process_uvsets(bm, lod)
        logger.log("Added UV channels: %d" % count_uv)
    
    selection_names = []
    proxy_lookup = {}
    if 'SELECTIONS' in operator.additional_data:
        proxy_lookup = lod.proxies_to_placeholders()
        selection_names = process_selections(bm, lod)
        logger.log("Added vertex groups: %d" % (len(selection_names)))
    
    if 'MATERIALS' in operator.additional_data:
        process_materials(mesh, bm, lod, materials, materials_lookup)
        logger.log("Assigned materials")
    
    if 'MASS' in operator.additional_data:
        process_mass(bm, lod)
        logger.log("Added vertex masses")
    
    process_properties(obj, lod)
    logger.log("Added named properties")

    process_flag_groups_vertex(obj, bm, lod)
    logger.log("Assigned vertex flag groups")

    process_flag_groups_face(obj, bm, lod)
    logger.log("Assigned face flag groups")
        
    for name in selection_names:
        obj.vertex_groups.new(name=name)

    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()

    collection = categories[lod_links[2]]
    collection.objects.link(obj)

    if operator.validate_meshes:
        mesh.validate(clean_customdata=False)

    if operator.proxy_action != 'NOTHING' and 'SELECTIONS' in operator.additional_data:
        process_proxies(operator, obj, proxy_lookup, materials[0])
        logger.log("Processed proxies: %d" % len(proxy_lookup))

    object_props.is_a3_lod = True

    logger.level_down()

    return obj


def read_file(operator, context, file):
    # If something is left selected in the scene, the proxy separation trips up with the operators.
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
        
    context.view_layer.objects.active = None

    wm = context.window_manager
    wm.progress_begin(0, 1000)
    wm.progress_update(0)
    logger = ProcessLogger()
    logger.step("P3D import from %s" % operator.filepath)

    time_file_start = time.time()

    if operator.first_lod_only:
        logger.log("Importing 1st LOD only")
    
    time_read_start = time.time()
    mlod = p3d.P3D_MLOD.read(file, operator.first_lod_only)
    logger.log("File reading done in %f sec" % (time.time() - time_read_start))

    logger.log("File version: %d" % mlod.version)
    logger.log("Number of read LODs: %d" % len(mlod.lods))
    
    categories, lod_links = categorize_lods(operator, context, mlod)

    if not operator.additional_data_allowed:
        operator.additional_data = set()
    
    materials = None
    materials_lookup = None
    if 'MATERIALS' in operator.additional_data:
        materials_lookup = mlod.get_materials()
        materials = create_blender_materials(materials_lookup)
        logger.log("Number of unique materials: %d" % len(materials))
    
    logger.log("Processing mesh data:")
    logger.level_up()

    lod_objects = []
    for i, lod in enumerate(mlod.lods):
        time_lod_start = time.time()
        logger.step("LOD %d" % (i + 1))

        lod_objects.append(process_lod(operator, logger, lod, materials, materials_lookup, categories, lod_links[i]))

        logger.log("Done in %f sec" % (time.time() - time_lod_start))
        wm.progress_update(i + 1)

    logger.level_down()

    print("P3D import finished in %f sec" % (time.time() - time_file_start))
    
    return lod_objects