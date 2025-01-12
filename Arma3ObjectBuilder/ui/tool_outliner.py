import bpy
from bpy.app.handlers import persistent

from .. import get_prefs
from .. import utils
from ..utilities import outliner as linerutils


class A3OB_UL_outliner_lods(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        op = row.operator("a3ob.select_object", text="", icon='RESTRICT_SELECT_OFF', emboss=False)
        op.object_name = item.obj
        row.label(text=" %s" % item.name)

        row_counts = row.row(align=True)
        row_counts.alignment = 'RIGHT'
        row_counts.label(text="%d " % (item.proxy_count + item.subobject_count))
    
    def filter_items(self, context, data, propname):
        helper_funcs = bpy.types.UI_UL_list
        flt_flags = []
        flt_neworder = []
        
        sorter = [(index, frame) for index, frame in enumerate(getattr(data, propname))]
        flt_neworder = helper_funcs.sort_items_helper(sorter, lambda f: f[1].priority, False)
        
        return flt_flags, flt_neworder


class A3OB_UL_outliner_proxies(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        row = layout.row(align=True)
        op = row.operator("a3ob.select_object", text="", icon='RESTRICT_SELECT_OFF', emboss=False)
        op.object_name = item.obj
        op.identify_lod = False
        row.label(text=" %s" % item.name)
    
    def filter_items(self, context, data, propname):
        helper_funcs = bpy.types.UI_UL_list
        flt_flags = []
        flt_neworder = []
        
        sorter = getattr(data, propname)
        flt_neworder = helper_funcs.sort_items_by_name(sorter, "name")
        
        return flt_flags, flt_neworder


class A3OB_OT_select_object(bpy.types.Operator):
    """Select object in scene"""
    
    bl_idname = "a3ob.select_object"
    bl_label = "Select Object"
    bl_options = {'REGISTER'}
    
    object_name: bpy.props.StringProperty(name="Object Name")
    identify_lod: bpy.props.BoolProperty(name="Identify In Outliner", default = True)
    
    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        if self.object_name in context.scene.objects:
            
            bpy.ops.object.select_all(action='DESELECT')
            
            obj = context.scene.objects.get(self.object_name)
            if obj:
                try:
                    obj.select_set(True)
                    context.view_layer.objects.active = obj
                    if self.identify_lod:
                        linerutils.identify_lod(context)
                except:
                    pass
        
        return {'FINISHED'}


class A3OB_OT_indentify_lod(bpy.types.Operator):
    """Identify the active object in the outliner"""

    bl_idname = "a3ob.identify_lod"
    bl_label = "Identify"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        if context.active_object:
            linerutils.identify_lod(context)

        return {'FINISHED'}


class A3OB_PT_outliner(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Object Builder"
    bl_label = "Outliner"
    bl_options = {'DEFAULT_CLOSED'}

    doc_url = "https://mrcmodding.gitbook.io/arma-3-object-builder/tools/outliner"
    
    @classmethod
    def poll(cls, context):
        return get_prefs().outliner == 'ENABLED'
    
    def draw_header(self, context):
        utils.draw_panel_header(self)
    
    def draw(self, context):
        layout = self.layout
        scene_props = context.scene.a3ob_outliner
        row_header = layout.row(align=True)
        row_header.label(text="LOD List:")
        row_header.prop(scene_props, "show_hidden", text="", icon='OBJECT_HIDDEN', toggle=True)

        col_list = layout.column(align=True)
        col_list.template_list("A3OB_UL_outliner_lods", "A3OB_outliner_lods", scene_props, "lods", scene_props, "lods_index")
        
        row_counts = col_list.row(align=True)
        box_proxy = row_counts.box()
        box_subobject = row_counts.box()

        if utils.is_valid_idx(scene_props.lods_index, scene_props.lods):
            item = scene_props.lods[scene_props.lods_index]
            box_proxy.label(text="%d" % item.proxy_count, icon='PMARKER_ACT')
            box_subobject.label(text="%d" % item.subobject_count, icon='MESH_CUBE')
        else:
            box_proxy.label(text="")
            box_subobject.label(text="")

        layout.operator("a3ob.identify_lod", icon='VIEWZOOM')


class A3OB_PT_outliner_proxies(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Object Builder"
    bl_label = "Proxies"
    bl_parent_id = "A3OB_PT_outliner"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        scene_props = context.scene.a3ob_outliner

        layout.template_list("A3OB_UL_outliner_proxies", "A3OB_outliner_proxies", scene_props, "proxies", scene_props, "proxies_index")
        

@persistent
def depsgraph_update_post_handler(scene, depsgraph):    
    linerutils.update_outliner(scene)
    

classes = (
    A3OB_UL_outliner_proxies,
    A3OB_UL_outliner_lods,
    A3OB_OT_select_object,
    A3OB_OT_indentify_lod,
    A3OB_PT_outliner,
    A3OB_PT_outliner_proxies
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    if get_prefs().outliner == 'ENABLED':
        bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_post_handler)
    
    print("\t" + "UI: Outliner")


def unregister():
    try:
        bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update_post_handler)
    except:
        pass
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    print("\t" + "UI: Outliner")
