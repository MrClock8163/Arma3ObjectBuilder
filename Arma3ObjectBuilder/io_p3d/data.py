# Class structure, read-write methods and conversion functions for handling
# the MLOD P3D binary data structure. Format specifications
# can be found on the community wiki (although not without errors):
# https://community.bistudio.com/wiki/P3D_File_Format_-_MLOD


import struct
import math
import re
from typing import BinaryIO, Self, Any
from abc import ABC, abstractmethod

from .. import binary
from . import translations as translate


class P3D_Error(Exception):
    def __str__(self) -> str:
        return "P3D - %s" % super().__str__()


class P3D_TAGG_Data(ABC):
    @abstractmethod
    def length(self) -> int: ...

    @abstractmethod
    def write(self, file: BinaryIO) -> None: ...


# Generic class to consume unneeded TAGG types (eg.: #Hidden#, #Selected#).
# The class is needed because the data field of the TAGG object must not be none.
class P3D_TAGG_DataEmpty(P3D_TAGG_Data):
    @classmethod
    def read(cls, file: BinaryIO, length: int) -> Self:
        file.seek(length, 1)
        return cls()

    def length(self) -> int:
        return 0

    def write(self, file: BinaryIO) -> None:
        pass


class P3D_TAGG_DataSharpEdges(P3D_TAGG_Data):
    def __init__(self) -> None:
        self.edges: list[tuple[int, int]] = []

    @classmethod
    def read(cls, file: BinaryIO, length: int = 0) -> Self:
        output = cls()

        count_values = length // 4
        data = binary.read_ulongs(file, count_values)

        for i in range(0, count_values, 2):
            point_1 = data[i]
            point_2 = data[i + 1]

            if point_1 == point_2:
                continue

            output.edges.append((point_1, point_2))

        return output

    def length(self) -> int:
        return len(self.edges) * 8

    def write(self, file: BinaryIO) -> None:
        for edge in self.edges:
            if edge[0] == edge[1]:
                continue

            binary.write_ulong(file, *edge)


class P3D_TAGG_DataProperty(P3D_TAGG_Data):
    def __init__(self) -> None:
        self.key: str = ""
        self.value: str = ""

    @classmethod
    def read(cls, file: BinaryIO) -> Self:
        output = cls()

        output.key = binary.read_asciiz_field(file, 64)
        output.value = binary.read_asciiz_field(file, 64)

        return output

    def length(self) -> int:
        return 128

    def write(self, file: BinaryIO) -> None:
        binary.write_asciiz_field(file, self.key, 64)
        binary.write_asciiz_field(file, self.value, 64)


class P3D_TAGG_DataMass(P3D_TAGG_Data):
    def __init__(self) -> None:
        self.masses: tuple[float, ...] = ()

    @classmethod
    def read(cls, file: BinaryIO, count_verts: int) -> Self:
        output = cls()
        output.masses = binary.read_floats(file, count_verts)

        return output

    def length(self) -> int:
        return len(self.masses) * 4

    def write(self, file: BinaryIO) -> None:
        binary.write_float(file, *self.masses)


class P3D_TAGG_DataUVSet(P3D_TAGG_Data):
    def __init__(self) -> None:
        self.id: int = 0
        self.uvs: list[tuple[float, float]] = []

    @classmethod
    def read(cls, file: BinaryIO, length: int = 0) -> Self:
        output = cls()
        output.id = binary.read_ulong(file)
        count_values = (length - 4) // 4
        data = binary.read_floats(file, count_values)
        output.uvs = [(data[i], 1 - data[i + 1]) for i in range(0, count_values, 2)]

        return output

    def length(self) -> int:
        return len(self.uvs) * 8 + 4

    def write(self, file: BinaryIO) -> None:
        binary.write_ulong(file, self.id)
        for u, v in self.uvs:
            binary.write_float(file, u, 1 - v)


class P3D_TAGG_DataSelection(P3D_TAGG_Data):
    def __init__(self) -> None:
        self.count_verts: int = 0
        self.count_faces: int = 0
        self.weight_verts: list[tuple[int, float]] = []
        self.weight_faces: list[tuple[int, float]] = []

    @classmethod
    def decode_weight(cls, weight: int) -> float:
        if weight in (0, 1):
            return weight

        return (255 - weight) / 254

    @classmethod
    def encode_weight(cls, weight: float) -> int:
        if weight in (0, 1):
            return int(weight)

        value = round(255 - 254 * weight)

        return value

    @classmethod
    def read(cls, file: BinaryIO, count_verts: int, count_faces: int) -> Self:
        output = cls()

        output.count_verts = count_verts
        output.count_faces = count_faces

        data_verts = bytearray(file.read(count_verts))
        output.weight_verts = [(i, cls.decode_weight(value)) for i, value in enumerate(data_verts) if value > 0]
        file.seek(count_faces, 1)  # skip face selection data
        # data_faces = bytearray(file.read(count_faces))
        # output.weight_faces = [(i, cls.decode_weight(value)) for i, value in enumerate(data_faces) if value > 0]

        return output

    def length(self) -> int:
        return self.count_verts + self.count_faces

    def write(self, file: BinaryIO) -> None:
        bytes_verts = bytearray(self.count_verts)
        for idx, weight in self.weight_verts:
            bytes_verts[idx] = self.encode_weight(weight)

        bytes_faces = bytearray(self.count_faces)
        for idx, weight in self.weight_faces:
            bytes_faces[idx] = self.encode_weight(weight)

        file.write(bytes_verts)
        file.write(bytes_faces)


class P3D_TAGG():
    def __init__(self) -> None:
        self.active: bool = True
        self.name: str = ""
        self.data: P3D_TAGG_Data = P3D_TAGG_DataEmpty()

    def __repr__(self) -> str:
        return self.name

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self)) and self.name == other.name

    # Read

    @classmethod
    def read(cls, file: BinaryIO, count_verts: int, count_faces: int) -> Self:
        output = cls()

        output.active = binary.read_bool(file)
        output.name = binary.read_asciiz(file)
        length = binary.read_ulong(file)

        if output.name == "#EndOfFile#":
            if length != 0:
                raise P3D_Error("Invalid EOF")

            output.active = False
        elif output.name == "#SharpEdges#":
            if length % 8 != 0:
                raise P3D_Error("Invalid sharp edges length: %d" % length)

            output.data = P3D_TAGG_DataSharpEdges.read(file, length)
        elif output.name == "#Property#":
            if length != 128:
                raise P3D_Error("Invalid named property length: %d" % length)

            output.data = P3D_TAGG_DataProperty.read(file)
        elif output.name == "#Mass#":
            output.data = P3D_TAGG_DataMass.read(file, count_verts)
        elif output.name == "#UVSet#":
            output.data = P3D_TAGG_DataUVSet.read(file, length)
        elif output.is_selection():
            output.data = P3D_TAGG_DataSelection.read(file, count_verts, count_faces)
        else:
            file.seek(length, 1)  # Skip unneeded TAGG data
            output.active = False

        return output

    # Write

    def write(self, file: BinaryIO) -> None:
        if not self.active:
            return

        binary.write_bool(file, self.active)
        binary.write_asciiz(file, self.name)
        binary.write_ulong(file, self.data.length())
        self.data.write(file)

    # Operations

    def is_proxy(self) -> bool:
        if not self.name.startswith("proxy:"):
            return False

        regex_proxy = r"proxy:.*\.\d+"
        return bool(re.match(regex_proxy, self.name))

    def is_selection(self) -> bool:
        return not self.name.startswith("#") and not self.name.endswith("#")


class P3D_LOD_Resolution():
    VISUAL = 0
    VIEW_GUNNER = 1
    VIEW_PILOT = 2
    VIEW_CARGO = 3
    SHADOW = 4
    EDIT = 5
    GEOMETRY = 6
    GEOMETRY_BUOY = 7
    GEOMETRY_PHYSX = 8
    MEMORY = 9
    LANDCONTACT = 10
    ROADWAY = 11
    PATHS = 12
    HITPOINTS = 13
    VIEW_GEOMETRY = 14
    FIRE_GEOMETRY = 15
    VIEW_CARGO_GEOMETRY = 16
    VIEW_CARGO_FIRE_GEOMETRY = 17
    VIEW_COMMANDER = 18
    VIEW_COMMANDER_GEOMETRY = 19
    VIEW_COMMANDER_FIRE_GEOMETRY = 20
    VIEW_PILOT_GEOMETRY = 21
    VIEW_PILOT_FIRE_GEOMETRY = 22
    VIEW_GUNNER_GEOMETRY = 23
    VIEW_GUNNER_FIRE_GEOMETRY = 24
    SUBPARTS = 25
    SHADOW_VIEW_CARGO = 26
    SHADOW_VIEW_PILOT = 27
    SHADOW_VIEW_GUNNER = 28
    WRECKAGE = 29
    UNDERGROUND = 30
    GROUNDLAYER = 31
    NAVIGATION = 32
    UNKNOWN = -1

    LODS_WITH_RESOLUTION = {
        VISUAL,
        VIEW_CARGO,
        SHADOW,
        EDIT,
        VIEW_CARGO_GEOMETRY,
        SHADOW_VIEW_CARGO
    }

    LODS_VISUAL = {
        VISUAL,
        VIEW_GUNNER,
        VIEW_PILOT,
        VIEW_CARGO,
        VIEW_COMMANDER,
        UNKNOWN
    }

    LODS_SHADOW = {
        SHADOW,
        SHADOW_VIEW_CARGO,
        SHADOW_VIEW_PILOT,
        SHADOW_VIEW_GUNNER
    }

    LODS_GEOMETRY = {
        GEOMETRY,
        GEOMETRY_BUOY,
        GEOMETRY_PHYSX,
        VIEW_GEOMETRY,
        FIRE_GEOMETRY,
        VIEW_CARGO_GEOMETRY,
        VIEW_CARGO_FIRE_GEOMETRY,
        VIEW_COMMANDER_GEOMETRY,
        VIEW_COMMANDER_FIRE_GEOMETRY,
        VIEW_PILOT_GEOMETRY,
        VIEW_PILOT_FIRE_GEOMETRY,
        VIEW_GUNNER_GEOMETRY,
        VIEW_GUNNER_FIRE_GEOMETRY,
        UNDERGROUND
    }

    LODS_ALLOW_UV = {*LODS_VISUAL, *LODS_SHADOW, GROUNDLAYER}

    SIGNATURE_MAP = {
        # "0.000e+00": VISUAL, # (+ resolution)
        "1.000e+03": VIEW_GUNNER,
        "1.100e+03": VIEW_PILOT,
        # "1.200e+03": VIEW_CARGO, # (+ resolution)
        # "1.000e+04": SHADOW, # (+ resolution)
        # "1.100e+04": SHADOWBUFFER,
        "1.300e+04": GROUNDLAYER,  # Shadow Volume 3000 for Arma 3
        # "2.000e+04": EDIT, # (+ resolution)
        "1.000e+13": GEOMETRY,
        "2.000e+13": GEOMETRY_BUOY,
        "3.000e+13": UNDERGROUND,  # Geometry PhysX (old) for Arma 3
        "4.000e+13": GEOMETRY_PHYSX,
        "5.000e+13": NAVIGATION,  # Resolution 5e13 for Arma 3
        "1.000e+15": MEMORY,
        "2.000e+15": LANDCONTACT,
        "3.000e+15": ROADWAY,
        "4.000e+15": PATHS,
        "5.000e+15": HITPOINTS,
        "6.000e+15": VIEW_GEOMETRY,
        "7.000e+15": FIRE_GEOMETRY,
        # "8.000e+15": VIEW_CARGO_GEOMETRY, (+ resolution * 1e13)
        "9.000e+15": VIEW_CARGO_FIRE_GEOMETRY,
        "1.000e+16": VIEW_COMMANDER,
        "1.100e+16": VIEW_COMMANDER_GEOMETRY,
        "1.200e+16": VIEW_COMMANDER_FIRE_GEOMETRY,
        "1.300e+16": VIEW_PILOT_GEOMETRY,
        "1.400e+16": VIEW_PILOT_FIRE_GEOMETRY,
        "1.500e+16": VIEW_GUNNER_GEOMETRY,
        "1.600e+16": VIEW_GUNNER_FIRE_GEOMETRY,
        "1.700e+16": SUBPARTS,
        # "1.800e+16": SHADOW_VIEW_CARGO, # (+ resolution * 1e13)
        "1.900e+16": SHADOW_VIEW_PILOT,
        "2.000e+16": SHADOW_VIEW_GUNNER,
        "2.100e+16": WRECKAGE,
        # (-1.0, 0): UNKNOWN
    }

    INFO_MAP = {
        VISUAL: ("Resolution", "Visual resolutiion"),
        VIEW_GUNNER: ("View - Gunner", "Gunner first person view"),
        VIEW_PILOT: ("View - Pilot", "First person view"),
        VIEW_CARGO: ("View - Cargo", "Passenger first person view"),
        SHADOW: ("Shadow Volume", "Shadow casting geometry"),
        EDIT: ("Edit", "Temporary layer"),
        GEOMETRY: ("Geometry", "Object collision geometry and occluders"),
        GEOMETRY_BUOY: ("Geometry Buoyancy", "Buoyant object geometry (Displacement for VBS)"),
        GEOMETRY_PHYSX: ("Geometry PhysX", "PhysX object collision geometry"),
        MEMORY: ("Memory", "Hard points and animation axes"),
        LANDCONTACT: ("Land Contact", "Points of contact with ground"),
        ROADWAY: ("Roadway", "Walkable surfaces"),
        PATHS: ("Paths", "AI path finding mesh"),
        HITPOINTS: ("Hit-points", "Hit point cloud"),
        VIEW_GEOMETRY: ("View Geometry", "View occlusion for AI"),
        FIRE_GEOMETRY: ("Fire Geometry", "Hitbox geometry"),
        VIEW_CARGO_GEOMETRY: ("View - Cargo Geometry", "Passenger view collision geometry and occluders"),
        VIEW_CARGO_FIRE_GEOMETRY: ("View - Cargo Fire Geometry", "Passenger view hitbox geometry"),
        VIEW_COMMANDER: ("View - Commander", "Commander first person view"),
        VIEW_COMMANDER_GEOMETRY: ("View - Commander Geometry", "Commander view collision geometry and occluders"),
        VIEW_COMMANDER_FIRE_GEOMETRY: ("View - Commander Fire Geometry", "Commander hitbox geometry"),
        VIEW_PILOT_GEOMETRY: ("View - Pilot Geometry", "First person collision geometry and occluders"),
        VIEW_PILOT_FIRE_GEOMETRY: ("View - Pilot Fire Geometry", "First person hitbox geometry"),
        VIEW_GUNNER_GEOMETRY: ("View - Gunner Geometry", "Gunner collision geometry and occluders"),
        VIEW_GUNNER_FIRE_GEOMETRY: ("View - Gunner Fire Geometry", "Gunner view hitbox geometry"),
        SUBPARTS: ("Sub Parts", "Obsolete"),
        SHADOW_VIEW_CARGO: ("Shadow Volume - Cargo View", "Passenger view shadow casting geometry"),
        SHADOW_VIEW_PILOT: ("Shadow Volume - Pilot View", "First person view shadow casting geometry"),
        SHADOW_VIEW_GUNNER: ("Shadow Volume - Gunner View", "Gunner view shadow casting geometry"),
        WRECKAGE: ("Wreckage", "Vehicle wreckage"),
        UNDERGROUND: (
            "Underground (VBS)",
            "Underground volume for VBS (not supported in Arma 3 -> Geometry PhysX Old)"
        ),
        GROUNDLAYER: (
            "Groundlayer (VBS)",
            "Ground deformation data for VBS (not supported in Arma 3 -> Shadow Volume 3000)"
        ),
        NAVIGATION: (
            "Navigation (VBS)",
            "Navigation data for VBS (not supported in Arma 3 -> Geometry / Resolution 5e+013)"
        ),
        UNKNOWN: ("Unknown", "Unknown model layer")
    }

    GROUPS_TYPE = {
        **dict.fromkeys(
            [
                VISUAL,
                VIEW_GUNNER,
                VIEW_PILOT,
                VIEW_CARGO,
                VIEW_COMMANDER
            ],
            "Visuals"
        ),
        **dict.fromkeys(
            [
                SHADOW,
                SHADOW_VIEW_CARGO,
                SHADOW_VIEW_PILOT,
                SHADOW_VIEW_GUNNER
            ],
            "Shadows"
        ),
        **dict.fromkeys(
            [
                GEOMETRY,
                GEOMETRY_BUOY,
                GEOMETRY_PHYSX,
                VIEW_GEOMETRY,
                FIRE_GEOMETRY,
                VIEW_CARGO_GEOMETRY,
                VIEW_CARGO_FIRE_GEOMETRY,
                VIEW_COMMANDER_GEOMETRY,
                VIEW_COMMANDER_FIRE_GEOMETRY,
                VIEW_PILOT_GEOMETRY,
                VIEW_PILOT_FIRE_GEOMETRY,
                VIEW_GUNNER_GEOMETRY,
                VIEW_GUNNER_FIRE_GEOMETRY,
                UNDERGROUND
            ],
            "Geometries"
        ),
        **dict.fromkeys(
            [
                MEMORY,
                LANDCONTACT,
                HITPOINTS
            ],
            "Point clouds"
        ),
        **dict.fromkeys(
            [
                EDIT,
                ROADWAY,
                PATHS,
                SUBPARTS,
                WRECKAGE,
                GROUNDLAYER,
                NAVIGATION,
                UNKNOWN
            ],
            "Misc"
        )
    }

    GROUPS: dict[str, dict[int, str]] = {
        'TYPE': GROUPS_TYPE,
        # 'CONTEXT': GROUPS_CONTEXT,
        'NONE': {}
    }

    def __init__(self, lod: int = 0, res: int = 0) -> None:
        self.lod: int = lod
        self.res: int = res
        self.source: float | None = None  # field to store the originally read float value for debug purposes

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self)) and self.get() == other.get()

    def __float__(self) -> float:
        return float(self.encode(self.lod, self.res))

    @classmethod
    def encode(cls, lod: int, resolution: int) -> float:
        if lod in (cls.VISUAL, cls.UNKNOWN):
            return resolution

        lookup = {v: k for k, v in cls.SIGNATURE_MAP.items()}
        signature = lookup.get(lod)
        if signature is not None:
            return float(signature)

        if lod == cls.VIEW_CARGO:
            return 1.2e3 + resolution
        elif lod == cls.SHADOW:
            return 1.0e4 + resolution
        elif lod == cls.EDIT:
            return 2.0e4 + resolution
        elif lod == cls.VIEW_CARGO_GEOMETRY:
            return 8.0e15 + resolution * 1e13
        elif lod == cls.SHADOW_VIEW_CARGO:
            return 1.8e16 + resolution * 1e13

        return resolution

    @classmethod
    def decode(cls, signature: float) -> tuple[int, int]:
        if signature < 1e3:
            return cls.VISUAL, round(signature)
        elif 1.2e3 <= signature < 1.3e3:
            return cls.VIEW_CARGO, round(signature - 1.2e3)
        elif 1.0e4 <= signature < 1.2e4:
            return cls.SHADOW, round(signature - 1e4)
        elif 2e4 <= signature < 3e4:
            return cls.EDIT, round(signature - 2e4)

        string = "%.3e" % signature
        lod = cls.SIGNATURE_MAP.get(string)
        if lod is not None:
            return lod, 0

        exp = int(string[-2:])
        if exp == 15:
            return cls.VIEW_CARGO_GEOMETRY, int(string[2:4])
        elif exp == 16:
            return cls.SHADOW_VIEW_CARGO, int(string[3:5])

        return cls.UNKNOWN, round(signature)

    @classmethod
    def from_float(cls, value: float) -> Self:
        output = cls(*cls.decode(value))
        output.source = value
        return output

    def set_from_float(self, value: float) -> None:
        self.lod, self.res = self.decode(value)
        self.source = value

    def set(self, lod: int, res: int) -> None:
        self.lod = lod
        self.res = res

    def get(self) -> tuple[int, int]:
        return self.lod, self.res

    def get_group_name(self, grouping: str) -> str:
        group_dict = self.GROUPS.get(grouping)
        if group_dict is None:
            return "Misc"

        return group_dict.get(self.lod, "Misc")

    @classmethod
    def build_name(cls, lod: int, res: int) -> str:
        name, _ = cls.INFO_MAP.get(lod, cls.INFO_MAP[cls.UNKNOWN])

        if lod in cls.LODS_WITH_RESOLUTION:
            return "%s %d" % (name, res)

        return name

    def name(self) -> str:
        return self.build_name(self.lod, self.res)


class P3D_LOD():
    def __init__(self) -> None:
        self.signature: bytes = b"P3DM"
        self.version: tuple[int, int] = (28, 256)
        self.flags: int = 0x00000000
        self.resolution: P3D_LOD_Resolution = P3D_LOD_Resolution()

        self.verts: list[tuple[float, float, float, int]] = []
        self.normals: list[tuple[float, float, float]] = []
        self.faces: list[
            tuple[
                list[int],
                list[int],
                list[tuple[float, float]],
                str,
                str,
                int
            ]
        ] = []
        self.taggs: list[P3D_TAGG] = []

    struct_vert = struct.Struct('<fffI')
    struct_normal = struct.Struct('<fff')
    struct_face = struct.Struct('<IIff')

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self)) and other.resolution == self.resolution

    # Reading

    @classmethod
    def read_vert(cls, file: BinaryIO) -> tuple[float, float, float, int]:
        x: float
        y: float
        z: float
        flag: int
        x, z, y, flag = cls.struct_vert.unpack(file.read(16))
        return x, y, z, flag

    def read_verts(self, file: BinaryIO, count_verts: int) -> None:
        self.verts = [self.read_vert(file) for _ in range(count_verts)]

    @classmethod
    def read_normal(cls, file: BinaryIO) -> tuple[float, float, float]:
        x: float
        y: float
        z: float
        x, z, y = cls.struct_normal.unpack(file.read(12))
        return -x, -y, -z

    def read_normals(self, file: BinaryIO, count_normals: int) -> None:
        self.normals = [self.read_normal(file) for i in range(count_normals)]

    @classmethod
    def read_face(
        cls,
        file: BinaryIO
    ) -> tuple[
        list[int],
        list[int],
        list[tuple[float, float]],
        str,
        str,
        int
    ]:
        count_sides = binary.read_ulong(file)
        vertices: list[int] = []
        normals: list[int] = []
        uvs: list[tuple[float, float]] = []

        vert: int
        norm: int
        u: float
        v: float
        for _ in range(count_sides):
            vert, norm, u, v = cls.struct_face.unpack(file.read(16))
            vertices.append(vert)
            normals.append(norm)
            uvs.append((u, 1 - v))

        if count_sides < 4:
            file.seek(16, 1)

        flag = binary.read_ulong(file)
        texture = binary.read_asciiz(file)
        material = binary.read_asciiz(file)

        return vertices, normals, uvs, texture, material, flag

    def read_faces(self, file: BinaryIO, count_faces: int) -> None:
        self.faces = [self.read_face(file) for i in range(count_faces)]

    @classmethod
    def read(cls, file: BinaryIO) -> Self:
        signature = file.read(4)
        if signature != b"P3DM":
            raise P3D_Error("Unsupported LOD type: %s" % str(signature))

        vmajor, vminor = binary.read_ulongs(file, 2)
        if (vmajor, vminor) != (0x1c, 0x100):
            raise P3D_Error("Unsupported LOD version: %d.%d" % (vmajor, vminor))

        output = cls()
        output.version = (vmajor, vminor)

        count_verts, count_normals, count_faces, flags = binary.read_ulongs(file, 4)
        output.flags = flags

        output.read_verts(file, count_verts)
        output.read_normals(file, count_normals)
        output.renormalize_normals()
        output.read_faces(file, count_faces)

        tagg_signature = binary.read_char(file, 4)
        if tagg_signature != "TAGG":
            raise P3D_Error("Invalid TAGG section signature: %s" % tagg_signature)

        while True:
            tagg = P3D_TAGG.read(file, count_verts, count_faces)
            if tagg.name == "#EndOfFile#":
                break

            if tagg.active:
                output.taggs.append(tagg)

        output.resolution.set_from_float(binary.read_float(file))

        return output

    # Writing

    def write_vert(self, file: BinaryIO, vert: tuple[float, float, float, int]) -> None:
        file.write(self.struct_vert.pack(vert[0], vert[2], vert[1], vert[3]))

    def write_verts(self, file: BinaryIO) -> None:
        for vert in self.verts:
            self.write_vert(file, vert)

    def write_normal(self, file: BinaryIO, normal: tuple[float, float, float]) -> None:
        file.write(self.struct_normal.pack(-normal[0], -normal[2], -normal[1]))

    def write_normals(self, file: BinaryIO) -> None:
        for vector in self.normals:
            self.write_normal(file, vector)

    def write_face(
        self,
        file:
        BinaryIO,
        face: tuple[
            list[int],
            list[int],
            list[tuple[float, float]],
            str,
            str,
            int
        ]
    ) -> None:
        count_sides = len(face[0])
        binary.write_ulong(file, count_sides)

        for i in range(count_sides):
            file.write(self.struct_face.pack(face[0][i], face[1][i], face[2][i][0], face[2][i][1]))

        if count_sides < 4:
            file.write(bytearray(16))

        binary.write_ulong(file, face[5])
        binary.write_asciiz(file, face[3])
        binary.write_asciiz(file, face[4])

    def write_faces(self, file: BinaryIO) -> None:
        for face in self.faces:
            self.write_face(file, face)

    def write(self, file: BinaryIO) -> None:
        file.write(self.signature)
        binary.write_ulong(file, *self.version)

        count_verts = len(self.verts)
        count_normals = len(self.normals)
        count_faces = len(self.faces)

        binary.write_ulong(file, count_verts, count_normals, count_faces, self.flags)

        self.write_verts(file)
        self.write_normals(file)
        self.write_faces(file)

        binary.write_chars(file, "TAGG")

        for tagg in self.taggs:
            tagg.write(file)

        eof = P3D_TAGG()
        eof.name = "#EndOfFile#"
        eof.write(file)

        binary.write_float(file, float(self.resolution))

    # Operations

    # The normals are stored as triplets of IEEE-754 32bit floating numbers,
    # which potentially result in a not normalized vector, which causes issues
    # in Blender, so the vectors need to be renormalized before usage.
    def renormalize_normals(self) -> None:
        renormalized = []
        for normal in self.normals:
            length = math.sqrt(normal[0]**2 + normal[1]**2 + normal[2]**2)

            if length == 0:
                renormalized.append(normal)
                continue

            coef = 1 / length
            renormalized.append((normal[0] * coef, normal[1] * coef, normal[2] * coef))

        self.normals = renormalized

    def pydata(self) -> tuple[
        list[tuple[float, float, float]],
        list[tuple[int, int]],
        list[list[int]]
    ]:
        verts = [vert[0:3] for vert in self.verts]
        faces = [face[0] for face in self.faces]

        return verts, [], faces

    def clean_taggs(self) -> None:
        self.taggs = [tagg for tagg in self.taggs if tagg.active]

    # Generate lookup dictionary for all unique materials. Primarily called
    # from the parent MLOD object, so the dictionary is edited in place, not
    # returned.
    def get_materials(self, materials: dict[tuple[str, str], int] = {}) -> None:
        for face in self.faces:
            texture = face[3]
            material = face[4]

            if (texture, material) not in materials:
                materials[(texture, material)] = len(materials)

    # Generate the necessary material index for each face, as well
    # as the indices of the used materials in each material slot.
    def get_sections(self, materials: dict[tuple[str, str], int]) -> tuple[list[int], list[int]]:
        slot_indices: list[int] = []
        slot_material_indices: list[int] = []

        last_idx = None
        face_idx = 0

        for face in self.faces:
            texture = face[3]
            material = face[4]

            idx = materials[(texture, material)]
            if last_idx is None:
                last_idx = idx
                slot_material_indices.append(idx)

            if idx != last_idx:
                slot_material_indices.append(idx)
                face_idx += 1
                last_idx = idx

            slot_indices.append(face_idx)

        return slot_indices, slot_material_indices

    def get_sections_merged(self, materials: dict[tuple[str, str], int]) -> tuple[list[int], list[int]]:
        slot_indices: list[int] = []
        material_slot_indices: dict[int, int] = {}

        for face in self.faces:
            texture = face[3]
            material = face[4]

            material_idx = materials[(texture, material)]
            slot_idx = material_slot_indices.get(material_idx)
            if slot_idx is None:
                slot_idx = len(material_slot_indices)
                material_slot_indices[material_idx] = slot_idx

            slot_indices.append(slot_idx)

        return slot_indices, list(material_slot_indices.keys())

    def renumber_components(self) -> int:
        counter = 1
        for tagg in self.taggs:
            if not re.match(r"component\d+", tagg.name, re.IGNORECASE):
                continue

            tagg.name = "component%02d" % counter
            counter += 1

        return counter

    # Blender only allows vertex group names to have up to 63 characters.
    # Since proxy selection names (file paths) are often longer than that,
    # they have to be replaced by formatted placeholders and later looked up
    # from a dictionary when needed.
    def proxies_to_placeholders(self) -> dict[str, tuple[str, int]]:
        regex_proxy = r"proxy:(.*)\.(\d+)"

        lookup: dict[str, tuple[str, int]] = {}

        proxy_idx = 0
        for tagg in self.taggs:
            if not tagg.is_proxy():
                continue

            m = re.match(regex_proxy, tagg.name)
            if m is None:
                continue

            data = m.groups()
            name = "@proxy_%d" % proxy_idx
            lookup[name] = (data[0], int(data[1]))
            tagg.name = name

            proxy_idx += 1

        return lookup

    def placeholders_to_proxies(self, lookup: dict[str, tuple[str, int]]) -> None:
        if len(lookup) == 0:
            return

        for tagg in self.taggs:
            if not tagg.name.startswith("@proxy_"):
                continue

            data = lookup.get(tagg.name)
            if not data:
                continue

            tagg.name = "proxy:%s.%03d" % (data[0], data[1])

    # Extract the UVSet 0 embedded into the face data, and return a dictionary
    # of all UVSets, unique by ID. If UVSet 0 is also found as a TAGG, the TAGG
    # data takes precedence over the embedded values.
    def uvsets(self) -> dict[int, list[tuple[float, float]]]:
        sets = {0: [uv for face in self.faces for uv in face[2]]}
        for tagg in self.taggs:
            if not isinstance(tagg.data, P3D_TAGG_DataUVSet):
                continue

            sets[tagg.data.id] = tagg.data.uvs

        return sets

    # Generate loop normals list that can be directly used by the Blender API
    # mesh.normals_split_custom_set() function
    def loop_normals(self) -> list[tuple[float, float, float]]:
        return [self.normals[item] for face in self.faces for item in face[1]]

    # Collect and group the used vertex flag values for setting up
    # the flag data layer and flag groups object data.
    def flag_groups_vertex(self) -> tuple[list[int], list[int]]:
        groups: dict[int, int] = {}
        values: list[int] = []

        for vert in self.verts:
            flag = vert[3]
            group = groups.get(flag)
            if group is None:
                group = len(groups)
                groups[flag] = group

            values.append(group)

        return list(groups.keys()), values

    # Collect and group the used face flag values for setting up
    # the flag data layer and flag groups object data.
    def flag_groups_face(self) -> tuple[list[int], list[int]]:
        groups: dict[int, int] = {}
        values: list[int] = []

        for face in self.faces:
            flag = face[5]
            group = groups.get(flag)
            if group is None:
                group = len(groups)
                groups[flag] = group

            values.append(group)

        return list(groups.keys()), values

    # Change every file path, and selection name to lower case for a uniform output.
    def force_lowercase(self) -> None:
        self.faces = [
            (verts, normals, uvs, tex.lower(), mat.lower(), flag)
            for verts, normals, uvs, tex, mat, flag
            in self.faces
        ]

        for tagg in self.taggs:
            if tagg.is_selection():
                tagg.name = tagg.name.lower()
            elif type(tagg.data) is P3D_TAGG_DataProperty:
                tagg.data.key = tagg.data.key.lower()
                tagg.data.value = tagg.data.value.lower()

    def selections_to_english(self) -> None:
        for tagg in self.taggs:
            tagg.name = translate.czech_to_english.get(tagg.name.lower(), tagg.name)

    def selections_to_czech(self) -> None:
        for tagg in self.taggs:
            tagg.name = translate.english_to_czech.get(tagg.name.lower(), tagg.name)


class P3D_MLOD():
    def __init__(self) -> None:
        self.source: str = ""
        self.version: int = 257
        self.signature: bytes = b"MLOD"

        self.lods: list[P3D_LOD] = []

    @classmethod
    def read(cls, file: BinaryIO, first_lod_only: bool = False) -> Self:

        signature = file.read(4)
        if signature != b"MLOD":
            raise P3D_Error("Invalid MLOD signature: %s" % str(signature))

        version = binary.read_ulong(file)
        if version != 257:
            raise P3D_Error("Unsupported MLOD version: %d" % version)

        output = cls()
        output.version = version

        count_lods = binary.read_ulong(file)
        if first_lod_only:
            count_lods = 1

        output.lods = [P3D_LOD.read(file) for i in range(count_lods)]

        return output

    @classmethod
    def read_file(cls, filepath: str, first_lod_only: bool = False) -> Self:
        output = None
        with open(filepath, "br") as file:
            output = cls.read(file, first_lod_only)

        output.source = filepath

        return output

    def write(self, file: BinaryIO) -> None:
        if len(self.lods) == 0:
            raise P3D_Error("Cannot write file with no LODs")

        file.write(self.signature)
        binary.write_ulong(file, self.version)
        binary.write_ulong(file, len(self.lods))
        for lod in self.lods:
            lod.write(file)

    def write_file(self, filepath: str) -> None:
        with open(filepath, "wb") as file:
            self.write(file)

    def get_materials(self) -> dict[tuple[str, str], int]:
        materials = {("", ""): 0}

        for lod in self.lods:
            lod.get_materials(materials)

        return materials

    # Function to ensure uniform format in the output files regardless
    # of the casing in Blender.
    def force_lowercase(self) -> None:
        for lod in self.lods:
            lod.force_lowercase()

    def find_lod(self, index: int = 0, resolution: int = 0) -> P3D_LOD | None:
        for lod in self.lods:
            if lod.resolution.get() == (index, resolution):
                return lod

        return None

    def get_duplicate_lods(self) -> list[int]:
        signatures: set[float] = set()
        duplicates: list[int] = []

        for i, lod in enumerate(self.lods):
            sign = float(lod.resolution)
            if sign in signatures:
                duplicates.append(i)
            else:
                signatures.add(sign)

        return duplicates
