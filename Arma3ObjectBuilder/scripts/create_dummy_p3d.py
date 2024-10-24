#   ---------------------------------------- HEADER ----------------------------------------
#   
#   Author: MrClock
#   Add-on: Arma 3 Object Builder
#   
#   Description:
#       The script creates an empty "dummy" P3D file at the specified path.
#       It might come in handy in special testing cases.
#
#   Usage:
#       1. set settings as necessary
#       2. run script
#   
#   ----------------------------------------------------------------------------------------


#   --------------------------------------- SETTINGS ---------------------------------------

class Settings:
    # Target path for dummy P3D
    filepath = r""


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
a3ob_utils = a3ob.utilities
a3ob_io = a3ob.io

p3d = a3ob.io.data_p3d


model = p3d.P3D_MLOD()
model.lods.append(p3d.P3D_LOD())

model.write_file(Settings.filepath)
