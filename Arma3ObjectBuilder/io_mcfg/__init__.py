# flake8: noqa: F722,E821
from typing import TextIO

import bpy
import bpy_extras

from . import importer, exporter
from .validator import SkeletonValidator
from ..utils import op_report
from ..utils_io import ExportFileHandler
from ..logger import ProcessLoggerNull
from ..types import OperatorReturn, Registerable


class A3OB_OT_import_mcfg(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """Import Arma 3 skeleton definition"""

    bl_idname = "a3ob.import_mcfg"
    bl_label = "Import Skeletons"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}
    filename_ext = ".cfg"

    filter_glob: bpy.props.StringProperty(
        default="*.cfg",
        options={'HIDDEN'}
    )
    force_lowercase: bpy.props.BoolProperty(
        name="Force Lowercase",
        description="Import all bone names as lowercase",
        default=True
    )
    protected: bpy.props.BoolProperty(
        name="Protected",
        description="Import skeletons as protected",
        default=True
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def draw(self, context: bpy.types.Context) -> None:
        pass

    def execute(self, context: bpy.types.Context) -> OperatorReturn:
        count_skeletons = importer.read_file(self, context)

        if count_skeletons > 0:
            op_report(self, {'INFO'}, "Successfully imported %d skeleton(s)" % count_skeletons)
            return {'FINISHED'}

        op_report(self, {'ERROR'}, "Could not import any skeletons (check the system console)")

        return {'FINISHED'}


class A3OB_PT_import_mcfg_main(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Main"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        sfile = context.space_data
        operator: bpy.types.Operator = sfile.active_operator  # type: ignore[attr-defined]

        return operator.bl_idname == "A3OB_OT_import_mcfg"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        sfile = context.space_data
        operator = sfile.active_operator  # type: ignore[attr-defined]

        layout.prop(operator, "force_lowercase")
        layout.prop(operator, "protected")


class A3OB_OT_export_mcfg(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    """Export Arma 3 skeleton definition"""

    bl_idname = "a3ob.export_mcfg"
    bl_label = "Export Skeleton"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}
    filename_ext = ".cfg"

    filter_glob: bpy.props.StringProperty(
        default="*.cfg",
        options={'HIDDEN'}
    )
    force_lowercase: bpy.props.BoolProperty(
        name="Force Lowercase",
        description="Export all bone names as lowercase",
        default=True
    )
    skeleton_index: bpy.props.IntProperty(
        name="Skeleton To Export",
        default=0
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        scene_props = context.scene.a3ob_rigging  # type: ignore[attr-defined]
        return len(scene_props.skeletons) > 0

    def draw(self, context: bpy.types.Context) -> None:
        pass

    def execute(self, context: bpy.types.Context) -> OperatorReturn:
        scene_props = context.scene.a3ob_rigging  # type: ignore[attr-defined]
        skeleton = scene_props.skeletons[self.skeleton_index]

        validator = SkeletonValidator(ProcessLoggerNull())
        if not validator.validate(skeleton, False, True):
            op_report(self, {'ERROR'}, "Invalid skeleton definiton, run skeleton validation for more info")
            return {'FINISHED'}

        file: TextIO
        with ExportFileHandler(self.filepath, "w") as file:  # type: ignore[attr-defined, assignment]
            exporter.write_file(self, skeleton, file)
            op_report(self, {'INFO'}, "Successfuly exported %s" % skeleton.name)

        return {'FINISHED'}


class A3OB_PT_export_mcfg_main(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Main"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        sfile = context.space_data
        operator: bpy.types.Operator = sfile.active_operator  # type: ignore[attr-defined]

        return operator.bl_idname == "A3OB_OT_export_mcfg"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        sfile = context.space_data
        operator = sfile.active_operator  # type: ignore[attr-defined]
        scene_props = context.scene.a3ob_rigging  # type: ignore[attr-defined]

        layout.template_list(
            "A3OB_UL_rigging_skeletons_noedit",
            "A3OB_armature_skeletons",
            scene_props,
            "skeletons",
            operator,
            "skeleton_index",
            rows=3
        )
        layout.prop(operator, "force_lowercase")


classes: tuple[Registerable, ...] = (
    A3OB_OT_import_mcfg,
    A3OB_PT_import_mcfg_main,
    A3OB_OT_export_mcfg,
    A3OB_PT_export_mcfg_main
)

if bpy.app.version >= (4, 1, 0):
    class A3OB_FH_import_mcfg(bpy.types.FileHandler):
        bl_label = "File handler for MCFG import"
        bl_import_operator = "a3ob.import_mcfg"
        bl_file_extensions = ".cfg"

        @classmethod
        def poll_drop(cls, context: bpy.types.Context) -> bool:
            return bool(context.area and context.area.type == 'VIEW_3D')

    classes = (*classes, A3OB_FH_import_mcfg)


def menu_func_import(self: bpy.types.Menu, context: bpy.types.Context) -> None:
    self.layout.operator(A3OB_OT_import_mcfg.bl_idname, text="Arma 3 skeletons (model.cfg)")


def menu_func_export(self: bpy.types.Menu, context: bpy.types.Context) -> None:
    self.layout.operator(A3OB_OT_export_mcfg.bl_idname, text="Arma 3 skeleton (model.cfg)")


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)  # type: ignore[no-untyped-call]
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)  # type: ignore[no-untyped-call]

    print("\t" + "IO: MCFG")


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)  # type: ignore[no-untyped-call]
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)  # type: ignore[no-untyped-call]

    print("\t" + "IO: MCFG")
