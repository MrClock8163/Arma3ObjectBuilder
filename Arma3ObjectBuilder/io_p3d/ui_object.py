import bpy

from .data import P3D_LOD_Resolution as LODRes
from . import flags as p3d_flags
from . import utils as p3d_utils
from .. import get_prefs, get_icon
from .. import utils


bl_version = bpy.app.version


class A3OB_OT_proxy_add(bpy.types.Operator):
    """Add an Arma 3 proxy object and parent to the active object"""
    
    bl_idname = "a3ob.proxy_add"
    bl_label = "Add Proxy"
    bl_options = {'REGISTER'}

    parent: bpy.props.StringProperty(
        name = "Parent LOD Object",
        description = "Name of the LOD object to parent the new proxy to"
    )
    path: bpy.props.StringProperty (
        name = "Proxy Path",
        description = "Proxy file path to assign to new proxy object"
    )
    
    @classmethod
    def poll(cls, context):
        return True
        
    def execute(self, context):
        proxy_object = p3d_utils.create_proxy()
        proxy_object.display_type = 'WIRE'
        proxy_object.show_name = True
        proxy_object.location = context.scene.cursor.location

        parent = context.scene.objects.get(self.parent, context.active_object)
        if parent:
            parent.users_collection[0].objects.link(proxy_object)
            proxy_object.parent = parent
            proxy_object.matrix_parent_inverse = parent.matrix_world.inverted()
        else:
            context.collection.objects.link(proxy_object)

        proxy_object.a3ob_properties_object_proxy.proxy_path = self.path
        return {'FINISHED'}


class A3OB_OT_proxy_remove(bpy.types.Operator):
    """Remove an Arma 3 proxy object from the active object"""

    bl_idname = "a3ob.proxy_remove"
    bl_label = "Remove Proxy"
    bl_options = {'REGISTER'}

    obj: bpy.props.StringProperty(
        name = "Proxy Object",
        description = "Name of the proxy object to remove"
    )

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        obj = context.scene.objects.get(self.obj, context.active_object)
        if not obj or obj.type != 'MESH' or not obj.a3ob_properties_object_proxy.is_a3_proxy:
            self.report({'ERROR'}, "Cannot remove proxy")
            return {'FINISHED'}
        
        bpy.data.meshes.remove(obj.data)

        return {'FINISHED'}


class A3OB_OT_paste_common_proxy(bpy.types.Operator):
    """Paste a common proxy model path"""
    
    bl_idname = "a3ob.paste_common_proxy"
    bl_label = "Paste Common Proxy"
    bl_options = {'REGISTER'}

    obj: bpy.props.StringProperty(
        name = "Proxy Object",
        description = "Proxy object to assign path to"
    )
    
    @classmethod
    def poll(cls, context):
        return True
    
    def invoke(self, context, event):
        utils.load_common_data(context.scene)
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        scene_props = context.scene.a3ob_commons
        layout = self.layout
        layout.template_list("A3OB_UL_common_data_proxies", "A3OB_proxies_common", scene_props, "items", scene_props, "items_index", item_dyntip_propname="value")
    
    def execute(self, context):
        obj = context.scene.objects.get(self.obj, context.object)
        if not obj or obj.type != 'MESH' or not obj.a3ob_properties_object_proxy.is_a3_proxy:
            self.report({'ERROR'}, "No proxy object was selected")
            return {'FINISHED'}

        scene_props = context.scene.a3ob_commons
        
        if utils.is_valid_idx(scene_props.items_index, scene_props.items):
            new_item = scene_props.items[scene_props.items_index]
            obj.a3ob_properties_object_proxy.proxy_path = new_item.value
            
        return {'FINISHED'}


class A3OB_OT_namedprops_add(bpy.types.Operator):
    """Add named property to the active object"""
    
    bl_idname = "a3ob.namedprops_add"
    bl_label = "Add Named Property"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH'
        
    def execute(self, context):
        obj = context.object
        object_props = obj.a3ob_properties_object
        item = object_props.properties.add()
        item.name = "New property"
        item.value = "no value"
        object_props.property_index = len(object_props.properties) - 1
        
        return {'FINISHED'}


class A3OB_OT_namedprops_remove(bpy.types.Operator):
    """Remove named property from the active object"""
    
    bl_idname = "a3ob.namedprops_remove"
    bl_label = "Remove Named Property"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        if not obj:
            return False
        object_props = obj.a3ob_properties_object
        return obj.type == 'MESH' and utils.is_valid_idx(object_props.property_index, object_props.properties)
        
    def execute(self, context):
        obj = context.object
        object_props = obj.a3ob_properties_object
        index = object_props.property_index
        if index != -1:
            object_props.properties.remove(index)
            if len(object_props.properties) == 0:
                object_props.property_index = -1
            elif index > len(object_props.properties) - 1:
                object_props.property_index = len(object_props.properties) - 1            
        
        return {'FINISHED'}


class A3OB_OT_paste_common_namedprop(bpy.types.Operator):
    """Add a common named property"""
    
    bl_label = "Paste Common Named Property"
    bl_idname = "a3ob.paste_common_namedprop"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH'
    
    def invoke(self, context, event):
        utils.load_common_data(context.scene)
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        scene_props = context.scene.a3ob_commons
        layout = self.layout
        layout.template_list("A3OB_UL_common_data_namedprops", "A3OB_common_namedprops", scene_props, "items", scene_props, "items_index")

    def execute(self, context):
        obj = context.object
        scene_props = context.scene.a3ob_commons
        
        if utils.is_valid_idx(scene_props.items_index, scene_props.items):
            new_item = scene_props.items[scene_props.items_index]
            object_props = obj.a3ob_properties_object
            item = object_props.properties.add()
            item.name = new_item.name
            item.value = new_item.value
            object_props.property_index = len(object_props.properties) - 1
        
        return {'FINISHED'}


class A3OB_OT_lod_copy_add(bpy.types.Operator):
    """Add copy directive to active object"""
    
    bl_idname = "a3ob.lod_copy_add"
    bl_label = "Add Copy"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH'
        
    def execute(self, context):
        obj = context.object
        object_props = obj.a3ob_properties_object
        object_props.copies.add()
        object_props.copies_index = len(object_props.copies) - 1
        
        return {'FINISHED'}


class A3OB_OT_lod_copy_remove(bpy.types.Operator):
    """Remove copy directive from the active object"""
    
    bl_idname = "a3ob.lod_copy_remove"
    bl_label = "Remove Copy"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        if not obj:
            return False
        object_props = obj.a3ob_properties_object
        return obj.type == 'MESH' and utils.is_valid_idx(object_props.copies_index, object_props.copies)
        
    def execute(self, context):
        obj = context.object
        object_props = obj.a3ob_properties_object
        index = object_props.copies_index
        if index != -1:
            object_props.copies.remove(index)
            if len(object_props.copies) == 0:
                object_props.copies_index = -1
            elif index > len(object_props.properties) - 1:
                object_props.copies_index = len(object_props.copies) - 1            
        
        return {'FINISHED'}


class A3OB_OT_flags_vertex_add(bpy.types.Operator):
    """Add a new vertex flag group to the active object"""
    
    bl_label = "Add Vertex Flag Group"
    bl_idname = "a3ob.flags_vertex_add"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH'
    
    def execute(self, context):
        obj = context.object
        flag_props = obj.a3ob_properties_object_flags
        item = flag_props.vertex.add()
        item.name = "New Flag Group"
        item.set_flag(get_prefs().flag_vertex)
        flag_props.vertex_index = len(flag_props.vertex) - 1
        
        return {'FINISHED'}


class A3OB_OT_flags_vertex_remove(bpy.types.Operator):
    """Remove the active vertex flag group from the active object"""
    
    bl_idname = "a3ob.flags_vertex_remove"
    bl_label = "Remove Vertex Flag Group"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH' and utils.is_valid_idx(obj.a3ob_properties_object_flags.vertex_index, obj.a3ob_properties_object_flags.vertex)
        
    def execute(self, context):
        obj = context.object
        flag_props = obj.a3ob_properties_object_flags
        index = flag_props.vertex_index

        flag_props.vertex.remove(index)
        flag_props.vertex_index = len(flag_props.vertex) - 1            
    
        p3d_flags.remove_group_vertex(obj, index)
        
        return {'FINISHED'}


class A3OB_OT_flags_vertex_assign(bpy.types.Operator):
    """Assign selected vertices to the active vertex flag group"""
    
    bl_label = "Assign"
    bl_idname = "a3ob.flags_vertex_assign"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH' and obj.mode == 'EDIT' and utils.is_valid_idx(obj.a3ob_properties_object_flags.vertex_index, obj.a3ob_properties_object_flags.vertex)
    
    def execute(self, context):
        obj = context.object
        flag_props = obj.a3ob_properties_object_flags
        p3d_flags.assign_group_vertex(obj, flag_props.vertex_index)
        
        return {'FINISHED'}


class A3OB_OT_flags_vertex_select(bpy.types.Operator):
    """Select all vertices assigned to the active vertex flag group"""
    
    bl_label = "Select"
    bl_idname = "a3ob.flags_vertex_select"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH' and obj.mode == 'EDIT' and utils.is_valid_idx(obj.a3ob_properties_object_flags.vertex_index, obj.a3ob_properties_object_flags.vertex)
    
    def execute(self, context):
        obj = context.object
        flag_props = obj.a3ob_properties_object_flags
        p3d_flags.select_group_vertex(obj, flag_props.vertex_index)
        bpy.ops.mesh.select_mode(type='VERT')
        
        return {'FINISHED'}


class A3OB_OT_flags_vertex_deselect(bpy.types.Operator):
    """Deselect all selected vertices assigned to the active vertex flag group"""
    
    bl_label = "Deselect"
    bl_idname = "a3ob.flags_vertex_deselect"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH' and obj.mode == 'EDIT' and utils.is_valid_idx(obj.a3ob_properties_object_flags.vertex_index, obj.a3ob_properties_object_flags.vertex)
    
    def execute(self, context):
        obj = context.object
        flag_props = obj.a3ob_properties_object_flags
        p3d_flags.select_group_vertex(obj, flag_props.vertex_index, False)
        bpy.ops.mesh.select_mode(type='VERT')
        
        return {'FINISHED'}


class A3OB_OT_flags_vertex_clear(bpy.types.Operator):
    """Clear all vertex flag groups from the active object"""
    
    bl_label = "Clear"
    bl_idname = "a3ob.flags_vertex_clear"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH' and len(obj.a3ob_properties_object_flags.vertex) > 0
    
    def execute(self, context):
        obj = context.object
        p3d_flags.clear_groups_vertex(obj)

        return {'FINISHED'}


class A3OB_OT_flags_face_add(bpy.types.Operator):
    """Add a new face flag group to the active object"""
    
    bl_label = "Add Face Flag Group"
    bl_idname = "a3ob.flags_face_add"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH'
    
    def execute(self, context):
        obj = context.object
        flag_props = obj.a3ob_properties_object_flags
        item = flag_props.face.add()
        item.name = "New Flag Group"
        item.set_flag(get_prefs().flag_face)
        flag_props.face_index = len(flag_props.face) - 1
        
        return {'FINISHED'}


class A3OB_OT_flags_face_remove(bpy.types.Operator):
    """Remove the active face flag group from the active object"""
    
    bl_idname = "a3ob.flags_face_remove"
    bl_label = "Remove Face Flag Group"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH' and utils.is_valid_idx(obj.a3ob_properties_object_flags.face_index, obj.a3ob_properties_object_flags.face)
        
    def execute(self, context):
        obj = context.object
        flag_props = obj.a3ob_properties_object_flags
        index = flag_props.face_index
        
        flag_props.face.remove(index)
        flag_props.face_index = len(flag_props.face) - 1            
        
        p3d_flags.remove_group_face(obj, index)
        
        return {'FINISHED'}


class A3OB_OT_flags_face_assign(bpy.types.Operator):
    """Assign selected vertices to the active face flag group"""
    
    bl_label = "Assign"
    bl_idname = "a3ob.flags_face_assign"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH' and obj.mode == 'EDIT' and utils.is_valid_idx(obj.a3ob_properties_object_flags.face_index, obj.a3ob_properties_object_flags.face)
    
    def execute(self, context):
        obj = context.object
        flag_props = obj.a3ob_properties_object_flags
        p3d_flags.assign_group_face(obj, flag_props.face_index)
        
        return {'FINISHED'}


class A3OB_OT_flags_face_select(bpy.types.Operator):
    """Select all vertices assigned to the active face flag group"""
    
    bl_label = "Select"
    bl_idname = "a3ob.flags_face_select"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH' and obj.mode == 'EDIT' and utils.is_valid_idx(obj.a3ob_properties_object_flags.face_index, obj.a3ob_properties_object_flags.face)
    
    def execute(self, context):
        obj = context.object
        flag_props = obj.a3ob_properties_object_flags
        p3d_flags.select_group_face(obj, flag_props.face_index)
        bpy.ops.mesh.select_mode(type='FACE')
        
        return {'FINISHED'}


class A3OB_OT_flags_face_deselect(bpy.types.Operator):
    """Deselect all selected vertices assigned to the active face flag group"""
    
    bl_label = "Deselect"
    bl_idname = "a3ob.flags_face_deselect"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH' and obj.mode == 'EDIT' and utils.is_valid_idx(obj.a3ob_properties_object_flags.face_index, obj.a3ob_properties_object_flags.face)
    
    def execute(self, context):
        obj = context.object
        flag_props = obj.a3ob_properties_object_flags
        p3d_flags.select_group_face(obj, flag_props.face_index, False)
        bpy.ops.mesh.select_mode(type='FACE')
        
        return {'FINISHED'}


class A3OB_OT_flags_face_clear(bpy.types.Operator):
    """Clear all face flag groups from the active object"""
    
    bl_label = "Clear"
    bl_idname = "a3ob.flags_face_clear"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH' and len(obj.a3ob_properties_object_flags.face) > 0
    
    def execute(self, context):
        obj = context.object
        p3d_flags.clear_groups_face(obj)

        return {'FINISHED'}


class A3OB_UL_namedprops(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.alignment = 'LEFT'
        layout.label(text="", icon='PROPERTIES')
        layout.prop(item, "name", text="", emboss=bool(bl_version >= (3, 3, 0)))
        layout.label(text="=")
        layout.prop(item, "value", text="", emboss=bool(bl_version >= (3, 3, 0)))


class A3OB_UL_lod_copies(bpy.types.UIList):
    def draw_item(self, context, layout, _data, item, icon, active_data, active_propname):
        layout.alignment = 'LEFT'
        layout.prop(item, "lod", text="", emboss=False)
        lod_idx = int(item.lod)
        if lod_idx in LODRes.LODS_WITH_RESOLUTION:
            layout.prop(item, "resolution", text="", emboss=False)
        elif lod_idx == LODRes.UNKNOWN:
            layout.prop(item, "resolution_float", text="", emboss=False)


class A3OB_UL_common_proxies(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.label(text=item.name)


class A3OB_UL_flags_vertex(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.prop(item, "name", text="", emboss=False)
        layout.label(text=("%08x" % item.get_flag()))


class A3OB_UL_flags_face(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.prop(item, "name", text="", emboss=False)
        layout.label(text=("%08x" % item.get_flag()))


class A3OB_UL_proxy_access(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        row = layout.row(align=True)
        op = row.operator("a3ob.select_object", text="", icon='RESTRICT_SELECT_OFF', emboss=False)
        op.object_name = item.obj
        row.label(text=" %s" % item.name)
    
    def filter_items(self, context, data, propname):
        helper_funcs = bpy.types.UI_UL_list
        flt_flags = []
        flt_neworder = []
        
        sorter = getattr(data, propname)
        flt_neworder = helper_funcs.sort_items_by_name(sorter, "name")
        
        return flt_flags, flt_neworder


class A3OB_PT_object_mesh(bpy.types.Panel, utils.PanelHeaderLinkMixin):
    bl_region_type = 'WINDOW'
    bl_space_type = 'PROPERTIES'
    bl_label = "Object Builder: LOD Properties"
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}

    doc_url = "https://mrcmodding.gitbook.io/arma-3-object-builder/properties/lod"
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH' and not obj.a3ob_properties_object_proxy.is_a3_proxy
        
    def draw(self, context):
        obj = context.object
        object_props = obj.a3ob_properties_object
        
        layout = self.layout
        row_toggle = layout.row(align=True)
        row_toggle.prop(object_props, "is_a3_lod", text="Is P3D LOD", toggle=True)
        
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        if object_props.is_a3_lod:
            layout.prop(object_props, "lod", text="Type")
            lod_idx = int(object_props.lod)
            if lod_idx in LODRes.LODS_WITH_RESOLUTION:
                layout.prop(object_props, "resolution")
            elif lod_idx == LODRes.UNKNOWN:
                layout.prop(object_props, "resolution_float")


class A3OB_PT_object_mesh_namedprops(bpy.types.Panel):
    bl_region_type = 'WINDOW'
    bl_space_type = 'PROPERTIES'
    bl_label = "Named Properties"
    bl_context = "data"
    bl_parent_id = "A3OB_PT_object_mesh"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH' and obj.a3ob_properties_object.is_a3_lod and not obj.a3ob_properties_object_proxy.is_a3_proxy
    
    def draw(self, context):
        obj = context.object
        object_props = obj.a3ob_properties_object
        
        layout = self.layout
        row = layout.row()
        col_list = row.column()
        col_list.template_list("A3OB_UL_namedprops", "A3OB_namedprops", object_props, "properties", object_props, "property_index")
            
        col_operators = row.column(align=True)
        col_operators.operator("a3ob.namedprops_add", text="", icon='ADD')
        col_operators.operator("a3ob.namedprops_remove", text="", icon='REMOVE')
        col_operators.separator()
        col_operators.operator("a3ob.paste_common_namedprop", icon='PASTEDOWN', text="")


class A3OB_PT_object_mesh_proxies(bpy.types.Panel):
    bl_region_type = 'WINDOW'
    bl_space_type = 'PROPERTIES'
    bl_label = "Proxy Access"
    bl_context = "data"
    bl_parent_id = "A3OB_PT_object_mesh"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH' and obj.a3ob_properties_object.is_a3_lod and not obj.a3ob_properties_object_proxy.is_a3_proxy
    
    def draw(self, context):
        layout = self.layout
        scene_props = context.scene.a3ob_proxy_access

        layout = self.layout
        row = layout.row()
        col_list = row.column()
        col_list.template_list("A3OB_UL_proxy_access", "A3OB_proxy_access", scene_props, "proxies", scene_props, "proxies_index")

        col_operators = row.column(align=True)
        op_add = col_operators.operator("a3ob.proxy_add", text="", icon='ADD')
        op_add.parent = context.object.name
        op_remove = col_operators.operator("a3ob.proxy_remove", text="", icon='REMOVE')

        if not utils.is_valid_idx(scene_props.proxies_index, scene_props.proxies):
            return
        
        proxy = context.scene.objects.get(scene_props.proxies[scene_props.proxies_index].obj)
        if not proxy:
            return
        
        op_remove.obj = proxy.name
        proxy_props = proxy.a3ob_properties_object_proxy
        row_path = col_list.row(align=True)
        op_common = row_path.operator("a3ob.paste_common_proxy", text="", icon='PASTEDOWN')
        op_common.obj = proxy.name
        row_path.prop(proxy_props, "proxy_path", text="", icon='MESH_CUBE')
        col_list.prop(proxy_props, "proxy_index")


class A3OB_PT_object_mesh_copies(bpy.types.Panel):
    bl_region_type = 'WINDOW'
    bl_space_type = 'PROPERTIES'
    bl_label = "Copies"
    bl_context = "data"
    bl_parent_id = "A3OB_PT_object_mesh"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH' and obj.a3ob_properties_object.is_a3_lod and not obj.a3ob_properties_object_proxy.is_a3_proxy

    def draw(self, context):
        obj = context.object
        object_props = obj.a3ob_properties_object

        layout = self.layout
        row = layout.row()
        col_list = row.column()
        col_list.template_list("A3OB_UL_lod_copies", "A3OB_lod_copies", object_props, "copies", object_props, "copies_index")
            
        col_operators = row.column(align=True)
        col_operators.operator("a3ob.lod_copy_add", text="", icon='ADD')
        col_operators.operator("a3ob.lod_copy_remove", text="", icon='REMOVE')


class A3OB_PT_object_mesh_flags(bpy.types.Panel, utils.PanelHeaderLinkMixin):
    bl_region_type = 'WINDOW'
    bl_space_type = 'PROPERTIES'
    bl_label = "Object Builder: Flag Groups"
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}

    doc_url = "https://mrcmodding.gitbook.io/arma-3-object-builder/properties/flag-groups"

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH' and not obj.a3ob_properties_object_proxy.is_a3_proxy

    def draw(self, context):
        pass


class A3OB_PT_object_mesh_flags_vertex(bpy.types.Panel):
    bl_region_type = 'WINDOW'
    bl_space_type = 'PROPERTIES'
    bl_label = "Vertex Flag Groups"
    bl_context = "data"
    bl_parent_id = "A3OB_PT_object_mesh_flags"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH' and not obj.a3ob_properties_object_proxy.is_a3_proxy
    
    def draw(self, context):
        obj = context.object
        flag_props = obj.a3ob_properties_object_flags
        
        layout = self.layout
        row = layout.row()
        col_list = row.column()
        col_list.template_list("A3OB_UL_flags_vertex", "A3OB_flags_vertex", flag_props, "vertex", flag_props, "vertex_index")
        
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        if utils.is_valid_idx(flag_props.vertex_index, flag_props.vertex):
            if obj.mode == 'EDIT':
                row_operators = layout.row(align=True)
                row_operators.operator("a3ob.flags_vertex_assign")
                row_operators.operator("a3ob.flags_vertex_select")
                row_operators.operator("a3ob.flags_vertex_deselect")
            
            prop = flag_props.vertex[flag_props.vertex_index]
            layout.prop(prop, "surface")
            layout.prop(prop, "fog")
            layout.prop(prop, "decal")
            layout.prop(prop, "lighting")
            layout.prop(prop, "normals")
            layout.prop(prop, "hidden")
            
        col_operators = row.column(align=True)
        col_operators.operator("a3ob.flags_vertex_add", text="", icon='ADD')
        col_operators.operator("a3ob.flags_vertex_remove", text="", icon='REMOVE')
        col_operators.separator()
        col_operators.operator("a3ob.flags_vertex_clear", text="", icon='TRASH')


class A3OB_PT_object_mesh_flags_face(bpy.types.Panel):
    bl_region_type = 'WINDOW'
    bl_space_type = 'PROPERTIES'
    bl_label = "Face Flag Groups"
    bl_context = "data"
    bl_parent_id = "A3OB_PT_object_mesh_flags"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH' and not obj.a3ob_properties_object_proxy.is_a3_proxy
    
    def draw(self, context):
        obj = context.object
        flag_props = obj.a3ob_properties_object_flags
        
        layout = self.layout
        row = layout.row()
        col_list = row.column()
        col_list.template_list("A3OB_UL_flags_face", "A3OB_flags_face", flag_props, "face", flag_props, "face_index")
        
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        if utils.is_valid_idx(flag_props.face_index, flag_props.face):
            if obj.mode == 'EDIT':
                row_operators = layout.row(align=True)
                row_operators.operator("a3ob.flags_face_assign")
                row_operators.operator("a3ob.flags_face_select")
                row_operators.operator("a3ob.flags_face_deselect")
            
            prop = flag_props.face[flag_props.face_index]
            layout.prop(prop, "lighting")
            layout.prop(prop, "zbias")
            layout.prop(prop, "shadow")
            layout.prop(prop, "merging")
            layout.prop(prop, "user")
            
        col_operators = row.column(align=True)
        col_operators.operator("a3ob.flags_face_add", text="", icon='ADD')
        col_operators.operator("a3ob.flags_face_remove", text="", icon='REMOVE')
        col_operators.separator()
        col_operators.operator("a3ob.flags_face_clear", text="", icon='TRASH')


class A3OB_PT_object_proxy(bpy.types.Panel, utils.PanelHeaderLinkMixin):
    bl_region_type = 'WINDOW'
    bl_space_type = 'PROPERTIES'
    bl_label = "Object Builder: Proxy Properties"
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}

    doc_url = "https://mrcmodding.gitbook.io/arma-3-object-builder/properties/proxy"
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH' and obj.a3ob_properties_object_proxy.is_a3_proxy and not obj.a3ob_properties_object.is_a3_lod
        
    def draw(self, context):
        obj = context.object
        object_props = obj.a3ob_properties_object_proxy
        
        layout = self.layout
        row = layout.row(align=True)
        col_enable = row.column(align=True)
        col_enable.prop(object_props, "is_a3_proxy", text="Is P3D Proxy", toggle=True)
        col_enable.enabled = False
        
        row_select = layout.row(align=True)
        op = row_select.operator("a3ob.select_object", text="Select Parent LOD", icon='RESTRICT_SELECT_OFF')
        if obj.parent and obj.parent.type == 'MESH' and obj.parent.a3ob_properties_object.is_a3_lod:
            op.object_name = obj.parent.name
            op.identify_lod = False
        else:
            row_select.enabled = False
        
        layout.separator()
        row_path = layout.row(align=True)
        row_path.operator("a3ob.paste_common_proxy", text="", icon='PASTEDOWN')
        row_path.prop(object_props, "proxy_path", text="", icon='MESH_CUBE')
        layout.prop(object_props, "proxy_index")


def menu_func(self, context):
    self.layout.separator()
    self.layout.operator(A3OB_OT_proxy_add.bl_idname, text="Arma 3 Proxy", icon_value=get_icon("op_proxy_add"))


classes = (
    A3OB_OT_proxy_add,
    A3OB_OT_proxy_remove,
    A3OB_OT_paste_common_proxy,
    A3OB_OT_namedprops_add,
    A3OB_OT_namedprops_remove,
    A3OB_OT_paste_common_namedprop,
    A3OB_OT_lod_copy_add,
    A3OB_OT_lod_copy_remove,
    A3OB_OT_flags_vertex_add,
    A3OB_OT_flags_vertex_remove,
    A3OB_OT_flags_vertex_assign,
    A3OB_OT_flags_vertex_select,
    A3OB_OT_flags_vertex_deselect,
    A3OB_OT_flags_vertex_clear,
    A3OB_OT_flags_face_add,
    A3OB_OT_flags_face_remove,
    A3OB_OT_flags_face_assign,
    A3OB_OT_flags_face_select,
    A3OB_OT_flags_face_deselect,
    A3OB_OT_flags_face_clear,
    A3OB_UL_namedprops,
    A3OB_UL_lod_copies,
    A3OB_UL_common_proxies,
    A3OB_UL_flags_vertex,
    A3OB_UL_flags_face,
    A3OB_UL_proxy_access,
    A3OB_PT_object_mesh,
    A3OB_PT_object_mesh_namedprops,
    A3OB_PT_object_mesh_proxies,
    A3OB_PT_object_mesh_copies,
    A3OB_PT_object_proxy,
    A3OB_PT_object_mesh_flags,
    A3OB_PT_object_mesh_flags_vertex,
    A3OB_PT_object_mesh_flags_face
)


def register_ui():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.VIEW3D_MT_add.append(menu_func)


def unregister_ui():
    bpy.types.VIEW3D_MT_add.remove(menu_func)
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
