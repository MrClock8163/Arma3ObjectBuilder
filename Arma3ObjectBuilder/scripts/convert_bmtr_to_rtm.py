#   ---------------------------------------- HEADER ----------------------------------------
#   
#   Author: MrClock
#   Add-on: Arma 3 Object Builder
#   
#   Description:
#       The script converts binarized (BMTR) animations back to plain editable RTM format.
#       Conversion is done using the OFP2_ManSkeleton bone hierarchy, for animations with custom skeletons,
#       the custom bone hierarchy has to be defined manually.
#
#   Usage:
#       1. set settings as necessary
#       2. run script
#   
#   ----------------------------------------------------------------------------------------


#   --------------------------------------- SETTINGS ---------------------------------------

class Settings:
    # Input folder or file
    path_input = r""
    # Output folder or file
    path_output = r""
    # Bone hierarchy dictionary (None or empty {} -> OFP2_ManSkeleton will be used, other skeleton can be defined 
    # as a {"bone1": "", "bone2": "bone3", ...} bone-parent dictionary in HIERARCHICAL order!)
    skeleton = None
    # Skip conversion if the BMTR has a bone that is not defined in the bone hierarchy
    # (transformations of unknown bones might come out faulty if they are allowed to be converted)
    skip_on_missing_bone = True
    # Force all bone names to be lowercase (casing of the bone names is important for previewing animations
    # in the Object Builder application and/or Buldozer)
    force_lowercase = False


#   ---------------------------------------- LOGIC -----------------------------------------

import os
import importlib

import bpy

name = None
for addon in bpy.context.preferences.addons:
    if addon.module.endswith("Arma3ObjectBuilder"):
        name = addon.module
        break
else:
    raise Exception("Arma 3 Object Builder could not be found")

a3ob = importlib.import_module(name)
a3ob_io = a3ob.io
rtm = a3ob.io_rtm.data
ofp2_manskeleton = a3ob.tool_rigging.ofp2_manskeleton
ProcessLogger = a3ob.logger.ProcessLogger


def get_ofp2_manskeleton():
    return {bone: parent for bone, parent in ofp2_manskeleton.bone_hierarchy}


def get_input_output():
    filepaths_in = []
    filepaths_out = []

    if os.path.isfile(Settings.path_input):
        if os.path.splitext(Settings.path_input)[1].lower() != ".rtm":
            raise ValueError("The input file is not an RTM")
        
        filepaths_in = [Settings.path_input]

        if os.path.splitext(Settings.path_output)[1] != "":
            filepaths_out = [Settings.path_output]
        else:
            filepaths_out = [os.path.join(Settings.path_output, os.path.basename(Settings.path_input))]

    elif os.path.isdir(Settings.path_input):
        folder_out = Settings.path_output

        if os.path.splitext(Settings.path_output)[1] != "":
            folder_out = os.path.split(Settings.path_output)[0]

        if not os.path.isdir(folder_out):
            os.makedirs(folder_out, exist_ok=True)

        for file in os.listdir(Settings.path_input):
            if os.path.splitext(file)[1].lower() == ".rtm":
                filepaths_in.append(os.path.join(Settings.path_input, file))
                filepaths_out.append(os.path.join(folder_out, os.path.basename(file)))

    else:
        raise ValueError("The input path does not exist")

    return filepaths_in, filepaths_out


def main():
    logger = ProcessLogger()
    logger.step("Converting BMTR to plain RTM")
    logger.level_up()

    files_in, files_out = get_input_output()

    if len(files_in) != len(files_out):
        raise ValueError("Input and output counts don not match (in: %d, out: %d)" % (len(files_in), len(files_out)))
    
    skeleton = Settings.skeleton
    if not skeleton:
        skeleton = get_ofp2_manskeleton()
    
    if Settings.force_lowercase:
        skeleton = {bone.lower(): parent.lower() for bone, parent in skeleton.items()}
    
    known_bones = set([bone.lower() for bone in skeleton])
    
    for path_in, path_out in zip(files_in, files_out):
        with open(path_in, "rb") as file:
            if file.read(4) != b"BMTR":
                logger.step("Skipping - not BMTR - path: %s" % path_in)
                continue

            file.seek(0)
            rtm_data = rtm.BMTR_File.read(file)

        unknown_bones = [bone for bone in rtm_data.bones if bone.lower() not in known_bones]
        if Settings.skip_on_missing_bone and len(unknown_bones) > 0:
            logger.step("Skipping - uknown bones: %s - path: %s" % (str(unknown_bones), path_in))
            continue
        
        rtm_data_plain = rtm_data.as_rtm(skeleton)

        with open(path_out, "wb") as file:
            rtm_data_plain.write(file)
        
        logger.step("Converted - path in: %s - path out: %s" % (path_in, path_out))
    
    logger.level_down()
    logger.step("Finished conversion")


main()
