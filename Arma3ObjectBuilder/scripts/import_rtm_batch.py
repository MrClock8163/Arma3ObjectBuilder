#   ---------------------------------------- HEADER ----------------------------------------
#   
#   Author: MrClock
#   Add-on: Arma 3 Object Builder
#   
#   Description:
#       The script batch imports RTM files from a given folder, with the given settings, and
#       applies them as new actions to a selected target armature.
#       The available settings correspond to the options available in the import function
#       included in the standard Blender menu.
#
#   Usage:
#       1. copy the path of source folder
#       2. set settings as necessary
#       3. select target armature in 3D view
#       4. run script
#   
#   ----------------------------------------------------------------------------------------


#   --------------------------------------- SETTINGS ---------------------------------------

class Settings:
    # Folder of RTM files
    filepath = r""
    # Bake motion vector into keyframes
    apply_motion = True
    # Mute bone constraints on target armature
    mute_constraints = True
    # Set the imported action as active (pointless in case of this batch import)
    make_active = False
    # Round calculated frame values to the nearest integer frames
    round_frames = True
    # Phase -> Frame mapping mod: 'RANGE', 'FPS' or 'DIRECT'
    mapping_mode = 'FPS'
    # Options for 'RANGE' mapping
    frame_start = 0
    frame_end = 100
    # Options for 'FPS' mapping
    time = 1
    fps = 24
    fps_base = 1.0


#   ---------------------------------------- LOGIC -----------------------------------------

import os
import importlib

import bpy

name = None
for addon in bpy.context.preferences.addons.keys():
    if addon.endswith("Arma3ObjectBuilder"):
        name = addon
        break
else:
    raise Exception("Arma 3 Object Builder could not be found")

import_file = importlib.import_module(addon).io.import_rtm.import_file


def main():
    files = []
    folder = Settings.filepath
    
    if not os.path.exists(folder) and not os.path.isdir(folder):
        return
    
    for item in os.listdir(folder):
        item = os.path.join(folder, item)
        if os.path.isfile(item) and os.path.splitext(item)[1].lower() == ".rtm":
            files.append(item)
    
    for item in files:
        Settings.filepath = item
        
        with open(Settings.filepath, "rb") as file:
                import_file(Settings, bpy.context, file)


main()
