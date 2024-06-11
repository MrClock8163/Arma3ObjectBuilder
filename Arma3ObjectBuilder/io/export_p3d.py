# Processing functions to export multiple meshed as LODs
# to the MLOD P3D format. The actual file handling is implemented
# in the data_p3d module.


import time
import re
from contextlib import contextmanager

import bpy
import bmesh

from . import data_p3d as p3d
from ..utilities import generic as utils
from ..utilities import flags as flagutils
from ..utilities import compat as computils
from ..utilities import structure as structutils
from ..utilities import data
from ..utilities.logger import ProcessLogger, ProcessLoggerNull
from ..utilities.validator import Validator


# Simple check to not even start the export if there are
# no LOD objects in the scene.
def can_export(operator, context):
    scene = context.scene
    export_objects = scene.objects
    
    if operator.use_selection:
        export_objects = context.selected_objects
        
    for obj in export_objects:
        if (not operator.visible_only or obj.visible_get()) and  obj.type == 'MESH' and obj.a3ob_properties_object.is_a3_lod and obj.parent == None:
            return True
            
    return False


def create_temp_collection(context):
    temp = bpy.data.collections.get("A3OB_temp")
    if temp is None:
        temp = bpy.data.collections.new("A3OB_temp")
        context.scene.collection.children.link(temp)
    
    objects = [obj for obj in temp.objects]
    while objects:
        bpy.data.objects.remove(objects.pop())
    
    return temp


def cleanup_temp_collection(temp):    
    temp_objects = [obj for obj in temp.objects]
    while temp_objects:
        bpy.data.meshes.remove(temp_objects.pop().data)

    bpy.data.collections.remove(temp)


def is_ascii(value):
    try:
        value.encode('ascii')
        return True
    except:
        return False


def duplicate_object(obj, temp_collection):
    new_object = obj.copy()
    new_object.data = obj.data.copy()
    new_object["a3ob_original_object"] = obj.get("a3ob_original_object", obj.name)
    temp_collection.objects.link(new_object)
    return new_object


# May be worth looking into bpy.ops.object.convert(target='MESH')
# instead to reduce operator calls.
def apply_modifiers(obj):
    ctx = {"object": obj}
    
    modifiers = [m for m in obj.modifiers if m.show_viewport]
    while modifiers:
        m = modifiers.pop(0)
        try:
            ctx["modifier"] = m
            computils.call_operator_ctx(bpy.ops.object.modifier_apply, ctx, modifier= m.name)
        except:
            obj.modifiers.remove(m)


def apply_transforms(obj):
    ctx = {
        "object": obj,
        "active_object": obj,
        "selected_editable_objects": [obj],
        "edit_object": None
    }
    computils.call_operator_ctx(bpy.ops.object.transform_apply, ctx)


# In order to simplify merging the LOD parts, and the data access later on, the dereferenced
# flags need to be written directly into their respective integer bmesh layers.
def bake_flags_vertex(obj):
    with utils.edit_bmesh(obj) as bm:
        bm.verts.ensure_lookup_table()

        default_flag = utils.get_addon_preferences().flag_vertex

        layer = flagutils.get_layer_flags_vertex(bm)
        flags_vertex = {i: item.get_flag() for i, item in enumerate(obj.a3ob_properties_object_flags.vertex)}
        if len(flags_vertex) > 0:
            for vert in bm.verts:
                vert[layer] = flags_vertex.get(vert[layer], default_flag)
        else:
            for vert in bm.verts:
                vert[layer] = default_flag


def bake_flags_face(obj):
    with utils.edit_bmesh(obj) as bm:
        bm.faces.ensure_lookup_table()

        default_flag = utils.get_addon_preferences().flag_face

        layer = flagutils.get_layer_flags_face(bm)
        flags_face = {i: item.get_flag() for i, item in enumerate(obj.a3ob_properties_object_flags.face)}
        if len(flags_face) > 0:
            for face in bm.faces:
                face[layer] = flags_face.get(face[layer], default_flag)
        else:
            for face in bm.faces:
                face[layer] = default_flag


def blank_flags_vertex(obj):
    with utils.edit_bmesh(obj) as bm:
        bm.verts.ensure_lookup_table()
        layer = flagutils.get_layer_flags_vertex(bm)

        for vert in bm.verts:
            vert[layer] = 0


def blank_flags_face(obj):
    with utils.edit_bmesh(obj) as bm:
        bm.faces.ensure_lookup_table()
        layer = flagutils.get_layer_flags_face(bm)

        for face in bm.faces:
            face[layer] = 0


# The sub-objects and proxy object need to be merged into the main LOD object after some
# preprocessing. The proxy selections need to be created with placeholder names, the flags
# need to be baked into the respective layers, and the modifiers have to get applied.
def merge_sub_objects(operator, main_obj, sub_objects):
    all_objects = sub_objects + [main_obj]

    # To simplify the object merging, the face and vertex flags need to be directly written
    # into their layers. This way the process doesn't have to deal with managing and merging
    # flag groups on the different component objects.
    for obj in all_objects:
        bake_flags_vertex(obj)
        bake_flags_face(obj)

        if operator.apply_modifiers:
            apply_modifiers(obj)
    
    if len(all_objects) > 1:
        ctx = {
            "active_object": main_obj,
            "selected_objects": all_objects,
            "selected_editable_objects": all_objects
        }
        computils.call_operator_ctx(bpy.ops.object.join, ctx)


def merge_proxy_objects(main_obj, proxy_objects, relative):
    # Blender has a 63 character length limit on vertex group names,
    # so the proxy paths can't be written to the group name directly,
    # a placeholder name must be used, and added to a lookup dictionary.
    proxy_lookup = {}
    for i, proxy in enumerate(proxy_objects):
        for face in proxy.data.polygons:
            face.use_smooth = False

        placeholder = "@proxy_%d" % i
        utils.create_selection(proxy, placeholder)
        proxy_lookup[placeholder] = proxy.a3ob_properties_object_proxy.to_placeholder(relative)

        utils.clear_uvs(proxy)

    all_objects = proxy_objects + [main_obj]
    for obj in proxy_objects:
        blank_flags_face(obj)
        blank_flags_vertex(obj)

    if len(all_objects) > 1:
        ctx = {
            "active_object": main_obj,
            "selected_objects": all_objects,
            "selected_editable_objects": all_objects
        }
        computils.call_operator_ctx(bpy.ops.object.join, ctx)

    return proxy_lookup


def validate_proxies(operator, proxy_objects):
    for proxy in proxy_objects:
        if len(proxy.data.polygons) != 1 or len(proxy.data.polygons[0].vertices) != 3:
            return False

        path, _ = proxy.a3ob_properties_object_proxy.to_placeholder(operator.relative_paths)
        if not is_ascii(path):
            return False
        
        for group in proxy.vertex_groups:
            if not is_ascii(group.name):
                return False
        
        for slot in proxy.material_slots:
            mat = slot.material
            if not mat:
                continue
            
            texture, material = mat.a3ob_properties_material.to_p3d(operator.relative_paths)
            if not is_ascii(texture) or not is_ascii(material):
                return False
    
    return True


def get_sub_objects(obj, temp_collection):
    sub_objects = []
    proxy_objects = []
    for child in obj.children:
        if child.type != 'MESH':
            continue
            
        if not child.mode == 'OBJECT':
            computils.call_operator_ctx(bpy.ops.object.mode_set, {"active_object": child}, mode='OBJECT')
        
        child_copy = duplicate_object(child, temp_collection)

        if child_copy.a3ob_properties_object_proxy.is_a3_proxy:
            proxy_objects.append(child_copy)
        else:
            sub_objects.append(child_copy)
    
    return sub_objects, proxy_objects


def sort_sections(obj):
    sections = {0: []}
    for i in range(len(obj.material_slots)):
        sections[i] = []

    with utils.edit_bmesh(obj) as bm:
        bm.faces.ensure_lookup_table()

        for face in bm.faces:
            sections.get(face.material_index, sections[0]).append(face)
        
        face_index = 0
        for section in sections.values():
            for face in section:
                face.index = face_index
                face_index -=- 1

        bm.faces.sort()


def cleanup_uvs(obj):
    if int(obj.a3ob_properties_object.lod) not in data.lod_allow_uvs:
        utils.clear_uvs(obj)


def cleanup_normals(operator, obj):
    if not operator.preserve_normals or int(obj.a3ob_properties_object.lod) not in data.lod_visuals:
        ctx = {
            "active_object": obj,
            "object": obj
        }
        computils.call_operator_ctx(bpy.ops.mesh.customdata_custom_splitnormals_clear, ctx)
        computils.mesh_auto_smooth(obj.data)
        mod = obj.modifiers.new("Temp", 'WEIGHTED_NORMAL')
        mod.weight = 50
        mod.keep_sharp = True
        apply_modifiers(obj)


def generate_components(operator, obj):
    if not operator.generate_components or int(obj.a3ob_properties_object.lod) not in data.lod_geometries:
        return
    
    re_component = re.compile(r"component\d+", re.IGNORECASE)
    for group in obj.vertex_groups:
        if re_component.match(group.name):
            return
    
    structutils.find_components(obj)


# Needed to get around the validator requiring component## selections. If the
# option to generate the components is enabled in the export, the selections
# might not yet be there, so the validation would fail. A dummy component is
# added temporarily in this case to satisfy the validator.
@contextmanager
def temporary_component(operator, obj):
    temporary_component = None
    try:
        if operator.generate_components:
            temporary_component = obj.vertex_groups.new(name="Component00")
        yield obj
    finally:
        if temporary_component:
            obj.vertex_groups.remove(temporary_component)


# Huge monolith function to produce the final object and mesh data that can be written to the 
# P3D file. Merges the sub-objects and proxies into the main objects, applies transformations,
# runs mesh validation and sorts sections if necessary. Also processes the LOD copy directives.
# [(LOD object 0, proxy lookup 0), (..., ....), ....]
def get_lod_data(operator, context, validator, temp_collection):
    scene = context.scene
    export_objects = scene.objects

    if operator.use_selection:
        export_objects = context.selected_objects

    lod_list = []

    for obj in [obj for obj in export_objects if not operator.visible_only or obj.visible_get()]:       
        if obj.type != 'MESH' or not obj.a3ob_properties_object.is_a3_lod or obj.parent != None:
            continue
            
        # Some operator polls fail later if an object is in edit mode.
        if not obj.mode == 'OBJECT':
            computils.call_operator_ctx(bpy.ops.object.mode_set, {"active_object": obj}, mode='OBJECT')
        
        main_obj = duplicate_object(obj, temp_collection)
        is_valid = True

        sub_objects, proxy_objects = get_sub_objects(obj, temp_collection)
        
        # Merging of the components has to be done in two steps (1st: sub-objects, 2nd: proxies), because the LOD
        # validation would otherwise get confused by the proxy triangles (eg.: it'd be impossible to validate
        # that a mesh is otherwise contiguous or not).
        merge_sub_objects(operator, main_obj, sub_objects)
        is_valid = validate_proxies(operator, proxy_objects)

        is_valid_copies = []
        for copy in main_obj.a3ob_properties_object.copies:
            with temporary_component(operator, main_obj):
                is_valid_copies.append(is_valid and validator.validate_lod(main_obj, copy.lod, True, operator.validate_lods_warning_errors, operator.relative_paths))

        with temporary_component(operator, main_obj):
            is_valid &= validator.validate_lod(main_obj, main_obj.a3ob_properties_object.lod, True, operator.validate_lods_warning_errors, operator.relative_paths)

        proxy_lookup = merge_proxy_objects(main_obj, proxy_objects, operator.relative_paths)

        if operator.apply_transforms:
            apply_transforms(main_obj)
        
        if operator.validate_meshes:
            main_obj.data.validate(clean_customdata=False)

        # Sections are important for in-game performace, and should be sorted during export
        # to avoid any unnecessary fragmentation. Some info about sections can be found on the
        # community wiki: https://community.bistudio.com/wiki/Section_Count.
        # Some corrections: https://mrcmodding.gitbook.io/home/documents/sections.
        if operator.sort_sections:
            sort_sections(main_obj)
        
        for copy, is_valid_copy in zip(main_obj.a3ob_properties_object.copies, is_valid_copies):
            main_obj_copy = duplicate_object(main_obj, temp_collection)
            copy_props = main_obj_copy.a3ob_properties_object
            copy_props.lod = copy.lod
            copy_props.resolution = copy.resolution
            copy_props.resolution_float = copy.resolution_float

            cleanup_uvs(main_obj_copy)
            cleanup_normals(operator, main_obj_copy)
            generate_components(operator, main_obj_copy)
            lod_list.append((main_obj_copy, proxy_lookup, is_valid_copy))
            
        cleanup_uvs(main_obj)
        cleanup_normals(operator, main_obj)
        generate_components(operator, main_obj)
        lod_list.append((main_obj, proxy_lookup, is_valid))

    return lod_list


# Produce the vertex dictionary from the bmesh data.
# {idx 0: (x, y, z, flag), ...: (..., ..., ..., ...), ...}
def process_vertices(bm):
    layer = flagutils.get_layer_flags_vertex(bm)

    output = {}

    for vert in bm.verts:
        output[vert.index] = (*vert.co, vert[layer])

    return output


# Produce the unique vertex normal dictionary from the bmesh data, as well as a mapping
# dictionary.
# {idx 0: (x, y, z), ...: (..., ..., ...), ....}
# {loop idx 0: normal idx X, loop idx 1: normal idx Y, ...}
def process_normals(mesh):
    output = {}
    normals_index = {}
    normals_lookup_dict = {}
    
    for i, normal in computils.mesh_static_normals_iterator(mesh):
        if normal not in normals_index:
            normals_index[normal] = len(normals_index)
            output[len(output)] = normal
        
        normals_lookup_dict[i] = normals_index[normal]

    return output, normals_lookup_dict


# Produce material lookup dictionary from the materials assigned to the object.
# {material 0: (texture, material), ...: (..., ....), ...}
def process_materials(obj, relative):
    output = {0: ("", "")}

    for i, slot in enumerate(obj.material_slots):
        mat = slot.material
        if mat:
            output[i] = mat.a3ob_properties_material.to_p3d(relative)
        else:
            output[i] = ("", "")

    return output


# Produce the face data dictionary from the obj and  bmesh data.
# {face 0: ([vert 0, vert 1, vert 2], [normal 0, normal 1, normal 2], [(uv 0 0, uv 0 1), (...), ...], texture, material, flag), ...}
def process_faces(obj, bm, normals_lookup, relative):
    output = {}
    # Materials need to be precompiled to speed up the face access.
    materials = process_materials(obj, relative)

    uv_layer = None
    if len(bm.loops.layers.uv.values()) > 0: # 1st UV set needs to be written into the face data section too
        uv_layer = bm.loops.layers.uv.values()[0]
    
    flag_layer = flagutils.get_layer_flags_face(bm)
    
    for face in bm.faces:
        verts = []
        normals = []
        uvs = []

        for loop in face.loops:
            verts.append(loop.vert.index)
            normals.append(normals_lookup[loop.index])
            uvs.append((loop[uv_layer].uv[0], 1 - loop[uv_layer].uv[1]) if uv_layer else (0, 0))

        output[face.index] = [verts, normals, uvs, *materials[face.material_index], face[flag_layer]]

    return output


def is_flat_shaded(bm):
    for face in bm.faces:
        if face.smooth:
            return False
    
    return True


def process_tagg_sharp(bm):
    output = p3d.P3D_TAGG()
    output.name = "#SharpEdges#"
    output.data = p3d.P3D_TAGG_DataSharpEdges()

    # For ease of use, the edges of flat shaded faces need to be exported as sharp as well.
    # Technically this creates fertile ground for mistakes, maybe it should be only done
    # if the whole mesh is flat shaded.
    if is_flat_shaded(bm):
        flat_face_edges = set()
        for face in bm.faces:
            if not face.smooth:
                flat_face_edges.update({edge for edge in face.edges if edge.is_contiguous})
        
        output.data.edges = [(edge.verts[0].index, edge.verts[1].index) for edge in flat_face_edges]
    else:
        output.data.edges = [(edge.verts[0].index, edge.verts[1].index) for edge in bm.edges if not edge.smooth and edge.is_contiguous]

    return output


def process_tagg_uvset(bm, layer):
    output = p3d.P3D_TAGG()
    output.name = "#UVSet#"
    output.data = p3d.P3D_TAGG_DataUVSet()
    uvs = {}

    for face in bm.faces:
        for loop in face.loops:
            uvs[loop.index] = (loop[layer].uv[0], loop[layer].uv[1])

    output.data.uvs = dict(sorted(uvs.items()))

    return output


def process_tagg_property(prop):
    output = p3d.P3D_TAGG()
    output.name = "#Property#"
    output.data = p3d.P3D_TAGG_DataProperty()
    output.data.key = prop.name
    output.data.value = prop.value

    return output


def process_tagg_mass(bm, layer):
    output = p3d.P3D_TAGG()
    output.name = "#Mass#"
    output.data = p3d.P3D_TAGG_DataMass()

    for vert in bm.verts:
        output.data.masses[vert.index] = vert[layer]

    return output


def process_taggs_selections(obj, bm):
    output = {}

    for i, group in enumerate(obj.vertex_groups):
        new_tagg = p3d.P3D_TAGG()
        new_tagg.name = group.name
        new_tagg.data = p3d.P3D_TAGG_DataSelection()
        new_tagg.data.count_verts = len(bm.verts)
        new_tagg.data.count_faces = len(bm.faces)
        output[i] = new_tagg

    bm.verts.layers.deform.verify()
    layer = bm.verts.layers.deform.active

    for vert in bm.verts:
        for idx in vert[layer].keys():
            output[idx].data.weight_verts[vert.index] = vert[layer][idx]
    
    # If all vertices of a face belong to a selection, then the face belongs to the 
    # selection as well.
    for face in bm.faces:
        indices = [idx for vert in face.verts for idx in vert[layer].keys()]
        unique = set(indices)
        for idx in unique:
            if indices.count(idx) == len(face.loops):
                output[idx].data.weight_faces[face.index] = 1

    return output.values()


def process_taggs(obj, bm, logger):
    object_props = obj.a3ob_properties_object
    taggs = [process_tagg_sharp(bm)]
    logger.log("Collected sharp edges")

    uv_index = 0
    for layer in bm.loops.layers.uv.values():
        uvset = process_tagg_uvset(bm, layer)
        uvset.data.id = uv_index
        taggs.append(uvset)
        uv_index += 1
    logger.log("Collected UV sets")
    
    for prop in object_props.properties:
        taggs.append(process_tagg_property(prop))
    logger.log("Collected named properties")

    # Vertex mass should only be exported for the Geometry LOD
    if object_props.lod == '6':
        layer = bm.verts.layers.float.get("a3ob_mass")
        if layer:
            taggs.append(process_tagg_mass(bm, layer))
            logger.log("Collected vertex masses")

    taggs.extend(process_taggs_selections(obj, bm))
    logger.log("Collected selections")

    return taggs


def translate_selections(p3dm):
    for tagg in p3dm.taggs:
        tagg.name = data.translations_english_czech.get(tagg.name.lower(), tagg.name)


def process_lod(operator, obj, proxy_lookup, is_valid, processed_signatures, logger):
    object_props = obj.a3ob_properties_object
    lod_name = object_props.get_name()

    logger.level_up()
    logger.step("Type: %s" % lod_name)

    if not is_valid:
        logger.log("Failed validation -> skipping LOD (run manual validation for details)")
        logger.level_down()
        return None

    logger.step("Processing data:")
    output = p3d.P3D_LOD()
    lod_idx = int(object_props.lod)
    if lod_idx != data.lod_unknown:
        output.resolution.set(lod_idx, object_props.resolution)
    else:
        output.resolution.set(lod_idx, object_props.resolution_float)
    
    signature = float(output.resolution)
    if signature in processed_signatures and operator.lod_collisions != 'IGNORE':
        if operator.lod_collisions == 'FAIL':
            raise p3d.P3D_Error("Duplicate LODs detected")
        logger.log("Duplicate -> skipping LOD")
        logger.level_down()
        return None
    else:
        processed_signatures.add(signature)

    mesh = obj.data

    normals, normals_lookup_dict = process_normals(mesh)
    output.normals = normals
    logger.log("Collected vertex normals")

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    output.verts = process_vertices(bm)
    logger.log("Collected vertices")
    output.faces = process_faces(obj, bm, normals_lookup_dict, operator.relative_paths)
    logger.log("Collected faces")
    output.taggs = process_taggs(obj, bm, logger)

    if operator.renumber_components:
        output.renumber_components()
        logger.log("Renumbered component selections")
    
    if operator.translate_selections:
        translate_selections(output)
        logger.log("Translated selections to czech")

    bm.free()

    # The placeholder proxy selection names must be replaced with the actual names.
    output.placeholders_to_proxies(proxy_lookup)
    logger.log("Finalized proxy selection names")

    logger.step("File report:")
    logger.log("Signature: %d" % float(output.resolution))
    logger.log("Type: P3DM")
    logger.log("Version: 28.256")
    logger.log("Vertices: %d" % len(output.verts))
    logger.log("Normals: %d" % len(output.normals))
    logger.log("Faces: %d" % len(output.faces))
    logger.log("Taggs: %d" % (len(output.taggs) + 1))

    logger.level_down()

    return output


def write_file(operator, context, file, temp_collection):
    wm = context.window_manager
    wm.progress_begin(0, 1000)
    wm.progress_update(0)
    
    validator = Validator(ProcessLoggerNull())
    if operator.validate_lods:
        validator.setup_lod_specific()
    
    logger = ProcessLogger()
    logger.step("P3D export to %s" % operator.filepath)

    time_file_start = time.time()

    # Gather all exportable LOD objects, duplicate them, merge their components, and validate for LOD type.
    # Produce the final mesh data, proxy lookup table and validity for each LOD.
    lod_list = get_lod_data(operator, context, validator, temp_collection)
    
    logger.log("Preprocessing done in %f sec" % (time.time() - time_file_start))
    logger.log("Detected %d LOD objects" % len(lod_list))

    mlod = p3d.P3D_MLOD()
    logger.log("File type: MLOD")
    logger.log("File version: %d" % 257)

    logger.log("Processing LOD data:")
    logger.level_up()

    mlod_lods = []
    processed_signatures = set()
    for i, (lod, proxy_lookup, is_valid) in enumerate(lod_list):
        time_lod_start = time.time()
        logger.step("LOD %d: %s" % (i + 1, lod["a3ob_original_object"]))

        new_lod = process_lod(operator, lod, proxy_lookup, is_valid, processed_signatures, logger)
        if new_lod:
            mlod_lods.append(new_lod)

        logger.log("Done in %f sec" % (time.time() - time_lod_start))
        wm.progress_update(i + 1)

    if len(mlod_lods) == 0:
        raise p3d.P3D_Error("All LODs failed validation, cannot write P3D with 0 LODs")

    # LODs should be sorted by their resolution signature.
    mlod_lods.sort(key=lambda lod: float(lod.resolution))
    mlod.lods = mlod_lods
    logger.step("Sorted LODs")

    if operator.force_lowercase:
        mlod.force_lowercase()
        logger.step("Forced lowercase")

    mlod.write(file)
    
    logger.level_down()
    logger.step("P3D export finished in %f sec" % (time.time() - time_file_start))

    return len(lod_list), len(mlod_lods)
