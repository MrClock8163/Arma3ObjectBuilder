import os

import bpy

from ..utilities import structure as structutils
from ..utilities import generic as utils
from ..utilities import data


class A3OB_OT_check_convexity(bpy.types.Operator):
    """Find concave edges"""
    
    bl_label = "Find Non-Convexities"
    bl_idname = "a3ob.find_non_convexities"
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return len(context.selected_objects) == 1 and obj and obj.type == 'MESH'
    
    def execute(self, context):
        obj = context.active_object
        concaves = structutils.check_convexity(obj)
        
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='EDGE')
        
        if concaves > 0:
            self.report({'WARNING'}, "%s has %d concave edge(s)" % (obj.name, concaves))
        else:
            self.report({'INFO'}, "%s is convex" % obj.name)
        
        return {'FINISHED'}


class A3OB_OT_check_closed(bpy.types.Operator):
    """Find non-closed parts of model"""
    
    bl_label = "Find Non-Closed"
    bl_idname = "a3ob.find_non_closed"
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return len(context.selected_objects) == 1 and obj and obj.type == 'MESH'
    
    def execute(self,context):
        structutils.check_closed()
        return {'FINISHED'}


class A3OB_OT_convex_hull(bpy.types.Operator):
    """Calculate convex hull for entire object"""
    
    bl_label = "Convex Hull"
    bl_idname = "a3ob.convex_hull"
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return len(context.selected_objects) == 1 and obj and obj.type == 'MESH'
    
    def execute(self, context):
        mode = bpy.context.object.mode
        structutils.convex_hull()
        bpy.ops.object.mode_set(mode=mode)
        return {'FINISHED'}


class A3OB_OT_component_convex_hull(bpy.types.Operator):
    """Create convex named component selections"""
    
    bl_label = "Component Convex Hull"
    bl_idname = "a3ob.component_convex_hull"
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return len(context.selected_objects) == 1 and obj and obj.type == 'MESH'
    
    def execute(self,context):
        mode = bpy.context.object.mode
        obj = context.active_object
        count_components = structutils.component_convex_hull(obj)
        bpy.ops.object.mode_set(mode=mode)
        self.report({'INFO'}, "Created %d component(s) in %s" % (count_components, obj.name))
        return {'FINISHED'}


class A3OB_OT_find_components(bpy.types.Operator):
    """Create named component selections"""
    
    bl_label = "Find Components"
    bl_idname = "a3ob.find_components"
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return len(context.selected_objects) == 1 and obj and obj.type == 'MESH'
    
    def execute(self, context):
        mode = bpy.context.object.mode
        obj = context.active_object
        count_components, no_ignored = structutils.find_components(obj)
        bpy.ops.object.mode_set(mode=mode)
        if count_components > 0 and no_ignored:
            self.report({'INFO'}, "Created %d component(s) in %s" % (count_components, obj.name))
        elif count_components > 0:
            self.report({'WARNING'}, "Created %d component(s) in %s, non-closed components were ignored" % (count_components, obj.name))
        else:
            self.report({'ERROR'}, "There are no closed components in %s" % obj.name)
        return {'FINISHED'}


class A3OB_OT_move_top(bpy.types.Operator):
    """Move selected faces to top of face list (relative order of selected faces is maintained)"""
    
    bl_label = "Move Top"
    bl_idname = "a3ob.move_top"
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and len(context.selected_objects) == 1 and obj.type == 'MESH' and obj.mode == 'EDIT'
    
    def execute(self, context):
        bpy.ops.mesh.sort_elements(type='SELECTED', elements={'FACE'}, reverse=True)
        return {'FINISHED'}


class A3OB_OT_move_bottom(bpy.types.Operator):
    """Move selected faces to bottom of face list (relative order of selected faces is maintained)"""
    
    bl_label = "Move Bottom"
    bl_idname = "a3ob.move_bottom"
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and len(context.selected_objects) == 1 and obj.type == 'MESH' and obj.mode == 'EDIT'
    
    def execute(self, context):
        bpy.ops.mesh.sort_elements(type='SELECTED', elements={'FACE'})
        return {'FINISHED'}


class A3OB_OT_recalculate_normals(bpy.types.Operator):
    """Recalculate face normals"""
    
    bl_label = "Recalculate Normals"
    bl_idname = "a3ob.recalculate_normals"
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and len(context.selected_objects) == 1 and obj.type == 'MESH' and obj.mode == 'EDIT'
    
    def execute(self, context):
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
        return {'FINISHED'}


class A3OB_OT_cleanup_vertex_groups(bpy.types.Operator):
    """Cleanup vertex groups with no vertices assigned"""
    
    bl_label = "Delete Unused Groups"
    bl_idname = "a3ob.vertex_groups_cleanup"
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and len(obj.vertex_groups) > 0
        
    def execute(self, context):
        obj = context.active_object
        mode = obj.mode
        
        bpy.ops.object.mode_set(mode='OBJECT')
        
        removed = structutils.cleanup_vertex_groups(obj)
        
        bpy.ops.object.mode_set(mode=mode)
        
        if removed > 0:
            self.report({'INFO'} ,"Removed %d unused vertex group(s) from %s" % (removed, obj.name))
        else:
            self.report({'INFO'}, "There were no unused vertex group(s) found in %s" % obj.name)
        
        return {'FINISHED'}


class A3OB_OT_translate_vertex_groups(bpy.types.Operator):
    """Translate czech vertex group name to english where possible"""

    bl_label = "Translate Vertex Groups"
    bl_idname = "a3ob.vertex_groups_translate"

    @classmethod
    def poll(self, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and len(obj.vertex_groups) > 0

    def execute(self, context):
        obj = context.active_object

        for group in obj.vertex_groups:
            group.name = data.translations_czech_english.get(group.name.lower(), group.name)
        
        return {'FINISHED'}


class A3OB_OT_redefine_vertex_group(bpy.types.Operator):
    """Remove vertex group and recreate it with the selected verticies assigned"""

    bl_label = "Redefine Vertex Group"
    bl_idname = "a3ob.vertex_group_redefine"
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return len(context.selected_objects) == 1 and obj and obj.type == 'MESH' and obj.vertex_groups.active and obj.mode == 'EDIT'
        
    def execute(self, context):
        obj = context.active_object
        structutils.redefine_vertex_group(obj, context.scene.tool_settings.vertex_group_weight)
        return {'FINISHED'}


class A3OB_OT_open_changelog(bpy.types.Operator):
    """Open Arma 3 Object Builder add-on changelog"""

    bl_label = "Open Changelog"
    bl_idname = "a3ob.open_changelog"

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        path = os.path.join(utils.get_addon_directory(), "CHANGELOG.md")
        bpy.ops.text.open(filepath=path, internal=True)
        self.report({'INFO'}, "See CHANGELOG.md text block")

        return {'FINISHED'}


class A3OB_UL_common_data_base(bpy.types.UIList):
    icons = {
        'MATERIALS': 'MATERIAL',
        'NAMEDPROPS': 'PROPERTIES',
        'MATERIALS_PENETRATION': 'SNAP_VOLUME',
        'PROCEDURALS': 'NODE_TEXTURE',
        'PROXIES': 'EMPTY_AXIS'
    }
    # For some reason, these custom properties need to be defined on all
    # subclasses as well, otherwise they are not found and result in exceptions.
    # Most likely some issue with instantiating inherited bpy props.
    # Not an issue in newer API versions, but need to be accounted for for compatibility.
    filter_type: bpy.props.EnumProperty(
        name = "Type",
        items = (
            ('ALL', "All", "No filtering", 'NONE', 0),
            ('MATERIALS', "Material", "Visual materials", 'MATERIAL', 1),
            ('NAMEDPROPS', "Named Property", "Named properties", 'PROPERTIES', 2),
            ('MATERIALS_PENETRATION', "Penetration", "Penetration materials", 'SNAP_VOLUME', 4),
            ('PROCEDURALS', "Procedural", "Procedural texture strings", 'NODE_TEXTURE', 8),
            ('PROXIES', "Proxies", "Proxy models", 'EMPTY_AXIS', 16)
        ),
        default = 'ALL'
    )
    use_filter_name_invert: bpy.props.BoolProperty(
        name = "Invert",
        description = "Invert name filtering"
    )
    use_filter_sort_alpha: bpy.props.BoolProperty(
        name = "Sort By Name",
        description = "Sort items by their name",
        default = True
    )

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        text = item.name
        if item.type == 'NAMEDPROPS':
            text = "%s = %s" % (item.name, item.value)

        layout.label(text=text, icon=self.icons.get(item.type, 'NONE'))
    
    def draw_filter_name(self, layout):
        row = layout.row(align=True)
        row.prop(self, "filter_name", text="")
        row.prop(self, "use_filter_name_invert", text="", icon='ARROW_LEFTRIGHT')
        row.separator()
        row.prop(self, "use_filter_sort_alpha", text="", icon='SORTALPHA')
        row.prop(self, "use_filter_sort_reverse", text="", icon='SORT_DESC' if self.use_filter_sort_reverse else 'SORT_ASC')
    
    def draw_filter(self, context, layout):
        row_filter = layout.row(align=True)
        row_filter.prop(self, "filter_type", text="")

        self.draw_filter_name(layout)
    
    def filter_items(self, context, data, property):
        mats = getattr(data, property)

        helper_funcs = bpy.types.UI_UL_list
        flt_flags = []
        flt_neworder = []

        if self.filter_name:
            flt_flags = helper_funcs.filter_items_by_name(self.filter_name, self.bitflag_filter_item, mats, "name", reverse=self.use_filter_name_invert)
        
        if not flt_flags:
            flt_flags = [self.bitflag_filter_item] * len(mats)

        if self.filter_type != 'ALL':
            for i, mat in enumerate(mats):
                if mat.type == self.filter_type:
                    continue

                flt_flags[i] = 0

        if self.use_filter_sort_alpha:
            flt_neworder = helper_funcs.sort_items_by_name(mats, "name")

        return flt_flags, flt_neworder


class A3OB_UL_common_data_materials(A3OB_UL_common_data_base):
    filter_type: bpy.props.EnumProperty(
        name = "Type",
        items = (
            ('MATERIALS', "Material", "Visual materials", 'MATERIAL', 0),
            ('MATERIALS_PENETRATION', "Penetration", "Penetration materials", 'SNAP_VOLUME', 1)
        ),
        default = 'MATERIALS'
    )
    use_filter_name_invert: bpy.props.BoolProperty(
        name = "Invert",
        description = "Invert name filtering"
    )
    use_filter_sort_alpha: bpy.props.BoolProperty(
        name = "Sort By Name",
        description = "Sort items by their name",
        default = True
    )


class A3OB_UL_common_data_namedprops(A3OB_UL_common_data_base):
    filter_type: bpy.props.EnumProperty(
        name = "Type",
        items = (
            ('NAMEDPROPS', "Named Property", "Named properties", 'PROPERTIES', 0),
        ),
        default = 'NAMEDPROPS'
    )
    use_filter_name_invert: bpy.props.BoolProperty(
        name = "Invert",
        description = "Invert name filtering"
    )
    use_filter_sort_alpha: bpy.props.BoolProperty(
        name = "Sort By Name",
        description = "Sort items by their name",
        default = True
    )
    def draw_filter(self, context, layout):
        self.draw_filter_name(layout)


class A3OB_UL_common_data_procedurals(A3OB_UL_common_data_base):
    filter_type: bpy.props.EnumProperty(
        name = "Type",
        items = (
            ('PROCEDURALS', "Procedural", "Procedural texture strings", 'NODE_TEXTURE', 0),
        ),
        default = 'PROCEDURALS'
    )
    use_filter_name_invert: bpy.props.BoolProperty(
        name = "Invert",
        description = "Invert name filtering"
    )
    use_filter_sort_alpha: bpy.props.BoolProperty(
        name = "Sort By Name",
        description = "Sort items by their name",
        default = True
    )
    def draw_filter(self, context, layout):
        self.draw_filter_name(layout)


class A3OB_UL_common_data_proxies(A3OB_UL_common_data_base):
    filter_type: bpy.props.EnumProperty(
        name = "Type",
        items = (
            ('PROXIES', "Proxies", "Proxy models", 'EMPTY_AXIS', 0),
        ),
        default = 'PROXIES'
    )
    use_filter_name_invert: bpy.props.BoolProperty(
        name = "Invert",
        description = "Invert name filtering"
    )
    use_filter_sort_alpha: bpy.props.BoolProperty(
        name = "Sort By Name",
        description = "Sort items by their name",
        default = True
    )
    def draw_filter(self, context, layout):
        self.draw_filter_name(layout)


class A3OB_MT_object_builder_topo(bpy.types.Menu):
    """Object Builder topology functions"""
    
    bl_label = "Topology"
    
    def draw(self, context):
        self.layout.operator("a3ob.find_non_closed")
        self.layout.operator("a3ob.find_components")


class A3OB_MT_object_builder_convexity(bpy.types.Menu):
    """Object Builder convexity functions"""
    
    bl_label = "Convexity"
    
    def draw(self, context):
        self.layout.operator("a3ob.find_non_convexities")
        self.layout.operator("a3ob.convex_hull")
        self.layout.operator("a3ob.component_convex_hull")


class A3OB_MT_object_builder_faces(bpy.types.Menu):
    """Object Builder face functions"""
    
    bl_label = "Faces"
    
    def draw(self, context):
        self.layout.operator("a3ob.move_top")
        self.layout.operator("a3ob.move_bottom")
        self.layout.operator("a3ob.recalculate_normals")


class A3OB_MT_object_builder_misc(bpy.types.Menu):
    """Object Builder miscellaneous functions"""
    
    bl_label = "Misc"
    
    def draw(self, context):
        self.layout.operator("a3ob.vertex_groups_cleanup")


class A3OB_MT_object_builder(bpy.types.Menu):
    """Arma 3 Object Builder utility functions"""
    
    bl_label = "Object Builder"
    
    def draw(self, context):
        self.layout.menu("A3OB_MT_object_builder_topo")
        self.layout.menu("A3OB_MT_object_builder_convexity")
        self.layout.menu("A3OB_MT_object_builder_faces")
        self.layout.menu("A3OB_MT_object_builder_misc")


class A3OB_MT_vertex_groups(bpy.types.Menu):
    """Object Builder utility functions"""

    bl_label = "Utilities"

    def draw(self, context):
        layout = self.layout
        layout.operator("a3ob.find_components", icon='STICKY_UVS_DISABLE')
        layout.separator()
        layout.operator("a3ob.vertex_group_redefine", icon='FILE_REFRESH')
        layout.operator("a3ob.vertex_groups_translate", icon='SYNTAX_OFF')
        layout.separator()
        layout.operator("a3ob.vertex_groups_cleanup", icon='TRASH')


class A3OB_MT_help(bpy.types.Menu):
    """Object Builder add-on docs"""

    bl_label = "Object Builder"

    def draw(self, context):
        layout = self.layout

        layout.operator("wm.url_open", text="Documentation", icon='HELP').url = "https://mrcmodding.gitbook.io/arma-3-object-builder/home"
        layout.operator("wm.url_open", text="Quick Start Reference", icon='URL').url = "https://mrcmodding.gitbook.io/arma-3-object-builder/quick-start-reference"
        layout.separator()
        layout.operator("wm.url_open", text="Releases", icon='URL').url = "https://github.com/MrClock8163/Arma3ObjectBuilder/releases"
        layout.operator("wm.url_open", text="Issue Tracker", icon='URL').url = "https://github.com/MrClock8163/Arma3ObjectBuilder/issues"
        layout.operator("a3ob.open_changelog", text="Changelog", icon='TEXT')


classes = (
    A3OB_OT_check_convexity,
    A3OB_OT_check_closed,
    A3OB_OT_convex_hull,
    A3OB_OT_component_convex_hull,
    A3OB_OT_find_components,
    A3OB_OT_move_top,
    A3OB_OT_move_bottom,
    A3OB_OT_recalculate_normals,
    A3OB_OT_cleanup_vertex_groups,
    A3OB_OT_translate_vertex_groups,
    A3OB_OT_redefine_vertex_group,
    A3OB_OT_open_changelog,
    A3OB_UL_common_data_base,
    A3OB_UL_common_data_materials,
    A3OB_UL_common_data_namedprops,
    A3OB_UL_common_data_procedurals,
    A3OB_UL_common_data_proxies,
    A3OB_MT_object_builder,
    A3OB_MT_object_builder_topo,
    A3OB_MT_object_builder_faces,
    A3OB_MT_object_builder_convexity,
    A3OB_MT_object_builder_misc,
    A3OB_MT_vertex_groups,
    A3OB_MT_help
)


def menu_func(self, context):
    self.layout.separator()
    col = self.layout.column()
    col.ui_units_x = 5.2
    col.menu("A3OB_MT_object_builder", icon_value=utils.get_icon("addon"))


def vertex_groups_func(self, context):
    layout = self.layout
    row = layout.row(align=True)
    row.alignment = 'RIGHT'
    row.menu("A3OB_MT_vertex_groups", text="", icon_value=utils.get_icon("addon"))


def menu_help_func(self, context):
    self.layout.separator()
    self.layout.menu("A3OB_MT_help", icon_value=utils.get_icon("addon"))


def register():
    from bpy.utils import register_class
    
    for cls in classes:
        register_class(cls)
    
    bpy.types.VIEW3D_MT_editor_menus.append(menu_func)
    bpy.types.DATA_PT_vertex_groups.append(vertex_groups_func)
    bpy.types.TOPBAR_MT_help.append(menu_help_func)
    
    print("\t" + "UI: Utility functions")


def unregister():
    from bpy.utils import unregister_class

    bpy.types.TOPBAR_MT_help.remove(menu_help_func)
    bpy.types.DATA_PT_vertex_groups.remove(vertex_groups_func)
    bpy.types.VIEW3D_MT_editor_menus.remove(menu_func)

    for cls in reversed(classes):
        unregister_class(cls)
    
    print("\t" + "UI: Utility functions")
