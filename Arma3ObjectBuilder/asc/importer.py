# Processing functions to import DTM data from ESRI ASCII grid (*.asc) files.
# The actual file handling is implemented in the data_asc module.


import time

import bpy

from . import data as asc
from ..logger import ProcessLogger
    
    
def build_points(raster, hscale = 1, vscale = 1):
    cellsize = raster.cellsize

    start_x = 0
    start_y = 0
    if raster.type == asc.ASC_File.TYPE_RASTER:
        start_x = start_y = cellsize / 2
    
    start_y += (len(raster.data) - 1) * cellsize
        
    points = []
    for i, row in enumerate(raster.data):
        for j, value in enumerate(row):
            x = (start_x + j * cellsize) * hscale
            y = (start_y + i * -cellsize) * hscale
            z = value * vscale
            points.append((x, y, z))
            
    return points
    
    
def build_faces(nrows, ncols):
    faces = []
    for i in range(nrows - 1):
        for j in range(ncols - 1):
            faces.append((i*ncols + j, (i + 1)*ncols + j, (i + 1)*ncols + j + 1, i*ncols + j + 1))
    
    return faces
            

def read_file(operator, context, file):
    logger = ProcessLogger()
    time_start = time.time()
    logger.start_subproc("ASC DTM import from %s" % operator.filepath)

    raster = asc.ASC_File.read(file)
    logger.step("File reading done in %f sec" % (time.time() - time_start))
    
    nrows, ncols = raster.get_dimensions()
    east, north = raster.pos
    logger.start_subproc("File report:")
    logger.step("Dimensions: %d x %d" % (nrows, ncols))
    logger.step("Cell size: %f" % raster.cellsize)
    logger.step("DTM type: %s" % ("raster" if raster.type == asc.ASC_File.TYPE_RASTER else "grid"))
    logger.step("Easting: %f" % east)
    logger.step("Northing: %f" % north)
    logger.end_subproc()

    logger.start_subproc("Processing data:")
    points = build_points(raster, operator.hscale, operator.vscale)
    logger.step("Built points: %d" % len(points))

    faces = build_faces(nrows, ncols)
    logger.step("Built faces: %d" % len(faces))
        
    mesh = bpy.data.meshes.new("DTM")
    mesh.from_pydata(points, [], faces)
    mesh.update(calc_edges=True)
    
    obj = bpy.data.objects.new("DTM", mesh)
    context.scene.collection.objects.link(obj)
    
    object_props = obj.a3ob_properties_object_dtm
    object_props.cellsize_source = 'MANUAL'
    object_props.cellsize = raster.cellsize
    
    if raster.type == asc.ASC_File.TYPE_RASTER:
        object_props.data_type = 'RASTER'
    else:
        object_props.data_type = 'GRID'

    object_props.easting = east
    object_props.northing = north
    object_props.nodata = raster.nodata if raster.nodata is not None else -9999.0
    
    logger.end_subproc()
    logger.end_subproc()
    logger.step("ASC export finished in %f sec" % (time.time() - logger.times.pop()))
