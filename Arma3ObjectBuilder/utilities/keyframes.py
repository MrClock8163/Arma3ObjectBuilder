import bpy


def get_range(wm_props):
    return list(range(wm_props.range_start, wm_props.range_end + 1, wm_props.range_step))


def add_frame_range(obj, wm_props):
    object_props = obj.a3ob_properties_object_armature
    frames_current = [frame.index for frame in object_props.frames]
    frames = get_range(wm_props)
    frames.sort()
    
    for frame in frames:
        if frame in frames_current:
            continue
        item = object_props.frames.add()
        item.index = frame
        
    return len(frames)


def add_frame_timeline(obj):
    object_props = obj.a3ob_properties_object_armature
    frames = []
    frames_current = [frame.index for frame in object_props.frames]
    
    fcurves = obj.animation_data.action.fcurves
    for curve in fcurves:
        for point in curve.keyframe_points:
            if point.co.x not in frames:
                frames.append(point.co.x)
                
    frames.sort()
    
    for frame in frames:
        if frame in frames_current:
            continue
        item = object_props.frames.add()
        item.index = frame
        
    return len(frames)