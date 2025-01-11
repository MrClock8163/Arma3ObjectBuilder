# Processing functions to import object positions from the list format
# produced by Terrain Builder
# Thanks to HorribleGoat for the help and suggestions


import time
import math

import bpy
import mathutils

from . import data as tb
from ..utilities.logger import ProcessLogger


def object_records(operator, tbcsv):    
    for obj in tbcsv.objects:
        trans = obj.transform
        yaw, pitch, roll = trans.rot
        east, north, elev = trans.loc
        rot = mathutils.Euler([math.radians(angle) for angle in [pitch, roll, -yaw]], 'ZXY').to_matrix().to_4x4()
        loc = mathutils.Vector((east + operator.coord_shift[0], north + operator.coord_shift[1], elev))
        locrot = rot + mathutils.Matrix.Translation(loc) - mathutils.Matrix.Identity(4)
        mat = locrot @ mathutils.Matrix.Scale(trans.scale, 4)
        yield obj.name, mat


def get_template_names(tbcsv):
    return {obj.name for obj in tbcsv.objects}


def get_object_name(obj, operator):
    if operator.name_source == 'PROPERTY' and obj.get(operator.name_prop):
        return obj.get(operator.name_prop)
    elif operator.name_source == 'OBJECT':
        return obj.name.split(".")[0]
    
    return ""


def find_template_objects(context, operator, names):
    lookup = {}
    for obj in context.scene.objects:
        name = get_object_name(obj, operator)
        if name not in names:
            continue

        names.remove(name)
        lookup[name] = obj

    return lookup, sorted(names)


def spawn_from_template(context, templates, name, mat):
    base = templates.get(name)
    if not base:
        return False
    
    obj = base.copy()
    obj.matrix_world = mat

    collection = base.users_collection
    collection = collection[0] if len(collection) > 0 else context.scene.collection
    collection.objects.link(obj)

    return True


def cleanup_templates(templates):
    for obj in templates.values():
        bpy.data.objects.remove(obj)


def read_file(operator, context, file):
    logger = ProcessLogger()
    logger.start_subproc("Map objects list import from %s" % operator.filepath)

    tbcsv = tb.TBCSV_File.read(file)
    logger.step("Read objects: %d" % len(tbcsv.objects))
    template_names = get_template_names(tbcsv)
    logger.step("Needed template objects: %d" % len(template_names))
    templates, unknowns = find_template_objects(context, operator, template_names)
    logger.step("Found template objects: %d" % len(templates))
    if len(unknowns) > 0:
        logger.step("No template object found for: %s" % (", ".join(["\"%s\"" % item for item in unknowns])))

    count_found = 0
    for name, mat in object_records(operator, tbcsv):
        if spawn_from_template(context, templates, name, mat):
            count_found += 1

    logger.step("Spawned objects: %d" % count_found)
    
    if operator.cleanup_templates:
        cleanup_templates(templates)
        logger.step("Cleaned up template objects")

    logger.end_subproc()
    logger.step("Map objects list import finished in %f sec" % (time.time() - logger.times.pop()))

    return len(tbcsv.objects), count_found
