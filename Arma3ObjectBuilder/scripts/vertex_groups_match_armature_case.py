#   ---------------------------------------- HEADER ----------------------------------------
#   
#   Author: MrClock
#   Add-on: Arma 3 Object Builder
#   
#   Description:
#       The script matches the casing of vertex group names in the selected mesh objects, to the 
#       bone names of the active armature object.
#
#   Usage:
#       1. select mesh objects
#       2. select target armature as active object
#       3. run script
#   
#   ----------------------------------------------------------------------------------------


#   ---------------------------------------- LOGIC -----------------------------------------

import bpy


armature = bpy.context.active_object
meshes = [obj for obj in bpy.context.selected_objects if obj is not armature and obj.type == 'MESH']

bones = {bone.name.lower(): bone.name for bone in armature.data.bones}

for obj in meshes:
    for group in obj.vertex_groups:
        key = group.name.lower()
        if key in bones:
            group.name = bones[key]
