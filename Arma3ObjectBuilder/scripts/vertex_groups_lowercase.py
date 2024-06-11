#   ---------------------------------------- HEADER ----------------------------------------
#   
#   Author: MrClock
#   Add-on: Arma 3 Object Builder
#   
#   Description:
#       The script turns the names of vertex groups defined in the selected objects to lowercase.
#
#   Usage:
#       1. select the target objects in the 3D view
#       2. run script
#   
#   ----------------------------------------------------------------------------------------


#   ---------------------------------------- LOGIC -----------------------------------------

import bpy


for obj in [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']:
    for group in obj.vertex_groups:
        group.name = group.name.lower()
