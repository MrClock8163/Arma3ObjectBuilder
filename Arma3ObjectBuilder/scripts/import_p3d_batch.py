#   ---------------------------------------- HEADER ----------------------------------------
#   
#   Author: MrClock
#   Add-on: Arma 3 Object Builder
#   
#   Description:
#       The script batch imports P3D files from a given folder, with the given settings.
#       The available settings correspond to the options available in the import function
#       included in the standard Blender menu.
#
#   Usage:
#       1. copy the path of source folder
#       2. set settings as necessary
#       3. run script
#   
#   ----------------------------------------------------------------------------------------


#   --------------------------------------- SETTINGS ---------------------------------------

class Settings:
    # Folder of P3D files
    filepath = r""
    # Attempt to restore relative file paths
    relative_paths = True
    # Create collection with P3D name
    enclose = True
    # Group LODs by: 'NONE' or 'TYPE'
    groupby = 'TYPE'
    # Import 1st LOD only (usually the 1st visual resolution)
    first_lod_only = False
    # Allow reading data other than pure mesh data
    additional_data_allowed = True
    # Additional data types to read if allowed
    additional_data = {
        'NORMALS',      # vertex normals
        # 'FLAGS',        # vertex and face flags
        'PROPS',        # named properties
        'MASS',         # vertex masses
        'SELECTIONS',   # named selections (aka: vertex groups)
        'UV',           # additional UV sets
        'MATERIALS'     # material
    }
    # Validate and cleanup imported meshes with degenerated geometry
    validate_meshes = False
    # Postprocess proxies: 'NOTHING', 'SEPARATE' or 'CLEAR'
    proxy_action = 'SEPARATE'
    # Translate czech selection names to english
    translate_selections = False
    # Cleanup selections without any vertices assigned
    cleanup_empty_selections = False


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

read_file = importlib.import_module(addon).io.import_p3d.read_file


def main():
    files = []
    folder = Settings.filepath
    
    if not os.path.exists(folder) and not os.path.isdir(folder):
        return
    
    for item in os.listdir(folder):
        item = os.path.join(folder, item)
        if os.path.isfile(item) and os.path.splitext(item)[1].lower() == ".p3d":
            files.append(item)

    for item in files:
        Settings.filepath = item
        
        with open(Settings.filepath, "rb") as file:
                read_file(Settings, bpy.context, file)


main()
