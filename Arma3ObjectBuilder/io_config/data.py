# Class structure for handling config data structures.


class CFG_Error(Exception):
    def __str__(self):
        return "CFG - %s" % super().__str__()


class CFGNode:
    pass


class CFGLiteralString(CFGNode):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return "\"%s\"" % self.value

    def topy(self):
        return self.value

    def format(self, indent=0):
        return "%s\"%s\"" % ("\t" * indent, self.value.replace("\"", "\"\""))


class CFGLiteralLong(CFGNode):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return "%f" % self.value

    def topy(self):
        return self.value

    def format(self, indent=0):
        return "%s%d" % ("\t" * indent, self.value)


class CFGLiteralFloat(CFGNode):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return "%f" % self.value

    def topy(self):
        return self.value

    def format(self, indent=0):
        return "%s%f" % ("\t" * indent, self.value)


class CFGArray(CFGNode):
    def __init__(self, members, extends=False):
        self.members = members
        self.extends = extends

    def __repr__(self):
        return "{...}"

    def topy(self):
        out = []

        for item in self.members:
            out.append(item.topy())

        return out

    def format(self, indent=0):
        padding = "\t" * indent

        if len(self.members) == 0:
            return "%s{}\n" % padding

        value = "%s{\n" % ("\t" * indent)
        items = []
        for item in self.members:
            items.append(item.format(indent + 1))

        value += ",\n".join(items) + "\n"
        value += "%s}" % ("\t" * indent)

        return value


class CFGProperty(CFGNode):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    @classmethod
    def type_from_py(cls, value):
        valuetype = type(value)
        if valuetype not in (str, int, float, list):
            raise ValueError("Could not create value (%s) from type (%s)" % (value, valuetype))

        if valuetype is str:
            return CFGLiteralString(value)
        elif valuetype is int:
            return CFGLiteralLong(value)
        elif valuetype is float:
            return CFGLiteralFloat(value)

        members = [cls.type_from_py(item) for item in value]

        return CFGArray(members)

    @classmethod
    def from_py(cls, name, value):
        if type(name) is not str or len(name) < 1:
            raise ValueError("Cannot create property (%s) without valid name (%s)" % (value, name))

        return cls(name, cls.type_from_py(value))

    def __repr__(self):
        return "%s = %s" % (self.name, repr(self.value))

    def __eq__(self, other):
        return type(self) is type(other) and self.name.lower() == other.name.lower()

    def format(self, indent=0):
        value = ""
        padding = "\t" * indent
        if type(self.value) is CFGArray:
            op = "+=" if self.value.extends else "="
            if len(self.value.members) == 0:
                return "%s%s[] %s {};\n" % (padding, self.name, op)

            value = "%s%s[] %s {\n" % (padding, self.name, op)
            items = [item.format(indent + 1) for item in self.value.members]

            value += ",\n".join(items) + "\n"
            value += "%s};\n" % padding
        else:
            value = "%s%s = %s;\n" % (padding, self.name, self.value.format())

        return value

    def datatype(self):
        valuetype = type(self.value)
        if valuetype is CFGLiteralLong:
            return 'LONG'
        elif valuetype is CFGLiteralFloat:
            return 'FLOAT'
        elif valuetype is CFGLiteralString:
            return 'STRING'

        return 'ARRAY'


class CFGClass(CFGNode):
    def __init__(self, name, parent=None, main=None, external=False):
        self.name = name
        self.parent = parent
        self.properties = []
        self.classes = []
        self.main = main
        self.external = external

    def __repr__(self):
        if self.external:
            return "class %s;" % self.name
        elif self.parent is None:
            return "class %s" % self.name

        return "class %s: %s" % (self.name, self.parent.name)

    def __eq__(self, other):
        return type(self) is type(other) and self.name.lower() == other.name.lower()

    @classmethod
    def resolve_parent_in_inheritance(cls, main, parentname):
        if not main:
            return None

        for item in main.classes:
            if item.name.lower() == parentname.lower():
                return item

        return cls.resolve_parent_in_inheritance(main.parent, parentname)

    @classmethod
    def resolve_parent_in_scopes(cls, main, parentname):
        if not main:
            return None

        for item in main.classes:
            if item.name.lower() == parentname.lower():
                return item

        return cls.resolve_parent_in_scopes(main.main, parentname)

    @classmethod
    def resolve_parent(cls, main, parentname):
        parent = cls.resolve_parent_in_inheritance(main, parentname)
        if parent:
            return parent

        return cls.resolve_parent_in_scopes(main.main, parentname)

    def get_class(self, steps):
        if len(steps) == 0:
            return self

        step = steps.pop(0).lower()
        for item in self.classes:
            if item.name.lower() == step:
                if len(steps) == 0:
                    return item

                return item.get_class(steps)

        if self.parent is None:
            return None

        steps.insert(0, step)
        return self.parent.get_class(steps)

    def get_prop(self, propname, default=None):
        for item in self.properties:
            if item.name.lower() == propname.lower():
                return item.value

        if self.parent is None:
            return default

        return self.parent.get_prop(propname, default)

    def get_path(self):
        steps = [self.name]
        main = self.main
        while main is not None:
            steps.insert(0, main.name)

            main = main.main

        return "/".join(steps)

    def get_ancestors(self):
        lineage = [self]
        if self.parent is None:
            return lineage

        lineage.extend(self.parent.get_ancestors())
        return lineage

    def compile(self):
        for item in self.classes:
            item.compile()

        if self.parent is None:
            return

        for item in self.parent.properties:
            if item not in self.properties:
                self.properties.append(item)
                continue

            prop = self.get_prop(item.name)
            if type(prop) is not CFGArray or not prop.extends or type(item.value) is not CFGArray or item.value.extends:
                continue

            prop.members = item.value.members + prop.members
            prop.extends = item.value.extends

        for item in self.parent.classes:
            if item not in self.classes:
                self.classes.append(item)

    def format(self, indent=0):
        padding = "\t" * indent
        value = ""

        if self.external:
            return "%sclass %s;\n" % (padding, self.name)

        if self.parent is not None:
            value += "%sclass %s: %s {" % (padding, self.name, self.parent.name)
        else:
            value += "%sclass %s {" % (padding, self.name)

        if len(self.properties) == 0 and len(self.classes) == 0:
            value += "};\n"
            return value
        else:
            value += "\n"

        for prop in self.properties:
            value += prop.format(indent + 1)

        for cls in self.classes:
            value += cls.format(indent + 1)

        value += "%s};\n" % padding
        return value

    def as_dict(self):
        propdict = {}
        classdict = {}
        data = {
            "properties": propdict,
            "classes": classdict,
            "external": self.external,
            "parent": self.parent.name if self.parent else None
        }

        for prop in self.properties:
            propdict[prop.name] = prop.value.topy()

        for cls in self.classes:
            classdict[cls.name] = cls.as_dict()

        return data

    @classmethod
    def from_dict(cls, name, main, data):
        parent = None
        parentname = data.get("parent")
        if parentname is not None:
            parent = cls.resolve_parent(main, parentname)
            if not parent:
                raise CFG_Error("Could not resolve parent (%s) of (%s) in (%s)" % (parentname, name, main.get_path()))

        out = cls(name, parent, main, data.get("external", False))

        for name, value in data.get("properties", {}).items():
            out.properties.append(CFGProperty.from_py(name, value))

        for name, item in data.get("classes", {}).items():
            out.classes.append(CFGClass.from_dict(name, out, item))

        return out

    def isreference(self):
        if self.external:
            return True

        if len(self.properties) > 0:
            return False

        for cls in self.classes:
            if not cls.isreference():
                return False

        return True


class CFG:
    def __init__(self, root):
        self.root = root

    def __repr__(self):
        return "CFG: %s" % self.root.name

    def get_class(self, path):
        steps = path.replace(" ", "").split("/")
        step = steps.pop(0)
        if step != self.root.name:
            return None
        elif len(steps) == 0:
            return self.root

        return self.root.get_class(steps)

    def get_prop(self, path, default=None):
        steps = path.replace(" ", "").split("/")
        step = steps.pop(0)

        if len(steps) == 0 or step != self.root.name:
            return default

        propname = steps.pop()
        leaf = self.root.get_class(steps)
        if leaf is None:
            return default

        return leaf.get_prop(propname, default)

    def compile(self):
        self.root.compile()

    def format(self):
        value = ""
        for prop in self.root.properties:
            value += prop.format()

        for cls in self.root.classes:
            value += cls.format()

        return value

    def as_dict(self):
        return {self.root.name: self.root.as_dict()}

    @classmethod
    def from_dict(cls, data):
        if len(data) != 1:
            raise ValueError("Root node must be a single key: %s" % list(data.keys()))

        name = list(data.keys())[0]
        root = CFGClass.from_dict(name, None, data[name])

        return cls(root)
