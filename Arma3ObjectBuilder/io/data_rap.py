# Reader function to import data from rapified files.
# Format specifications: https://community.bistudio.com/wiki/raP_File_Format_-_Elite


from enum import Enum

from . import binary_handler as binary


class RAP_Error(Exception):
    def __str__(self):
        return "RAP - %s" % super().__str__()


class CFG_Formatter():
    def __init__(self, file):
        self.indent = 0
        self.file = file
    
    def write(self, value):
        self.file.write(self.indented(value) + "\n")
    
    def indented(self, value):
        return self.indent * "\t" + value
    
    @staticmethod
    def quoted(value):
        return "\"%s\"" % value
    
    def comment(self, content):
        self.write("// %s" % content)

    def class_delete(self, name):
        self.write("del %s;" % name)

    def class_reference(self, name):
        self.write("class %s;" % name)
    
    def class_copy(self, name, parent):
        self.write("class %s: %s {};" % (name, parent))
    
    def class_open(self, name, parent = ""):
        self.write("class %s%s {" % (name, ": %s" % parent if parent != "" else ""))
        self.indent += 1
    
    def class_close(self):
        self.indent -= 1
        self.write("};")
    
    def array_open(self, name):
        self.write("%s[] = {" % name)
        self.indent += 1
    
    def array_flagged_open(self, name):
        self.write("%s[] += {" % name)
        self.indent += 1
    
    def array_close(self):
        self.indent -= 1
        self.write("};")
    
    def array_empty(self, name):
        self.write("%s[] = {};" % name)
    
    def array_items(self, values):
        for item in values[:-1]:
            self.write(item + ",")
        
        self.write(values[-1])
    
    def property_string(self, name, value):
        self.write("%s = %s;" % (name, self.quoted(value)))
    
    def property_float(self, name, value):
        self.write("%s = %f;" % (name, value))
    
    def property_int(self, name, value):
        self.write("%s = %d;" % (name, value))
    
    def variable(self, name, value):
        self.write("%s = %s;" % (name, value))
    
    def enum_open(self):
        self.write("enum {")
        self.indent += 1

    def enum_close(self):
        self.indent -= 1
        self.write("};")
    
    def enum_item(self, name, value):
        self.write("%s = %d;" % (name, value))


# Internal data structure to store the read data.
class RAP():
    class EntryType(Enum):
        CLASS = 0
        SCALAR = 1
        ARRAY = 2
        EXTERN = 3
        DELETE = 4
        FLAGGED = 5

    class EntrySubType(Enum):
        NONE = 0
        STRING = 1
        FLOAT = 2
        LONG = 3
        ARRAY = 4
        VARIABLE = 5

    class EnumItem():
        def __init__(self):
            self.name = ""
            self.value = 0
        
        def __str__(self):
            return "%s = %s" % (self.name, self.value)

    class ClassBody():    
        def __init__(self):
            self.inherits = ""
            self.entry_count = 0
            self.entries = []
        
        def __str__(self):
            return "Inherits: %s" % (self.inherits if self.inherits != "" else "nothing")
        
        def find(self, name):
            for item in self.entries:
                if item.name.lower() == name.lower():
                    return item

    class Entry():
        def __init__(self):
            self.type = RAP.EntryType.CLASS
            self.subtype = RAP.EntrySubType.NONE
            self.name = ""
            self.value = ""

    class Class():
        def __init__(self):
            self.type = RAP.EntryType.CLASS
            self.subtype = RAP.EntrySubType.NONE
            self.name = ""
            self.value = ""
            self.body_offset = 0
            self.body = RAP.ClassBody()
        
        def __str__(self):
            if self.body:
                return "class %s {%d}" % (self.name, self.body.entry_count)
            return "class %s {...}" % self.name

    class Scalar():
        def __init__(self):
            self.type = RAP.EntryType.SCALAR
            self.subtype = RAP.EntrySubType.NONE
            self.name = ""
            self.value = ""

    class String():
        def __init__(self):
            self.type = RAP.EntryType.SCALAR
            self.subtype = RAP.EntrySubType.STRING
            self.name = ""
            self.value = ""
        
        def __str__(self):
            if self.name != "":
                return "%s = \"%s\";" % (self.name, self.value)
            return "\"%s\"" % self.value

    class Float():
        def __init__(self):
            self.type = RAP.EntryType.SCALAR
            self.subtype = RAP.EntrySubType.FLOAT
            self.name = ""
            self.value = 0.0
        
        def __str__(self):
            if self.name != "":
                return "%s = %f;" % (self.name, self.value)
            return "%f" % self.value

    class Long():
        def __init__(self):
            self.type = RAP.EntryType.SCALAR
            self.subtype = RAP.EntrySubType.LONG
            self.name = ""
            self.value = 0
        
        def __str__(self):
            if self.name != "":
                return "%s = %d;" % (self.name, self.value)
            return "%d" % self.value

    class Variable():
        def __init__(self):
            self.type = RAP.EntryType.SCALAR
            self.subtype = RAP.EntrySubType.VARIABLE
            self.name = ""
            self.value = ""
        
        def __str__(self):
            if self.name != "":
                return "%s = ""%s"";" % (self.name, self.value)
            return "\"%s\"" % self.value

    class ArrayBody():
        def __init__(self):
            self.type = RAP.EntryType.ARRAY
            self.subtype = RAP.EntrySubType.NONE
            self.name = ""
            self.value = ""
            self.element_count = 0
            self.elements = []

    class Array():
        def __init__(self):
            self.type = RAP.EntryType.ARRAY
            self.subtype = RAP.EntrySubType.NONE
            self.name = ""
            self.value = ""
            self.body = RAP.ArrayBody()
            self.flag = None
        
        def __str__(self):
            if self.body:
                return "%s[] = {%d};" % (self.name, self.body.element_count)
            return "%s[] = {...};" % self.name

    class External():
        def __init__(self):
            self.type = RAP.EntryType.EXTERN
            self.subtype = RAP.EntrySubType.NONE
            self.name = ""
            self.value = ""
        
        def __str__(self):
            return "class %s;" % self.name

    class Delete():
        def __init__(self):
            self.type = RAP.EntryType.DELETE
            self.subtype = RAP.EntrySubType.NONE
            self.name = ""
            self.value = ""
        
        def __str__(self):
            return "delete %s;" % self.name

    class Root():
        def __init__(self):
            self.enum_offset = 0
            self.body = RAP.ClassBody()
            self.enums = []


class RAP_Reader():
    @classmethod
    def read_entry_class_body(cls, file, body_offset):
        output = RAP.ClassBody()
        current_pos = file.tell()
        file.seek(body_offset, 0)
        
        output.inherits = binary.read_asciiz(file)
        output.entry_count = binary.read_compressed_uint(file)
        output.entries = cls.read_entries(file, output.entry_count)
        
        file.seek(current_pos, 0)
        
        return output
    
    @classmethod
    def read_entry_class(cls, file):
        output = RAP.Class()
        
        output.name = binary.read_asciiz(file)
        output.body_offset = binary.read_ulong(file)
        output.body = cls.read_entry_class_body(file, output.body_offset)
        
        return output
    
    @classmethod
    def read_entry_value(cls, file, sign):
        output = RAP.Scalar()
        
        if sign == 0:
            output = RAP.String()
            output.value = binary.read_asciiz(file)
        
        elif sign == 1:
            output = RAP.Float()
            output.value = binary.read_float(file)
        
        elif sign == 2:
            output = RAP.Long()
            output.value = binary.read_long(file)
        
        elif sign == 3:
            output = cls.read_entry_array_body(file)
            
        elif sign == 4:
            output = RAP.Variable()
            output.value = binary.read_asciiz(file)
            
        return output
            
    
    @classmethod
    def read_entry_scalar(cls, file):
        entry_sign = binary.read_byte(file)
        entry_name = binary.read_asciiz(file)
        
        output = cls.read_entry_value(file, entry_sign)
        output.name = entry_name
        
        return output
    
    @classmethod
    def read_entry_array_body(cls, file):
        output = RAP.ArrayBody()
        output.element_count = binary.read_compressed_uint(file)
        
        for i in range(output.element_count):
            output.elements.append(cls.read_entry_value(file, binary.read_byte(file)))
        
        return output
        
    @classmethod
    def read_entry_array(cls, file):
        output = RAP.Array()
        output.name = binary.read_asciiz(file)
        output.body = cls.read_entry_array_body(file)
        
        return output
    
    @classmethod
    def read_entry_array_flagged(cls, file):
        output = RAP.Array()
        output.flag = binary.read_long(file)
        output.name = binary.read_asciiz(file)
        output.body = cls.read_entry_array_body(file)
        
        return output
    
    @classmethod
    def read_entry_class_external(cls, file):
        output = RAP.External()
        output.name = binary.read_asciiz(file)
        
        return output
    
    @classmethod
    def read_entry_class_delete(cls, file):
        output = RAP.Delete()
        output.name = binary.read_asciiz(file)
        
        return output
    
    @classmethod
    def read_entry(cls, file):
        output = RAP.Entry()
        entry_sign = binary.read_byte(file)
        
        if entry_sign == 0:
            output = cls.read_entry_class(file)
            
        elif entry_sign == 1:
            output = cls.read_entry_scalar(file)
            
        elif entry_sign == 2:
            output = cls.read_entry_array(file)
            
        elif entry_sign == 3:
            output = cls.read_entry_class_external(file)
            
        elif entry_sign == 4:
            output = cls.read_entry_class_delete(file)
            
        elif entry_sign == 5:
            output = cls.read_entry_array_flagged(file)
        
        return output
    
    @classmethod
    def read_entries(cls, file, entry_count):
        output = []
        
        for i in range(entry_count):
            output.append(cls.read_entry(file))
        
        return output
    
    @classmethod
    def read_file(cls, filepath):
        output = RAP.Root()
        
        with open(filepath, "rb") as file:
            try:
                signature = file.read(4)
                if signature != b"\x00raP":
                    raise RAP_Error("Invalid RAP signature: %s" % str(signature))
                
                file.read(8)
                output.enum_offset = binary.read_ulong(file)
                
                # Body
                output_body = RAP.ClassBody()
                output_body.inherits = binary.read_asciiz(file)
                output_body.entry_count = binary.read_compressed_uint(file)
                output_body.entries = cls.read_entries(file, output_body.entry_count)
                
                output.body = output_body
                
                # Enums
                file.seek(output.enum_offset)
                enum_count = binary.read_ulong(file)
                for i in range(enum_count):
                    new_item = RAP.EnumItem()
                    new_item.name = binary.read_asciiz(file)
                    new_item.value = binary.read_ulong(file)
                    output.enums.append(new_item)
                    
                if file.peek():
                    raise RAP_Error("Invalid EOF")
                
            except:
                output = None
                
        return output
