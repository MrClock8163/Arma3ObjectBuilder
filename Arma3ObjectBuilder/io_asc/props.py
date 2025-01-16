import bpy


class A3OB_PG_properties_object_dtm(bpy.types.PropertyGroup):
    data_type: bpy.props.EnumProperty(
        name = "Data Type",
        description = "Type of data arrangement",
        items = (
            ('RASTER', "Raster", "Data points are cell centered"),
            ('GRID', "Grid", "Data points are on cell corners")
        ),
        default = 'GRID'
    )
    easting: bpy.props.FloatProperty(
        name = "Easting",
        unit = 'LENGTH',
        default = 200000,
        soft_max = 1000000
    )
    northing: bpy.props.FloatProperty(
        name = "Northing",
        unit = 'LENGTH',
        soft_max = 1000000
    )
    cellsize_source: bpy.props.EnumProperty(
        name = "Source",
        description = "Source of cell size",
        items = (
            ('MANUAL', "Manual", "The cell size is explicitly set"),
            ('CALCULATED', "Calculated", "The cell size is from the distance of the first 2 points of the gird")
        ),
        default = 'MANUAL'
    )
    cellsize: bpy.props.FloatProperty(
        name = "Cell Size",
        description = "Horizontal and vertical space between raster points",
        unit = 'LENGTH',
        default = 1.0
    )
    nodata: bpy.props.FloatProperty(
        name = "NULL Indicator",
        description = "Filler value where data does not exist",
        default = -9999.0
    )


classes = (
    A3OB_PG_properties_object_dtm,
)


def register_props():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Object.a3ob_properties_object_dtm = bpy.props.PointerProperty(type=A3OB_PG_properties_object_dtm)


def unregister_props():
    del bpy.types.Object.a3ob_properties_object_dtm

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)