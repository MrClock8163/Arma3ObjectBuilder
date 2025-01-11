# Processing functions to import animation data from RTM files.
# Actual file handling is implemented in the data_rtm module.
# Keyframe importing is based on the official io_scene_fbx module.


import os
from itertools import chain

import bpy
from mathutils import Matrix, Vector

from . import data as rtm
from ..logger import ProcessLogger


def mute_constraints(obj, bones):
    for bone in obj.pose.bones:
        if bone.name.lower() not in bones:
            continue

        for item in bone.constraints:
            item.mute = True


def create_action(operator, obj):
    action = bpy.data.actions.new(os.path.basename(operator.filepath))
    action.use_fake_user = True
    if not obj.animation_data:
        obj.animation_data_create()
    
    if not obj.animation_data.action or operator.make_active:
        obj.animation_data.action = action
    
    return action


def build_transform_lookup(rtm_0101):
    transforms = {}
    for i, frame in enumerate(rtm_0101.frames):
        for item in frame.transforms:
            transforms[item.bone.lower(), i] = Matrix(item.matrix)

    return transforms


def build_motion_lookup(operator, rtm_0101):
    lookup = {}
    motion = Vector(rtm_0101.motion).xzy # not sure why it has to be swizzled back to XZY order, but oh well...
    if motion.length == 0 or not operator.apply_motion:
        empty = Vector()
        for i in range(len(rtm_0101.frames)):
            lookup[i] = empty
    else:
        for i, frame in enumerate(rtm_0101.frames):
            lookup[i] = motion * frame.phase
    
    return lookup


def build_frame_mapping(operator, rtm_0101):
    frames = {}

    frame_start = operator.frame_start
    frame_end = operator.frame_end
    if operator.mapping_mode == 'FPS':
        frame_start = 1
        frame_end = operator.fps * operator.time + 1

    frames = {}

    if operator.mapping_mode == 'DIRECT':
        frames = {i: i + 1 for i in range(len(rtm_0101.frames))}
    else:
        for i, frame in enumerate(rtm_0101.frames):
            frames[i] = frame.phase * frame_end + (1 - frame.phase) * frame_start
    
    if operator.mapping_mode != 'DIRECT' or operator.round_frames:
        frames = {i: round(frames[i]) for i in frames}

    return frames


def build_fcurves(action, pose_bone):
    rot_mode = "rotation_euler"
    channel_count = 3
    if pose_bone.rotation_mode == 'QUATERNION':
        rot_mode = "rotation_quaternion"
        channel_count = 4
    elif pose_bone.rotation_mode == 'AXIS_ANGLE':
        rot_mode = "rotation_axis_angle"
        channel_count = 4

    path_loc = pose_bone.path_from_id("location")
    path_rot = pose_bone.path_from_id(rot_mode)
    path_scale = pose_bone.path_from_id("scale")

    props = [(path_loc, 3, pose_bone.name),
            (path_rot, channel_count, pose_bone.name),
            (path_scale, 3, pose_bone.name)]
    
    fcurves = [action.fcurves.new(prop, index=channel, action_group=grpname)
                for prop, nbr_channels, grpname in props for channel in range(nbr_channels)]

    return fcurves


def store_keyframes(dictionary, frame_idx, iterator):
    for fc, value in iterator:
        fc_key = (fc.data_path, fc.array_index)
        if not dictionary.get(fc_key):
            dictionary[fc_key] = []
        dictionary[fc_key].extend((frame_idx, value))


def add_keyframes(action, fcurves, dictionary):
    for fc_key, key_values in dictionary.items():
        data_path, index = fc_key

        fcurve = action.fcurves.find(data_path=data_path, index=index)
        num_keys = len(key_values) // 2
        fcurve.keyframe_points.add(num_keys)
        fcurve.keyframe_points.foreach_set('co', key_values)
        linear_enum_value = bpy.types.Keyframe.bl_rna.properties['interpolation'].enum_items['LINEAR'].value
        fcurve.keyframe_points.foreach_set('interpolation', (linear_enum_value,) * num_keys)

    for fc in fcurves:
        fc.update()


def import_keyframes(obj, action, transforms, frames, motion):
    for pose_bone in obj.pose.bones:
        fcurves = build_fcurves(action, pose_bone)

        mat_rest = pose_bone.bone.matrix_local.copy()

        rot_eul_prev = pose_bone.rotation_euler.copy()
        rot_quat_prev = pose_bone.rotation_quaternion.copy()

        keyframes = {}
        mat_identity = Matrix()
        for i in frames:
            mat_channel = transforms.get((pose_bone.name.lower(), i), mat_identity)
            mat_parent_channel = transforms.get((pose_bone.parent.name.lower() if pose_bone.parent else "", i), mat_identity)
            mat_basis = mat_rest.inverted_safe() @ mat_parent_channel.inverted_safe() @ (mat_channel @ mat_rest)
            loc, rot, scale = mat_basis.decompose()

            if mat_channel is not mat_identity and not pose_bone.parent:
                loc += motion[i]

            if pose_bone.rotation_mode == 'QUATERNION':
                if rot_quat_prev.dot(rot) < 0.0:
                    rot = -rot
                rot_quat_prev = rot
            elif pose_bone.rotation_mode == 'AXIS_ANGLE':
                vec, ang = rot.to_axis_angle()
                rot = ang, vec.x, vec.y, vec.z
            else:  # Euler
                rot = rot.to_euler(pose_bone.rotation_mode, rot_eul_prev)
                rot_eul_prev = rot
            
            if pose_bone.bone.use_connect:
                loc = Vector() # clean computational residuals

            store_keyframes(keyframes, frames[i], zip(fcurves, chain(loc, rot, scale)))

        add_keyframes(action, fcurves, keyframes)


def get_bone_hierarchy(bones, parent = ""):
    hierarchy = {}
    for bone in bones:
        if not bone.parent or bone.parent.name == parent:
            hierarchy[bone.name.lower()] = parent.lower()
            hierarchy.update(get_bone_hierarchy(bone.children, bone.name))
        
    return hierarchy


def import_file(operator, context, file):
    logger = ProcessLogger()
    logger.start_subproc("RTM import from %s" % operator.filepath)

    obj = context.active_object
    if not obj or obj.type != 'ARMATURE':
        logger.step("No target armature found, aborting import")
        logger.end_subproc("RTM import finished")
        return 0
    
    rtm_data = rtm.read_rtm_universal(file)
    
    logger.start_subproc("File report:")
    if type(rtm_data) is rtm.BMTR_File:
        logger.start_subproc("BMTR:")
        logger.step("Version: %d" % rtm_data.version)
        logger.step("Motion vector: %s" % str(rtm_data.motion))
        logger.step("Bones: %d" % len(rtm_data.bones))
        logger.step("Properties: %d" % len(rtm_data.props))
        logger.step("Phases: %d" % len(rtm_data.phases))
        logger.step("Frames: %d" % len(rtm_data.frames))
        logger.end_subproc()

        bone_parents = get_bone_hierarchy(obj.data.bones)
        rtm_data = rtm_data.as_rtm(bone_parents)
        logger.step("Converted BMTR to plain RTM")

    rtm_0101 = rtm_data.anim
    rtm_mdat = rtm_data.props

    if rtm_mdat:
        logger.start_subproc("RTM_MDAT:")
        for item in rtm_mdat.items:
            logger.step(item)

        logger.end_subproc()

    logger.start_subproc("RTM_0101:")
    logger.step("Motion vector: %s" % str(rtm_0101.motion))
    logger.step("Bones: %d" % len(rtm_0101.bones))
    logger.step("Frames: %d" % len(rtm_0101.frames))
    logger.end_subproc()
    logger.end_subproc()

    logger.start_subproc("Processing data:")
    logger.step("Target armature: %s" % obj.name)

    action = create_action(operator, obj)
    logger.step("Created action: %s" % action.name)

    transforms = build_transform_lookup(rtm_0101)
    logger.step("Built transform lookup")

    motion = build_motion_lookup(operator, rtm_0101)
    logger.step("Built motion lookup")

    frames = build_frame_mapping(operator, rtm_0101)
    operator.frame_start = frames[0]
    operator.frame_end = frames[len(rtm_0101.frames) - 1]
    logger.step("Built frame mapping")

    if operator.mute_constraints:
        mute_constraints(obj, [item.lower() for item in rtm_0101.bones])
        logger.step("Muted bone constraints")

    import_keyframes(obj, action, transforms, frames, motion)
    logger.step("Created keyframes")

    if operator.make_active:
        context.scene.frame_start = operator.frame_start
        context.scene.frame_end = operator.frame_end

    action_props = action.a3ob_properties_action

    if not operator.apply_motion:
        action_props.motion_vector = rtm_0101.motion

    if rtm_mdat:
        for phase, name, value in rtm_mdat.items:
            new_item = action_props.props.add()
            new_item.index = round(phase * operator.frame_end + (1 - phase) * operator.frame_start)
            new_item.name = name
            new_item.value = value
    
    logger.end_subproc()
    logger.end_subproc()
    logger.step("RTM import finished")
    return len(set(frames.values()))
