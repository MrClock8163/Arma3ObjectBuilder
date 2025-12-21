# Processing functions to export DTM data to ESRI ASCII grid (*.asc) files.
# The actual file handling is implemented in the data_asc module.


import math
import time
from typing import TextIO

import bpy
from mathutils import Vector

from . import data as asc
from ..logger import ProcessLogger


def calc_resolution(
    operator: bpy.types.Operator,
    count_vertex: int
) -> tuple[int, int]:
    nrows = 0
    ncols = 0

    if operator.dimensions == 'SQUARE':  # type: ignore[attr-defined]
        nrows = ncols = int(math.sqrt(count_vertex))
    elif operator.dimensions == 'LANDSCAPE':  # type: ignore[attr-defined]
        nrows = int(math.sqrt(count_vertex / 2))
        ncols = 2 * nrows
    elif operator.dimensions == 'PORTRAIT':  # type: ignore[attr-defined]
        ncols = int(math.sqrt(count_vertex / 2))
        nrows = 2 * ncols
    else:
        nrows = operator.rows  # type: ignore[attr-defined]
        ncols = operator.columns  # type: ignore[attr-defined]

    return nrows, ncols


def calc_cellsize(
    data: list[list[Vector]],
    nrows: int,
    ncols: int
) -> float | None:
    if ncols > 1:
        return round(data[0][1][0] - data[0][0][0], 3)
    elif nrows > 1:
        return round(data[1][0][1] - data[0][0][1], 3)
    else:
        return None


def get_points(
    vertices: bpy.types.MeshVertices,
    nrows: int,
    ncols: int
) -> list[list[Vector]]:
    points = [vertex.co for vertex in vertices]
    points.sort(key=lambda vert: vert[1], reverse=True)

    data: list[list[Vector]] = []
    for i in range(nrows):
        row = points[i * ncols: (i + 1) * ncols]
        row.sort(key=lambda vert: vert[0])
        data.append(row)

    assert len(data) == nrows

    return data


def write_file(
    operator: bpy.types.Operator,
    context: bpy.types.Context,
    file: TextIO,
    obj: bpy.types.Object
) -> None:
    logger = ProcessLogger()
    logger.start_subproc("ASC DTM export to %s" % operator.filepath)  # type: ignore[attr-defined]

    assert isinstance(context.active_object, bpy.types.Object)
    obj = context.active_object
    if obj.mode == 'EDIT':
        obj.update_from_editmode()

    logger.start_subproc("Processing data:")

    if operator.apply_modifiers:  # type: ignore[attr-defined]
        obj = obj.evaluated_get(context.evaluated_depsgraph_get())
        logger.step("Applied modifiers")

    mesh = obj.data
    assert isinstance(mesh, bpy.types.Mesh)
    object_props = obj.a3ob_properties_object_dtm  # type: ignore[attr-defined]

    raster = asc.ASC_File()
    raster.type = asc.ASC_Type.RASTER if object_props.data_type == 'RASTER' else asc.ASC_Type.GRID
    raster.pos = (object_props.easting, object_props.northing)
    raster.nodata = object_props.nodata

    count_vertex = len(mesh.vertices)
    nrows, ncols = calc_resolution(operator, count_vertex)
    if count_vertex != (nrows * ncols):
        raise asc.ASC_Error("Invalid dimensions: %d x %d (vertex count: %d)" % (nrows, ncols, count_vertex))

    logger.step("Calculated dimensions")

    data = get_points(mesh.vertices, nrows, ncols)
    raster.data = [[vert[2] for vert in row] for row in data]
    logger.step("Collected data")

    cellsize = object_props.cellsize
    if object_props.cellsize_source == 'CALCULATED' and count_vertex > 1:
        cellsize = calc_cellsize(data, nrows, ncols)
        if cellsize is None:
            raise asc.ASC_Error("Could not calculate cellsize")
        logger.step("Calculated cellsize")

    raster.cellsize = cellsize
    logger.end_subproc(True)

    logger.start_subproc("File report:")
    logger.step("Dimensions: %d x %d" % (nrows, ncols))
    logger.step("Cell size: %f" % cellsize)
    logger.step("DTM type: %s" % ("raster" if raster.type is asc.ASC_Type.RASTER else "grid"))
    logger.step("Easting: %f" % object_props.easting)
    logger.step("Northing: %f" % object_props.northing)
    logger.step("NULL indicator: %f" % object_props.nodata)
    logger.end_subproc()

    raster.write(file)

    logger.end_subproc()
    logger.step("ASC export finished in %.3f sec" % (time.time() - logger.times.pop()))
