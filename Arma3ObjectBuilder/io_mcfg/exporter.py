# Writer functions to export text formatted model.cfg file.


from .. import io_config
from ..logger import ProcessLogger


def bones_from_skeleton(skeleton):
    return {bone.name: bone.parent for bone in skeleton.bones}


def write_file(operator, skeleton, file):
    logger = ProcessLogger()
    logger.start_subproc("Skeleton definition export to %s" % operator.filepath)
    logger.step("Skeleton definition: %s" % skeleton.name)
    bones_parents = bones_from_skeleton(skeleton)
    
    if operator.force_lowercase:
        logger.step("Force lowercase")
        bones_parents = {k.lower(): v.lower() for k, v in bones_parents.items()}

    logger.step("Bones: %d" % len(bones_parents))
    
    data = {
        "root": {
            "classes": {
                "CfgSkeletons": {
                    "classes": {
                        skeleton.name: {
                            "properties": {
                                "isDiscrete": 0,
                                "skeletonInherit": "",
                                "skeletonBones": [item for records in bones_parents.items() for item in records],
                                "pivotsModel": ""
                            }
                        }
                    }
                }
            }
        }
    }

    cfg = io_config.from_dict(data)
    file.write(cfg.format())

    logger.step("Wrote formatted file")
    logger.end_subproc()
    logger.step("Skeleton export finished")
