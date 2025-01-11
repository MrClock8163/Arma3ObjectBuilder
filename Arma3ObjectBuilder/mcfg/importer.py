# Processing functions to import skeleton definitions from model.cfg file.
# The actual file handling is implemented in the data_rap module.


import os
import tempfile
import subprocess

from .. import get_prefs
from .. import config
from ..utilities.logger import ProcessLogger


class Bone():
    def __init__(self, name = "", parent = ""):
        self.name = name
        self.parent = parent
    
    def __eq__(self, other):
        return isinstance(other, Bone) and self.name.lower() == other.name.lower()
    
    def __hash__(self):
        return hash(self.name)
    
    def __repr__(self):
        return "\"%s\"" % self.name
    
    def to_lowercase(self):
        self.name = self.name.lower()
        self.parent = self.parent.lower()

        return self


def get_cfg_convert():
    return os.path.join(get_prefs().a3_tools, "cfgconvert/cfgconvert.exe")


# Binary reading is far more reliable, and less messy than trying to
# parse either the raw config syntax, or the XML output of cfgconvert.
# It can be used as a fallback option on systems where and Arma 3 Tools are installed.
def cfgconvert(filepath, exepath):
    current_dir = os.getcwd()
    
    if os.path.exists("P:\\"):
        os.chdir("P:\\")
    
    destfile = tempfile.NamedTemporaryFile(mode="w+b", prefix="mcfg_", delete=False)
    destfile.close()
    
    try:
        results = subprocess.run([exepath, "-bin", "-dst", destfile.name, filepath], capture_output=True)
        results.check_returncode()
    except:
        os.chdir(current_dir)
        os.remove(destfile.name)
        return ""
        
    os.chdir(current_dir)
    
    return destfile.name


# Attempt to read in a model.cfg file. First attempt will be made to parse the file directly.
# If parsing fails, second attempt will be to rapify the model.cfg and reading the binary.
def read_mcfg(filepath, logger):
    data = None
    try:
        tokens = config.tokenize_file(filepath)
        tokens = config.wrap(tokens, "root")
        data = config.parse(tokens)
        return data
    except:
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
        
        data = config.derapify_file(temppath)
        os.remove(temppath)
        return data
    except:
        logger.step("Failed to binarize and read model.cfg")
        return None


def get_bones(bonearray):
    output = []
    for i in range(0, len(bonearray), 2):
        new_bone = Bone()
        new_bone.name = bonearray[i]
        new_bone.parent = bonearray[i + 1]
        output.append(new_bone)
        
    return output


# Like properties, bones can be inherited from other skeletons with the
# skeletonInherit property, so the inheritance tree has to traversed.
def get_bones_compiled(mcfg, skeleton_name):
    bones_prop = mcfg.get_prop("root/CfgSkeletons/%s/skeletonBones" % skeleton_name)
    bones_self = []
    if bones_prop:
        bones_self = get_bones(bones_prop.topy())
    
    bones_inherit = mcfg.get_prop("root/CfgSkeletons/%s/skeletonInherit" % skeleton_name)
    if bones_inherit is None or bones_inherit == "":
        return bones_self
    
    bones_inherited = get_bones_compiled(mcfg, bones_inherit)

    output = []
    for item in bones_inherited + bones_self:
        if item not in output:
            output.append(item)
        
    return output


def read_file(operator, context):
    logger = ProcessLogger()
    logger.start_subproc("Skeleton import from %s" % operator.filepath)
    data = read_mcfg(operator.filepath, logger)
    scene_props = context.scene.a3ob_rigging

    if not data:
        logger.step("Could not read model.cfg file")
        logger.end_subproc("Skeleton import terminated")
        return 0
    
    if operator.force_lowercase:
        logger.step("Force lowercase")

    skeletons = data.get_class("root/cfgskeletons")
    if not skeletons or len(skeletons.classes) == 0:
        logger.step("Did not find any skeletons")
        logger.end_subproc("Skeleton import terminated")
        return 0
    
    logger.start_subproc("Found skeletons:")
    newcount = 0
    for skelly in skeletons.classes:
        if skelly.isreference():
            continue

        new_skelly = scene_props.skeletons.add()
        newcount += 1
        new_skelly.name = skelly.name.lower() if operator.force_lowercase else skelly.name
        new_skelly.protected = operator.protected

        cfgbones = get_bones_compiled(data, skelly.name)
        logger.step("%s: %d compiled bones" % (skelly.name, len(cfgbones)))
        if operator.force_lowercase:
            cfgbones = [bone.to_lowercase() for bone in cfgbones]

        for bone in cfgbones:
            new_bone = new_skelly.bones.add()
            new_bone.name = bone.name
            new_bone.parent = bone.parent
    
    logger.end_subproc()
    logger.end_subproc()
    logger.step("Skeleton import finished")
        
    return newcount
