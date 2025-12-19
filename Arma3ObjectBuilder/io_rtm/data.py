# Class structure, read-write methods and conversion functions for handling
# the RTM and BMTR binary data structures. Format specifications
# can be found on the community wiki (although not 100% accurate/complete regarding certain details):
# https://community.bistudio.com/wiki/Rtm_(Animation)_File_Format
# https://community.bistudio.com/wiki/Rtm_Binarised_File_Format


import struct
from io import BytesIO, BufferedReader
from typing import TypeAlias, BinaryIO, Self, Never, Any

import numpy as np

from .. import binary
from ..compression import lzo1x_decompress, LZO_Error


class RTM_Error(Exception):
    def __str__(self) -> str:
        return "RTM - %s" % super().__str__()


_TransformMatrix: TypeAlias = tuple[
    tuple[float, float, float, float],
    tuple[float, float, float, float],
    tuple[float, float, float, float],
    tuple[float, float, float, float]
]


class RTM_Transform():
    def __init__(self) -> None:
        self.bone: str = ""
        self.matrix: _TransformMatrix = ((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1))

    @classmethod
    def read(cls, file: BinaryIO) -> Self:
        output = cls()

        output.bone = binary.read_asciiz_field(file, 32)
        data = struct.unpack('<12f', file.read(48))

        output.matrix = (
            (data[0], data[6], data[3], data[9]),
            (data[2], data[8], data[5], data[11]),
            (data[1], data[7], data[4], data[10]),
            (0, 0, 0, 1)
        )

        return output

    def write(self, file: BinaryIO) -> None:
        binary.write_asciiz_field(file, self.bone, 32)

        data = self.matrix
        mat = (
            (data[0][0], data[2][0], data[1][0]),
            (data[0][2], data[2][2], data[1][2]),
            (data[0][1], data[2][1], data[1][1]),
            (data[0][3], data[2][3], data[1][3])
        )

        file.write(struct.pack('<12f', *mat[0], *mat[1], *mat[2], *mat[3]))


class RTM_Frame():
    def __init__(self) -> None:
        self.phase: float = 0
        self.transforms: list[RTM_Transform] = []

    def __repr__(self) -> str:
        return "Phase: %f" % self.phase

    @classmethod
    def read(cls, file: BinaryIO, count_bones: int) -> Self:
        output = cls()

        output.phase = binary.read_float(file)
        output.transforms = [RTM_Transform.read(file) for i in range(count_bones)]

        return output

    def write(self, file: BinaryIO) -> None:
        binary.write_float(file, self.phase)
        for item in self.transforms:
            item.write(file)


class RTM_MDAT():
    signature = b"RTM_MDAT"

    def __init__(self) -> None:
        self.items: list[tuple[float, str, str]] = []

    @classmethod
    def read(cls, file: BinaryIO, skip_signature: bool = False) -> Self:
        output = cls()

        if not skip_signature:
            signature = file.read(8)
            if signature != b"RTM_MDAT":
                raise RTM_Error("Invalid MDAT signature: %s" % str(signature))

        file.read(4)  # padding
        count_items = binary.read_ulong(file)
        for _ in range(count_items):
            phase = binary.read_float(file)
            name = binary.read_lascii(file)
            value = binary.read_lascii(file)

            output.items.append((phase, name, value))

        return output

    def write(self, file: BinaryIO) -> None:
        file.write(self.signature)
        binary.write_ulong(file, 0, len(self.items))

        for phase, name, value in self.items:
            binary.write_float(file, phase)
            binary.write_lascii(file, name)
            binary.write_lascii(file, value)


class RTM_0101():
    signature = b"RTM_0101"

    def __init__(self) -> None:
        self.motion: tuple[float, float, float] = (0, 0, 0)
        self.frames: list[RTM_Frame] = []
        self.bones: list[str] = []

    @classmethod
    def read(cls, file: BinaryIO, skip_signature: bool = False) -> Self:
        output = cls()
        if not skip_signature:
            signature = file.read(8)
            if signature != b"RTM_0101":
                raise RTM_Error("Invalid header signature: %r" % signature)

        x, z, y = binary.read_floats(file, 3)
        output.motion = (x, y, z)
        count_frames, count_bones = binary.read_ulongs(file, 2)

        output.bones = [binary.read_asciiz_field(file, 32) for i in range(count_bones)]
        output.frames = [RTM_Frame.read(file, count_bones) for i in range(count_frames)]

        return output

    def write(self, file: BinaryIO) -> None:
        file.write(self.signature)
        binary.write_float(file, self.motion[0], self.motion[2], self.motion[1])

        count_frames = len(self.frames)
        count_bones = len(self.bones)

        binary.write_ulong(file, count_frames, count_bones)

        for item in self.bones:
            binary.write_asciiz_field(file, item, 32)

        for frame in self.frames:
            frame.write(file)

    # While the game engine itself seems to be not case sensitive,
    # some tools (eg.: animation preview in Object Builder, the preview would
    # not work if the case of the selection names in the model and the RTM is not
    # matcing) are. So it's good to have a way to keep everything uniform in the
    # outputs, regardless of how things are called in Blender.
    def force_lowercase(self) -> None:
        self.bones = [bone.lower() for bone in self.bones]

        for frame in self.frames:
            for trans in frame.transforms:
                trans.bone = trans.bone.lower()


class RTM_File():
    def __init__(self) -> None:
        self.source: str = ""
        self.props: RTM_MDAT | None = None
        self.anim: RTM_0101 = RTM_0101()

    @classmethod
    def read(cls, file: BufferedReader) -> Self:
        output = cls()

        while file.peek():
            signature = file.read(8)
            if signature == b"RTM_0101":
                output.anim = RTM_0101.read(file, True)
            elif signature == b"RTM_MDAT":
                output.props = RTM_MDAT.read(file, True)
            else:
                raise RTM_Error("Unknown datablock signature: %s" % str(signature))

        return output

    @classmethod
    def read_file(cls, filepath: str) -> Self:
        output = None
        with open(filepath, "br") as file:
            output = cls.read(file)

        return output

    def write(self, file: BinaryIO) -> None:
        if self.props:
            self.props.write(file)

        if not self.anim:
            raise RTM_Error("Cannot export RTM without animation data")

        self.anim.write(file)

    def write_file(self, filepath: str) -> None:
        with open(filepath, "wb") as file:
            self.write(file)


class BMTR_Error(Exception):
    def __str__(self) -> str:
        return "BMTR - %s" % super().__str__()


class BMTR_Prop:
    def __init__(self) -> None:
        self.name: str = ""
        self.value: str = ""
        self.phase: float = 0

    @classmethod
    def read(cls, file: BinaryIO) -> Self:
        output = cls()

        file.read(4)
        output.name = binary.read_asciiz(file)
        output.phase = binary.read_float(file)
        output.value = binary.read_asciiz(file)

        return output

    def as_rtm(self) -> tuple[float, str, str]:
        return (self.phase, self.name, self.value)


class BMTR_Transform:
    def __init__(self) -> None:
        self.quaternion: tuple[float, float, float, float] = (0, 0, 0, 1)
        self.location: tuple[float, float, float] = (0, 0, 0)

    @classmethod
    def read(cls, file: BinaryIO) -> Self:
        output = cls()

        q1, q2, q3, q4 = binary.read_shorts(file, 4)
        output.quaternion = (
            q1 / 16384,
            q2 / 16384,
            q3 / 16384,
            q4 / 16384
        )
        x, z, y = binary.read_halfs(file, 3)
        output.location = (-x, -y, z)

        return output

    # The BMTR format stores quaternions and offsets instead of full transformation matrices,
    # so the matrices need to be reconstructed. Since the Arma 3 uses a left handed coordinate system
    # with Y axis up, the order of some components, and some signs need to be swapped around.
    # Formulas to convert a right-handed quaternion to matrix representation:
    # https://www.euclideanspace.com/maths/geometry/rotations/conversions/quaternionToMatrix/index.htm
    def as_rtm(self, bone: str) -> RTM_Transform:
        output = RTM_Transform()
        output.bone = bone
        qx, qz, qy, qw = self.quaternion
        x, y, z = self.location

        r00 = 1 - 2 * qy**2 - 2 * qz**2
        r01 = 2 * qx * qy - 2 * qz * qw
        r02 = 2 * qx * qz + 2 * qy * qw

        r10 = 2 * qx * qy + 2 * qz * qw
        r11 = 1 - 2 * qx**2 - 2 * qz**2
        r12 = 2 * qy * qz - 2 * qx * qw

        r20 = 2 * qx * qz - 2 * qy * qw
        r21 = 2 * qy * qz + 2 * qx * qw
        r22 = 1 - 2 * qx**2 - 2 * qy**2

        output.matrix = (
            (r00, r01, -r02, x),
            (r10, r11, -r12, y),
            (-r20, -r21, r22, z),
            (0, 0, 0, 1)

        )

        return output


class BMTR_Frame:
    def __init__(self) -> None:
        self.transforms: list[BMTR_Transform] = []

    @classmethod
    def read(cls, file: BinaryIO, count_bones: int) -> Self:
        output = cls()
        output.transforms = [BMTR_Transform.read(file) for _ in range(count_bones)]

        return output

    def as_rtm(self, phase: float, bones: list[str], bone_parents: dict[str, str]) -> RTM_Frame:
        output = RTM_Frame()
        output.phase = phase

        transform_lookup: dict[str, RTM_Transform] = {}
        for bone, transform in zip(bones, self.transforms):
            rtm_transform = transform.as_rtm(bone)
            output.transforms.append(rtm_transform)
            transform_lookup[bone] = rtm_transform

        # The transformations stored in the BMTR format are not absolute like in plain RTM, but relative to the parent
        # bones instead. To get the absolute transformation, the matrix of each bone has to be multiplied with the
        # matrix of its parent. To get the correct results, the multiplication must be done in hierarchical order.
        default = RTM_Transform()
        for bone in bone_parents:
            rtm_transform_final = transform_lookup.get(bone)
            if not rtm_transform_final:
                continue
            rtm_transform_parent = transform_lookup.get(bone_parents[bone], default)
            absolute_matrix = np.matrix(rtm_transform_parent.matrix) @ np.matrix(rtm_transform_final.matrix)
            rtm_transform_final.matrix = absolute_matrix.tolist()

        return output


class BMTR_File:
    signature = b"BMTR"
    versions = {3, 4, 5}

    def __init__(self) -> None:
        self.source: str = ""
        self.version: int = 5
        self.motion: tuple[float, float, float] = (0, 0, 0)
        self.bones: list[str] = []
        self.props: list[BMTR_Prop] = []
        self.phases: list[float] = []
        self.frames: list[BMTR_Frame] = []

    def read_frame_phases(self, file: BinaryIO, count_frames: int) -> list[float]:
        expected = count_frames * 4
        compressed = expected >= 1024
        if self.version > 4:
            compressed = binary.read_bool(file)

        output: list[float] = []
        if compressed:
            try:
                _, uncompressed = lzo1x_decompress(file, expected)
            except LZO_Error as ex:
                raise BMTR_Error(str(ex))

            buffer = BufferedReader(BytesIO(uncompressed))
            output = [binary.read_float(buffer) for i in range(count_frames)]
            if buffer.read() != b"":
                raise BMTR_Error("Decompressed data is longer than expected")
        else:
            output = [binary.read_float(file) for i in range(count_frames)]

        return output

    def read_frames(self, file: BinaryIO, count_frames: int, count_bones: int) -> list[BMTR_Frame]:
        output: list[BMTR_Frame] = []
        for _ in range(count_frames):
            count_bones = binary.read_ulong(file)

            expected = count_bones * 14
            compressed = expected >= 1024
            if self.version > 4:
                compressed = binary.read_bool(file)

            if compressed:
                try:
                    _, uncompressed = lzo1x_decompress(file, expected)
                except LZO_Error as ex:
                    raise BMTR_Error(str(ex))

                buffer = BufferedReader(BytesIO(uncompressed))
                output.append(BMTR_Frame.read(buffer, count_bones))
                if buffer.read() != b"":
                    raise BMTR_Error("Decompressed data is longer than expected")
            else:
                output.append(BMTR_Frame.read(file, count_bones))

        return output

    @classmethod
    def read(cls, file: BinaryIO) -> Self:
        signature = file.read(4)
        if signature != cls.signature:
            raise BMTR_Error("Invalid header signature: %r" % signature)

        output = cls()
        version = binary.read_ulong(file)
        if version not in cls.versions:
            raise BMTR_Error("Unknown version: %s" % version)

        output.version = version
        file.read(1)
        x, z, y = binary.read_floats(file, 3)
        output.motion = (x, y, z)

        count_frames = binary.read_ulong(file)
        file.read(4)
        count_bones = binary.read_ulong(file)
        count_bones_check = binary.read_ulong(file)
        if count_bones_check != count_bones:
            raise BMTR_Error("Bone count mismatch (expected: %d, got: %d)" % (count_bones, count_bones_check))

        output.bones = [binary.read_asciiz(file) for i in range(count_bones)]

        if output.version > 4:
            file.read(4)
            count_props = binary.read_ulong(file)
            output.props = [BMTR_Prop.read(file) for i in range(count_props)]

        count_frames_check = binary.read_ulong(file)
        if count_frames_check != count_frames:
            raise BMTR_Error("Frame count mismatch (expected: %d, got: %d)" % (count_frames, count_frames_check))

        output.phases = output.read_frame_phases(file, count_frames)
        output.frames = output.read_frames(file, count_frames, count_bones)

        remainder = file.read()
        if remainder != b"":
            raise BMTR_Error("EOF not found")

        return output

    @classmethod
    def read_file(cls, filepath: str) -> Self:
        output = None
        with open(filepath, "br") as file:
            output = cls.read(file)

        output.source = filepath

        return output

    def as_rtm(self, bone_parents: dict[str, str]) -> RTM_File:
        output = RTM_File()
        output.source = self.source

        if len(self.props) > 0:
            output.props = RTM_MDAT()
            output.props.items = [prop.as_rtm() for prop in self.props]

        rtm_0101 = output.anim
        rtm_0101.motion = self.motion

        case_lookup = {bone.lower(): bone for bone in bone_parents}
        rtm_0101.bones = [case_lookup.get(bone.lower(), bone) for bone in self.bones]

        for phase, frame in zip(self.phases, self.frames):
            rtm_0101.frames.append(frame.as_rtm(phase, rtm_0101.bones, bone_parents))

        return output

    def write(self, file: Any) -> Never:
        raise BMTR_Error("BMTR output is not supported, use plain RTM instead")

    def write_file(self, filepath: str) -> Never:
        self.write(None)


def read_rtm_universal(file: BufferedReader) -> RTM_File | BMTR_File:
    signature = file.read(4)
    file.seek(0)

    if signature == b"BMTR":
        return BMTR_File.read(file)
    elif signature == b"RTM_":
        return RTM_File.read(file)
    else:
        raise ValueError("File is not a valid RTM file.")
