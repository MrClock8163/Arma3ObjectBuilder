# Processing functions to import skeleton definitions from model.cfg file.
# The actual file handling is implemented in the data_rap module.


import os
import tempfile
import subprocess
from typing import Any, Self, cast

import bpy

from .. import get_prefs
from .. import io_config as cfg
from ..logger import ProcessLogger


class Bone():
    def __init__(self, name: str = "", parent: str = "") -> None:
        self.name: str = name
        self.parent: str = parent

    def __eq__(self, other: Any) -> bool:
        return bool(isinstance(other, Bone) and self.name.lower() == other.name.lower())

    def __hash__(self) -> int:
        return hash(self.name)

    def __repr__(self) -> str:
        return "\"%s\"" % self.name

    def to_lowercase(self) -> Self:
        self.name = self.name.lower()
        self.parent = self.parent.lower()

        return self


def get_cfg_convert() -> str:
    return os.path.join(get_prefs().a3_tools, "cfgconvert/cfgconvert.exe")


# Binary reading is far more reliable, and less messy than trying to
# parse either the raw config syntax, or the XML output of cfgconvert.
# It can be used as a fallback option on systems where and Arma 3 Tools are installed.
def cfgconvert(filepath: str, exepath: str) -> str:
    current_dir = os.getcwd()

    if os.path.exists("P:\\"):
        os.chdir("P:\\")

    destfile = tempfile.NamedTemporaryFile(mode="w+b", prefix="mcfg_", delete=False)
    destfile.close()

    try:
        results = subprocess.run([exepath, "-bin", "-dst", destfile.name, filepath], capture_output=True)
        results.check_returncode()
    except Exception:
        os.chdir(current_dir)
        os.remove(destfile.name)
        return ""

    os.chdir(current_dir)

    return destfile.name


# Attempt to read in a model.cfg file. First attempt will be made to parse the file directly.
# If parsing fails, second attempt will be to rapify the model.cfg and reading the binary.
def read_mcfg(filepath: str, logger: ProcessLogger) -> cfg.data.CFG | None:
    data: cfg.data.CFG | None = None
    try:
        tokens = cfg.tokenize_file(filepath)
        tokens = cfg.wrap(tokens, "root")
        data = cfg.parse(tokens)
        return data
    except Exception:
        logger.step("Failed to directly parse model.cfg -> attempting rapification")

    try:
        exepath = get_cfg_convert()
        if not os.path.isfile(exepath):
            logger.step("Could not find CfgConvert.exe")
            return None

        temppath = cfgconvert(filepath, exepath)

        if temppath == "":
            logger.step("Failed to rapify file")
            return None

        data = cfg.derapify_file(temppath)
        os.remove(temppath)
        return data
    except Exception:
        logger.step("Failed to binarize and read model.cfg")
        return None


def get_bones(bonearray: list[str]) -> list[Bone]:
    output: list[Bone] = []
    for i in range(0, len(bonearray), 2):
        new_bone = Bone()
        new_bone.name = bonearray[i]
        new_bone.parent = bonearray[i + 1]
        output.append(new_bone)

    return output


# Like properties, bones can be inherited from other skeletons with the
# skeletonInherit property, so the inheritance tree has to traversed.
def get_bones_compiled(
    mcfg: cfg.data.CFG,
    skeleton_name: str
) -> list[Bone]:
    bones_prop = mcfg.get_prop("root/CfgSkeletons/%s/skeletonBones" % skeleton_name)
    bones_self = []
    if bones_prop:
        bones_self = get_bones(bones_prop.topy())

    bones_inherit = mcfg.get_prop("root/CfgSkeletons/%s/skeletonInherit" % skeleton_name)
    if bones_inherit is None or bones_inherit.topy() == "":
        return bones_self

    bones_inherited = get_bones_compiled(mcfg, cast(cfg.data.CFGString, bones_inherit).topy())

    output = []
    for item in bones_inherited + bones_self:
        if item not in output:
            output.append(item)

    return output


def read_file(
    operator: bpy.types.Operator,
    context: bpy.types.Context
) -> int:
    logger = ProcessLogger()
    logger.start_subproc("Skeleton import from %s" % operator.filepath)  # type: ignore[attr-defined]
    data = read_mcfg(operator.filepath, logger)  # type: ignore[attr-defined]
    scene_props = context.scene.a3ob_rigging  # type: ignore[attr-defined]

    if not data:
        logger.step("Could not read model.cfg file")
        logger.end_subproc()
        # logger.end_subproc("Skeleton import terminated")
        return 0

    if operator.force_lowercase:  # type: ignore[attr-defined]
        logger.step("Force lowercase")

    skeletons = data.get_class("root/cfgskeletons")
    if not skeletons or len(skeletons.classes) == 0:
        logger.step("Did not find any skeletons")
        logger.end_subproc()
        # logger.end_subproc("Skeleton import terminated")
        return 0

    logger.start_subproc("Found skeletons:")
    newcount = 0
    for skelly in skeletons.classes:
        if skelly.isreference():
            continue

        new_skelly = scene_props.skeletons.add()
        newcount += 1
        new_skelly.name = skelly.name.lower() if operator.force_lowercase else skelly.name  # type: ignore[attr-defined]
        new_skelly.protected = operator.protected  # type: ignore[attr-defined]

        cfgbones = get_bones_compiled(data, skelly.name)
        logger.step("%s: %d compiled bones" % (skelly.name, len(cfgbones)))
        if operator.force_lowercase:  # type: ignore[attr-defined]
            cfgbones = [bone.to_lowercase() for bone in cfgbones]

        for bone in cfgbones:
            new_bone = new_skelly.bones.add()
            new_bone.name = bone.name
            new_bone.parent = bone.parent

    logger.end_subproc()
    logger.end_subproc()
    logger.step("Skeleton import finished")

    return newcount
