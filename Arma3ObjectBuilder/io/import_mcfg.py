# Processing functions to import skeleton definitions from model.cfg file.
# The actual file handling is implemented in the data_rap module.


import os
import tempfile
import subprocess

from . import data_rap as rap
from ..utilities import generic as utils
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


# The model.cfg reading is dependent on the import_rap module,
# so the model config first needs to be rapified by the Arma 3 Tools.
# Binary reading is far more reliable, and less messy than trying to
# parse either the raw config syntax, or the XML output of cfgconvert.
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


# Derapify the previously converted model.cfg.
def read_mcfg(filepath):
    exepath = utils.get_cfg_convert()
    if not os.path.isfile(exepath):
        return None

    temppath = cfgconvert(filepath, exepath)
    
    if temppath == "":
        return None
    
    data = rap.RAP_Reader.read_file(temppath)
    
    os.remove(temppath)
    
    return data


# Since the config syntax supports class inheritance, as well as
# some additional annoying ways to combine skeletons in model.cfg files,
# the inheritance tree has to be traversed to query properties.
def get_prop_compiled(mcfg, classname, propname):
    entry = mcfg.body.find(classname)
    if not entry or entry.type != rap.RAP.EntryType.CLASS:
        return None
    
    prop = entry.body.find(propname)
    if prop:
        return prop.value
    
    if entry.body.inherits == "":
        return None
        
    return get_prop_compiled(mcfg, entry.body.inherits, propname)


def get_skeletons(mcfg):
    skeletons = mcfg.body.find("CfgSkeletons")
    if skeletons:
        return skeletons.body.entries
    
    return []


def get_bones(skeleton):
    if skeleton.type == rap.RAP.EntryType.EXTERN:
        return []
    
    bones = skeleton.body.find("skeletonBones")
    if not bones:
        return []

    output = []
    for i in range(0, bones.body.element_count, 2):
        new_bone = Bone()
        new_bone.name = bones.body.elements[i].value
        new_bone.parent = bones.body.elements[i + 1].value
        output.append(new_bone)
        
    return output


# Like properties, bones can be inherited from other skeletons with the
# skeletonInherit property, so the inheritance tree has to traversed again.
def get_bones_compiled(mcfg, skeleton_name):
    cfg_skeletons = mcfg.body.find("CfgSkeletons")
    output = []
    
    if not cfg_skeletons or cfg_skeletons.type != rap.RAP.EntryType.CLASS:
        return []
        
    skeleton = cfg_skeletons.body.find(skeleton_name)
    if not skeleton or skeleton.type != rap.RAP.EntryType.CLASS:
        return []
    
    inherit_bones = get_prop_compiled(cfg_skeletons, skeleton_name, "skeletonInherit")
    if not inherit_bones:
        inherit_bones = ""
    
    bones_self = get_bones(skeleton)
    bones_inherit = []
    
    if not skeleton.body.find("skeletonBones") and skeleton.body.inherits != "":
        parent = cfg_skeletons.body.find(skeleton.body.inherits)
        if parent:
            bones_self = get_bones(parent)
        
    if inherit_bones != "":
        bones_inherit = get_bones_compiled(mcfg, inherit_bones)
    
    output = bones_self + bones_inherit
        
    return list(set(output))


def read_file(operator, context):
    logger = ProcessLogger()
    logger.step("Skeleton import from %s" % operator.filepath)
    data = read_mcfg(operator.filepath)
    scene_props = context.scene.a3ob_rigging

    if not data:
        logger.log("Could not read model.cfg file")
        logger.step("Skeleton import finished")
        return 0
    
    if operator.force_lowercase:
        logger.log("Force lowercase")

    skeletons = get_skeletons(data)
    logger.log("Found skeletons:")
    logger.level_up()
    for skelly in skeletons:
        new_skelly = scene_props.skeletons.add()
        new_skelly.name = skelly.name.lower() if operator.force_lowercase else skelly.name
        new_skelly.protected = operator.protected
        
        cfgbones = get_bones_compiled(data, skelly.name)
        logger.log("%s: %d compiled bones" % (skelly.name, len(cfgbones)))
        if operator.force_lowercase:
            cfgbones = [bone.to_lowercase() for bone in cfgbones]

        for bone in cfgbones:
            new_bone = new_skelly.bones.add()
            new_bone.name = bone.name
            new_bone.parent = bone.parent
    
    logger.level_down()
    logger.step("Skeleton import finished")
        
    return len(skeletons)
