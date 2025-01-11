# Parser implementation for reading files using the standard config syntax.


from . import tokenizer as t
from . import data


class CFGParser:
    def __init__(self, tokens):
        self.ptr = 0
        self.tokens = tokens

    def read_token(self, count=1):
        if self.ptr == len(self.tokens):
            return []

        if count == 1:
            result = self.tokens[self.ptr]
            self.ptr += 1
            return result

        tokens = self.tokens[self.ptr:self.ptr+count]
        self.ptr += len(tokens)
        return tokens

    def peek_token(self, count=1):
        if self.ptr == len(self.tokens):
            return []

        if count == 1:
            return self.tokens[self.ptr]

        tokens = self.tokens[self.ptr:self.ptr+count]
        return tokens

    def seek_token(self, offset, ref):
        token_count = len(self.tokens)
        if ref == 2:
            offset += token_count - 1
        elif ref == 1:
            offset += self.ptr

        if not (0 <= offset < token_count):
            raise ValueError("Offset (%d) out of range (0 - %d)" % (offset, token_count-1))

        self.ptr = offset

    @staticmethod
    def compare_tokens(got, expected):
        for t, exp in zip(got, expected):
            if exp is not None and type(t) is not exp:
                return False

        return True

    def parse_identifier(self):
        value = ""
        nexttoken = self.peek_token()
        while nexttoken and type(nexttoken) in (t.TIdentifier, t.TLiteralLong):
            value += str(nexttoken.value)
            self.read_token()
            nexttoken = self.peek_token()

        if value == "":
            return None

        return t.TIdentifier(value)

    def recover_literal(self):
        values = []
        nexttoken = self.peek_token()
        while nexttoken and type(nexttoken) in (t.TIdentifier, t.TLiteralLong, t.TLiteralFloat, t.TLiteralString):
            values.append(nexttoken)
            self.read_token()
            nexttoken = self.peek_token()

        return t.TLiteralString(" ".join([("\"\"%s\"\"" % t.value) if type(t) is t.TLiteralString else str(t.value) for t in values]))

    def parse_literal(self):
        items = []
        while self.peek_token() and type(self.peek_token()) not in (t.TComma, t.TSemicolon, t.TBraceClose):
            items.append(self.read_token())

        count = len(items)

        if count == 0:
            return data.CFGLiteralString("")

        if count == 1:
            itemtype = type(items[0])
            if itemtype is t.TLiteralString:
                return data.CFGLiteralString(items[0].value)
            elif itemtype is t.TLiteralLong:
                return data.CFGLiteralLong(items[0].value)
            elif itemtype is t.TLiteralFloat:
                return data.CFGLiteralFloat(items[0].value)

            return data.CFGLiteralString(str(items[0]))

        if count == 2 and type(items[0]) in (t.TPlus, t.TMinus):
            if type(items[1]) is t.TLiteralLong:
                return data.CFGLiteralLong(items[1].value * (-1 if type(items[0]) is t.TMinus else 1))
            elif type(items[1]) is t.TLiteralFloat:
                return data.CFGLiteralFloat(items[1].value * (-1 if type(items[0]) is t.TMinus else 1))

        return data.CFGLiteralString(" ".join([("\"%s\"" % token) if type(token) is t.TLiteralString else str(token) for token in items]))

    def parse_array(self, main, propname):
        if type(self.read_token()) is not t.TBraceOpen:
            raise data.CFG_Error("Unexpected token at array start of property (%s) in (%s)" % (propname, main.get_path()))

        nexttoken = self.peek_token()
        if nexttoken and type(nexttoken) is t.TBraceClose:
            self.read_token()
            return data.CFGArray([])

        members = []
        while nexttoken and type(nexttoken) is not t.TBraceClose:
            if type(nexttoken) is t.TBraceOpen:
                members.append(self.parse_array(main, propname))
            else:
                members.append(self.parse_literal())

            nexttoken = self.peek_token()
            if type(nexttoken) is t.TComma:
                self.read_token()
                nexttoken = self.peek_token()

        self.read_token()

        return data.CFGArray(members)

    def parse_property(self, main):
        name = self.parse_identifier()
        if not name:
            raise data.CFG_Error("Could not parse property name in (%s)" % (main.get_path()))

        value = None
        if type(self.peek_token()) is t.TEquals:
            self.read_token()
            value = self.parse_literal()
            end = self.read_token()
            if not end or type(end) is not t.TSemicolon:
                raise data.CFG_Error("Expected semicolon instead of (%s) after assignment of property (%s) in (%s)" % (
                    end, name, main.get_path()))

        elif self.compare_tokens(self.peek_token(2), [t.TBracketOpen, t.TBracketClose]):
            self.read_token(2)
            operator = self.read_token()
            optype = type(operator)
            extends = False
            if not operator or optype not in (t.TEquals, t.TPlus) or optype is t.TPlus and type(self.peek_token()) is not t.TEquals:
                raise data.CFG_Error("Unexpected array assignment operator (%s) for property (%s) in (%s)" % (operator, name, main.get_path()))

            if optype is t.TPlus:
                self.read_token()
                extends = True

            value = self.parse_array(main, name)
            value.extends = extends

            end = self.read_token()
            if not end or type(end) is not t.TSemicolon:
                raise data.CFG_Error("Expected semicolon instead of (%s) after assignment of property (%s) in (%s)" % (end, name, main.get_path()))

        return data.CFGProperty(name.value, value)

    def parse_class_header(self, main=None):
        self.read_token()  # skip class keyword
        name = self.parse_identifier()
        if not name:
            raise data.CFG_Error("Could not parse class name in (%s)" % (main.get_path()))

        delimiter = self.read_token()
        delimitertype = type(delimiter)
        if delimitertype not in (t.TColon, t.TSemicolon, t.TBraceOpen):
            raise data.CFG_Error("Unexpected token (%s) after class name (%s) in (%s)" % (delimiter, name, main.get_path()))

        if delimitertype is t.TSemicolon:
            return data.CFGClass(name.value, None, main, external=True)
        elif delimitertype is t.TBraceOpen:
            return data.CFGClass(name.value, None, main)

        parentname = self.parse_identifier()
        if not parentname:
            raise data.CFG_Error("Could not parse class parent name of (%s) in (%s)" % (name, main.get_path()))

        parent = data.CFGClass.resolve_parent(main, parentname.value)
        if not parent:
            raise data.CFG_Error("Could not resolve class parent (%s) of (%s) in (%s)" % (parentname, name, main.get_path()))

        end = self.read_token()
        if not end or type(end) is not t.TBraceOpen:
            raise data.CFG_Error("Unexpected token (%s) in class header in (%s)" % (end, main.get_path()))

        return data.CFGClass(name.value, parent, main)

    def parse_class(self, main=None):
        new = self.parse_class_header(main)
        if new.external:
            return new

        clses = set()
        props = set()
        newclass = None
        newprop = None

        peeked = self.peek_token()
        peekedtype = None
        while peeked and type(peeked) is not t.TBraceClose:
            peekedtype = type(peeked)
            if peekedtype is t.TDel:
                raise data.CFG_Error("Class deletion syntax is not supported in (%s)" % (new.get_path()))
            elif peekedtype is t.TEnum:
                raise data.CFG_Error("Enum syntax is not supported in (%s)" % (new.get_path()))
            elif peekedtype is t.TClass:
                newclass = self.parse_class(new)
                if newclass.name in clses:
                    raise data.CFG_Error("Duplicate class definition (%s) in (%s)" % (newclass.name, new.get_path()))
                clses.add(newclass.name)
                new.classes.append(newclass)
            else:
                newprop = self.parse_property(new)
                if newprop.name not in props:
                    props.add(newprop.name)
                    new.properties.append(newprop)

            peeked = self.peek_token()

        end = self.read_token(2)
        if not self.compare_tokens(end, [t.TBraceClose, t.TSemicolon]):
            raise data.CFG_Error("Unexpected class ending (%s) in (%s)" % (", ".join([str(item) for item in end]), new.get_path()))

        return new

    def parse(self):
        if t.TUnknown("") in self.tokens:
            raise data.CFG_Error("Cannot parse unknown tokens")
        if t.THashmark() in self.tokens:
            raise data.CFG_Error("Preprocessor directives are not supported")

        root = self.parse_class()
        return data.CFG(root)
