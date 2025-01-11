# Processing functions to export animation data to the RTM file format.
# The actual file handling is implemented in the data_rtm module.


import time
import mathutils

from . import data as rtm
from ..logger import ProcessLogger


def build_frame_list(operator, action):
    frame_range = operator.frame_end - operator.frame_start
    if not action or frame_range == 0 or operator.static_pose:
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

        trans.matrix = matrix

        transforms.append(trans)
    
    output.transforms = transforms

    return output


def process_props(operator, action_props):
    output = []
    frame_range = operator.frame_end - operator.frame_start
    for item in action_props.props:
        if not (operator.frame_start <= item.index <= operator.frame_end):
            continue
    
        phase = (item.index - operator.frame_start) / frame_range

        output.append((phase, item.name, item.value))

    return output


def write_file(operator, context, file, obj, action):
    logger = ProcessLogger()
    logger.start_subproc("RTM export to %s" % operator.filepath)
    
    frame_start = operator.frame_start
    frame_end = operator.frame_end
    
    frame_mapping = build_frame_list(operator, action)
    static_pose = len(frame_mapping) < 2
    if operator.force_lowercase:
        logger.step("Force lowercase")

    if static_pose:
        logger.step("Exporting static pose")
        frame_mapping = [
            (context.scene.frame_current, 0),
            (context.scene.frame_current, 1)
        ]
    else:
        logger.step("Detected %d frames" % len(frame_mapping))
    
    logger.start_subproc("Processing data:")

    rtm_data = rtm.RTM_File()
    rtm_0101 = rtm.RTM_0101()
    if not static_pose:
        rtm_0101.motion = process_motion(context, obj, action, frame_start, frame_end)
        logger.step("Calculated motion")

    bone_map = build_bone_map(operator, context, obj)
    rtm_0101.bones = list(bone_map.values())
    logger.step("Collected bones")
    rtm_0101.frames = [process_frame(context, obj, bone_map, index, phase) for index, phase in frame_mapping]
    
    logger.step("Collected frames")
    logger.end_subproc()

    action_props = action.a3ob_properties_action
    if not static_pose and len(action_props.props) > 0:
        rtm_mdat = rtm.RTM_MDAT()
        rtm_mdat.items = process_props(operator, action_props)
        rtm_data.props = rtm_mdat
        
    logger.start_subproc("File report:")

    if rtm_data.props:
        logger.start_subproc("RTM_MDAT")
        for item in rtm_data.props.items:
            logger.step(item)
        logger.end_subproc()

    logger.start_subproc("RTM_0101")
    logger.step("Motion: %f, %f, %f" %  tuple(rtm_0101.motion))
    logger.step("Bones: %d" % len(rtm_0101.bones))
    logger.step("Frames: %d" % len(rtm_0101.frames))
    logger.end_subproc()

    logger.end_subproc()

    if operator.force_lowercase:
        rtm_0101.force_lowercase()
    
    rtm_data.anim = rtm_0101

    rtm_data.write(file)

    logger.end_subproc()
    logger.step("RTM export finished in %f sec" % (time.time() - logger.times.pop()))

    return static_pose, len(rtm_0101.frames)
