#   ---------------------------------------- HEADER ----------------------------------------
#   
#   Author: MrClock
#   Add-on: Arma 3 Object Builder
#   
#   Description:
#       The script adds the OFP2_ManSkeleton to the skeleton list of the Rigging tool panel.
#
#   Usage:
#       1. set settings as necessary
#       2. run script
#   
#   ----------------------------------------------------------------------------------------


#   --------------------------------------- SETTINGS ---------------------------------------

class Settings:
    # Turn all bone names to lowercase
    force_lowercase = True


#   ---------------------------------------- LOGIC -----------------------------------------
    
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
data = a3ob.tool_rigging.ofp2_manskeleton


def main():
    scene_props = bpy.context.scene.a3ob_rigging
    skeleton = scene_props.skeletons.add()
    skeleton.name = "ofp2_manskeleton" if Settings.force_lowercase else "OFP2_ManSkeleton"
    skeleton.protected = True

    for bone, parent in data.bone_hierarchy:
        item = skeleton.bones.add()
        item.name = bone.lower() if Settings.force_lowercase else bone
        item.parent = parent.lower() if Settings.force_lowercase else parent


main()
