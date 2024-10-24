import os

import bpy

from .. import get_icon, addon_dir


scripts = {
    "vertex_groups": {
        "Lowercase": "vertex_groups_lowercase.py",
        "Match Armature": "vertex_groups_match_armature_case.py"
    },
    "import": {
        "P3D batch": "import_p3d_batch.py",
        "RTM batch": "import_rtm_batch.py",
        "OFP2_ManSkeleton": "ofp2_manskeleton.py"
    },
    "rvmat": {
        "PBR shader (VBS)": "pbr_vbs.rvmat_template",
        "Super Shader - Cloth": "super_cloth.rvmat_template",
        "Super Shader - Weapon": "super_weapon.rvmat_template"
    },
    "misc": {
        "Convert ATBX to A3OB": "convert_atbx_to_a3ob.py",
        "Convert BMTR to plain RTM": "convert_bmtr_to_rtm.py",
        "Create dummy P3D": "create_dummy_p3d.py"
    }
}


def get_scripts_directory():
    return os.path.join(addon_dir, "scripts")


def add_operators(layout, files):
    script_folder = get_scripts_directory()

    for name in files:
        op = layout.operator("text.open", text=name)
        op.filepath = os.path.join(script_folder, files[name])
        op.internal = True


class A3OB_MT_scripts_import(bpy.types.Menu):
    bl_label = "Import"

    def draw(self, context):
        add_operators(self.layout, scripts["import"])


class A3OB_MT_scripts_vertex_groups(bpy.types.Menu):
    bl_label = "Vertex Groups"

    def draw(self, context):
        add_operators(self.layout, scripts["vertex_groups"])


class A3OB_MT_scripts_rvmat(bpy.types.Menu):
    bl_label = "RVMAT Templates"

    def draw(self, context):
        add_operators(self.layout, scripts["rvmat"])


class A3OB_MT_scripts_misc(bpy.types.Menu):
    bl_label = "Misc"

    def draw(self, context):
        add_operators(self.layout, scripts["misc"])


class A3OB_MT_scripts(bpy.types.Menu):
    """Utility scripts from Arma 3 Object Builder"""

    bl_label = "Scripts"

    def draw(self, context):
        layout = self.layout
        layout.menu("A3OB_MT_scripts_import")
        layout.menu("A3OB_MT_scripts_vertex_groups")
        layout.menu("A3OB_MT_scripts_rvmat")
        layout.menu("A3OB_MT_scripts_misc")


classes = (
    A3OB_MT_scripts_import,
    A3OB_MT_scripts_vertex_groups,
    A3OB_MT_scripts_rvmat,
    A3OB_MT_scripts_misc,
    A3OB_MT_scripts
)


def draw_scripts_menu(self, context):
    self.layout.separator()
    self.layout.menu("A3OB_MT_scripts", text="Object Builder", icon_value=get_icon("addon"))


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.TEXT_MT_templates.append(draw_scripts_menu)
    
    print("\t" + "UI: Scripts")


def unregister():
    bpy.types.TEXT_MT_templates.remove(draw_scripts_menu)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    print("\t" + "UI: Scripts")
