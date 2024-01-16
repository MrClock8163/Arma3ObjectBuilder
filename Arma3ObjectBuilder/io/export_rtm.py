# Processing functions to export animation data to the RTM file format.
# The actual file handling is implemented in the data_rtm module.


import mathutils

from . import data_rtm as rtm
from ..utilities.logger import ProcessLogger


def build_frame_list(operator, action):
    frame_range = operator.frame_end - operator.frame_start
    if frame_range == 0 or operator.static_pose:
        return []

    frames = []
    if operator.frame_source == 'LIST':
        if not action or len(action.a3ob_properties_action.frames) == 0:
            return []
        
        frames = [item.index for item in action.a3ob_properties_action.frames if operator.frame_start <= item.index <= operator.frame_end]
    elif operator.frame_source == 'SAMPLE_STEP':
        frames = list(range(operator.frame_start, operator.frame_end, operator.frame_step))
    elif operator.frame_source == 'SAMPLE_COUNT':
        count = operator.frame_count - 1
        if count > 0:
            delta = frame_range / count
            for i in range(count + 1):
                frames.append(round(operator.frame_start + i * delta))

    frames.extend([operator.frame_start, operator.frame_end])
    frames = sorted(list(set(frames)))

    mapping = [(item, (item - operator.frame_start) * 1 / frame_range) for item in frames]

    return mapping


# Since we want the model.cfg skeleton to govern the casing of bone names (like other parts of the addon do),
# but we need the posing bone casing for the bone lookup from the armature, we have to build a posing name -> skeleton bone name
# mapping. The key of the map would be used to query the posing bones, and the corresponding value would be written to the RTM.
def build_bone_map(operator, context, obj):
    scene_props = context.scene.a3ob_rigging
    skeleton = scene_props.skeletons[operator.skeleton_index]

    pose_bones = {bone.name.lower(): bone.name for bone in obj.pose.bones}
    return {pose_bones[bone.name.lower()]: bone.name for bone in skeleton.bones if bone.name.lower() in pose_bones}


# For movement animations, a motion vector is supported. Motion
# can be manually set, or calculated from the start and end position of a selected bone.
def process_motion(context, obj, action, frame_start, frame_end):
    action_props = action.a3ob_properties_action
    
    motion_vector = mathutils.Vector((0, 0, 0))
    if not action:
        return motion_vector
    
    if action_props.motion_source == 'MANUAL' or action_props.motion_bone not in obj.pose.bones:
        motion_vector = action_props.motion_vector
    else:
        bone = obj.pose.bones.get(action_props.motion_bone)
        if not bone:
            return (0, 0, 0)
        
        context.scene.frame_set(frame_start)
        pos_start = (obj.matrix_world @ bone.matrix).to_translation()
        
        context.scene.frame_set(frame_end)
        pos_end = (obj.matrix_world @ bone.matrix).to_translation()
        
        motion_vector = pos_end - pos_start

    return tuple(motion_vector)


def process_frame(context, obj, bones_map, frame, phase):
    context.scene.frame_set(frame)
    output = rtm.RTM_Frame()
    output.phase = phase

    transforms = []
    for bone in bones_map:
        pose_bone = obj.pose.bones.get(bone)
        if not pose_bone:
            continue

        trans = rtm.RTM_Transform()
        trans.bone = bones_map[bone]
        matrix = pose_bone.matrix_channel.copy()
        matrix.transpose()

        trans.matrix = matrix

        transforms.append(trans)
    
    output.transforms = transforms

    return output


def write_file(operator, context, file, obj, action):
    logger = ProcessLogger()
    logger.step("RTM export to %s" % operator.filepath)
    
    frame_start = operator.frame_start
    frame_end = operator.frame_end
    
    frame_mapping = build_frame_list(operator, action)
    static_pose = len(frame_mapping) < 2

    if static_pose:
        logger.log("Exporting static pose")
        frame_mapping = [
            (context.scene.frame_current, 0),
            (context.scene.frame_current, 1)
        ]
    else:
        logger.log("Detected %d frames" % len(frame_mapping))
    
    logger.log("Processing data:")
    logger.level_up()

    rtm_data = rtm.RTM_File()
    anim = rtm.RTM_0101()
    if not static_pose:
        anim.motion = process_motion(context, obj, action, frame_start, frame_end)
        logger.log("Calculated motion")

    bone_map = build_bone_map(operator, context, obj)
    anim.bones = list(bone_map.values())
    logger.log("Collected bones")
    anim.frames = [process_frame(context, obj, bone_map, index, phase) for index, phase in frame_mapping]
    
    logger.log("Collected frames")
    logger.level_down()

    logger.log("File report:")
    logger.level_up()

    logger.log("Motion: %f, %f, %f" %  tuple(anim.motion))
    logger.log("Bones: %d" % len(anim.bones))
    logger.log("Frames: %d" % len(anim.frames))

    logger.level_down()

    if operator.force_lowercase:
        anim.force_lowercase()
    
    rtm_data.anim = anim

    rtm_data.write(file)

    return static_pose, len(anim.frames)