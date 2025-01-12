# Backend functions for the LOD object outliner panel.


from .. import utils


def update_outliner(scene):
    scene_props = scene.a3ob_outliner
    
    scene_props.lods.clear()
    scene_props.proxies.clear()

    for obj in [obj for obj in scene.objects if obj.visible_get() or scene_props.show_hidden]:
        if obj.type != 'MESH' or not obj.a3ob_properties_object.is_a3_lod or obj.parent != None:
            continue
        
        item = scene_props.lods.add()
        item.obj = obj.name
        item.name = obj.a3ob_properties_object.get_name()
        item.priority = int(obj.a3ob_properties_object.lod) * 1e5 + obj.a3ob_properties_object.resolution

        for child in obj.children:
            if child.type != 'MESH':
                continue
                
            if child.a3ob_properties_object_proxy.is_a3_proxy:
                item.proxy_count += 1
            else:
                item.subobject_count += 1
    
    if not utils.is_valid_idx(scene_props.lods_index, scene_props.lods):
        return
    
    lod = scene.objects[scene_props.lods[scene_props.lods_index].obj]
    for child in lod.children:
        if child.type != 'MESH' or not child.a3ob_properties_object_proxy.is_a3_proxy:
            continue

        item = scene_props.proxies.add()
        item.obj = child.name
        item.name = child.a3ob_properties_object_proxy.get_name()


def identify_lod(context):
    obj = context.active_object
    scene_props = context.scene.a3ob_outliner

    if not obj:
        return

    for i, item in enumerate(scene_props.lods):
        if obj.name == item.obj:
            scene_props.lods_index = i
            return
    
    scene_props.lods_index = -1
