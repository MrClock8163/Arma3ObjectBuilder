# Writer functions to export text formatted model.cfg file.


from . import data_rap as rap
from ..utilities import rigging as riggingutils
from ..utilities.logger import ProcessLogger


def write_file(operator, skeleton, file):
    logger = ProcessLogger()
    logger.step("Skeleton definition export to %s" % operator.filepath)
    logger.log("Skeleton definition: %s" % skeleton.name)
    bones_parents = riggingutils.bone_order_from_skeleton(skeleton)

    logger.log("Bones: %d" % len(bones_parents))
    
    if operator.force_lowercase:
        logger.log("Force lowercase")
        bones_parents = {k.lower(): v.lower() for k, v in bones_parents.items()}
    
    printer = rap.CFG_Formatter(file)

    printer.class_open("CfgSkeletons")
    printer.class_open(skeleton.name)

    printer.property_int("isDiscrete", 0)
    printer.property_string("skeletonInherit", "")

    printer.array_open("skeletonBones")
    printer.array_items(["\"%s\", \"%s\"" % (k, v) for k, v in bones_parents.items()])
    printer.array_close()
    printer.comment("Path to the pivot points model has to be set manually")
    printer.comment("pivotsModel = \"path\\to\\pivots.p3d\";")
    
    printer.class_close()
    printer.class_close()

    logger.log("Wrote formatted file")
    logger.step("Skeleton export finished")
