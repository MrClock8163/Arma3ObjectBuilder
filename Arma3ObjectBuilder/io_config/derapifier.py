# Reader functions to import data from rapified config files.
# Format specifications: https://community.bistudio.com/wiki/raP_File_Format_-_Elite


from . import data
from .. import binary


class RAP_Error(Exception):
    def __str__(self):
        return "RAP - %s" % super().__str__()


class Derapifier:
    @classmethod
    def read_array(cls, file):
        count = binary.read_compressed_uint(file)
        members = []
        for i in range(count):
            sign = binary.read_byte(file)
            members.append(cls.read_value(file, sign))

        return data.CFGArray(members)

    @classmethod
    def read_value(cls, file, sign):
        if sign == 0:
            return data.CFGLiteralString(binary.read_asciiz(file))
        elif sign == 1:
            return data.CFGLiteralFloat(binary.read_float(file))
        elif sign == 2:
            return data.CFGLiteralLong(binary.read_ulong(file))
        elif sign == 3:
            return cls.read_array(file)

        raise RAP_Error("Unsupported value type")

    @classmethod
    def read_class(cls, file, main=None):
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
    def read_entries(cls, file, count, main=None):
        classes = main.classes if main else []
        properties = main.properties if main else []

        for i in range(count):
            entry_sign = binary.read_byte(file)
            if entry_sign == 0:
                classes.append(cls.read_class(file, main))
            elif entry_sign == 1:
                sign = binary.read_byte(file)
                name = binary.read_asciiz(file)
                value = cls.read_value(file, sign)
                properties.append(data.CFGProperty(name, value))
            elif entry_sign == 2:
                name = binary.read_asciiz(file)
                value = cls.read_value(file, 3)
                properties.append(data.CFGProperty(name, value))
            elif entry_sign == 3:
                classes.append(data.CFGClass(binary.read_asciiz(file), None, main, True))
            elif entry_sign == 4:
                # raise RAP_Error("Delete statements are not supported")
                binary.read_asciiz(file)  # dump delete statements
            elif entry_sign == 5:
                name = binary.read_asciiz(file)
                file.read(4)  # skip flag, always 1
                value = cls.read_value(file, 3)
                value.extends = True
                properties.append(data.CFGProperty(name, value))

        return classes, properties

    @classmethod
    def read(cls, file):
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
        for i in range(enum_count):
            binary.read_asciiz(file)  # dump name
            file.read(4)  # dump value

        if file.peek():
            raise RAP_Error("Invalid EOF")

        return data.CFG(root)

    @classmethod
    def read_file(cls, path):
        with open(path, "rb") as file:
            return cls.read(file)
