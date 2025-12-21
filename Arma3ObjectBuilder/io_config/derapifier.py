# Reader functions to import data from rapified config files.
# Format specifications: https://community.bistudio.com/wiki/raP_File_Format_-_Elite
from typing import BinaryIO, cast
from io import BufferedReader


from . import data
from .. import binary


class RAP_Error(Exception):
    def __str__(self) -> str:
        return "RAP - %s" % super().__str__()


class Derapifier:
    @classmethod
    def read_array(cls, file: BinaryIO) -> data.CFGArray:
        count = binary.read_compressed_uint(file)
        members: list[data.CFGValue] = []
        for _ in range(count):
            sign = binary.read_byte(file)
            members.append(cls.read_value(file, sign))

        return data.CFGArray(members)

    @classmethod
    def read_value(cls, file: BinaryIO, sign: int) -> data.CFGValue:
        match sign:
            case 0:
                return data.CFGString(binary.read_asciiz(file))
            case 1:
                return data.CFGFloat(binary.read_float(file))
            case 2:
                return data.CFGInt(binary.read_ulong(file))
            case 3:
                return cls.read_array(file)

        raise RAP_Error("Unsupported value type")

    @classmethod
    def read_class(cls, file: BinaryIO, main: data.CFGClass | None = None) -> data.CFGClass:
        name = binary.read_asciiz(file)
        offset = binary.read_ulong(file)
        current = file.tell()
        file.seek(offset)

        parentname = binary.read_asciiz(file)
        parent = None
        if parentname != "":
            parent = data.CFGClass.resolve_parent(main, parentname)
            if not parent:
                raise RAP_Error("Could not resolve parent")

        out = data.CFGClass(name, parent, main)
        count = binary.read_compressed_uint(file)
        cls.read_entries(file, count, out)

        file.seek(current)

        return out

    @classmethod
    def read_entries(
        cls,
        file: BinaryIO,
        count: int,
        main: data.CFGClass | None = None
    ) -> tuple[list[data.CFGClass], list[data.CFGProperty]]:
        classes = main.classes if main else []
        properties = main.properties if main else []

        for _ in range(count):
            entry_sign = binary.read_byte(file)
            match entry_sign:
                case 0:
                    # Class entry
                    classes.append(cls.read_class(file, main))
                case 1:
                    # Scalar entry
                    sign = binary.read_byte(file)
                    name = binary.read_asciiz(file)
                    scalar = cls.read_value(file, sign)
                    properties.append(data.CFGProperty(name, scalar))
                case 2:
                    # Array entry
                    name = binary.read_asciiz(file)
                    array: data.CFGArray = cast(data.CFGArray, cls.read_value(file, 3))
                    properties.append(data.CFGProperty(name, array))
                case 3:
                    # External reference
                    classes.append(data.CFGClass(binary.read_asciiz(file), None, main, True))
                case 4:
                    # Delete statement
                    # raise RAP_Error("Delete statements are not supported")
                    binary.read_asciiz(file)  # dump delete statements
                case 5:
                    # Array extension
                    name = binary.read_asciiz(file)
                    file.read(4)  # skip flag, always 1
                    array = cast(data.CFGArray, cls.read_value(file, 3))
                    array.extends = True
                    properties.append(data.CFGProperty(name, array))

        return classes, properties

    @classmethod
    def read(cls, file: BufferedReader) -> data.CFG:
        signature = file.read(4)
        if signature != b"\x00raP":
            raise RAP_Error("Invalid RAP signature: %s" % str(signature))

        file.read(8)
        enum_offset = binary.read_ulong(file)

        # Body
        root = data.CFGClass("root")
        file.read(1)  # skip empty parent
        count_entries = binary.read_compressed_uint(file)
        classes, properties = cls.read_entries(file, count_entries)
        root.classes = classes
        root.properties = properties

        # Enums
        file.seek(enum_offset)
        enum_count = binary.read_ulong(file)
        for _ in range(enum_count):
            binary.read_asciiz(file)  # dump name
            file.read(4)  # dump value

        if file.peek():
            raise RAP_Error("Invalid EOF")

        return data.CFG(root)

    @classmethod
    def read_file(cls, path: str) -> data.CFG:
        with open(path, "rb") as file:
            return cls.read(file)
