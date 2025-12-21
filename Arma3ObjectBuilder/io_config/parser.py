# Parser implementation for reading files using the standard config syntax.


from . import tokenizer as t
from . import data


class CFGParser:
    def __init__(self, tokens: list[t.Token]) -> None:
        self.ptr: int = 0
        self.tokens: list[t.Token] = tokens

    def read_single_token(self) -> t.Token | None:
        if self.ptr >= len(self.tokens):
            return None

        result = self.tokens[self.ptr]
        self.ptr += 1
        return result

    def read_tokens(self, count: int) -> list[t.Token]:
        if self.ptr >= len(self.tokens):
            return []

        tokens = self.tokens[self.ptr:self.ptr + count]
        self.ptr += len(tokens)
        return tokens

    def peek_single_token(self) -> t.Token | None:
        if self.ptr >= len(self.tokens):
            return None

        return self.tokens[self.ptr]

    def peek_tokens(self, count: int) -> list[t.Token]:
        if self.ptr >= len(self.tokens):
            return []

        return self.tokens[self.ptr:self.ptr + count]

    def seek_token(self, offset: int, ref: int) -> None:
        token_count = len(self.tokens)
        if ref == 2:
            offset += token_count - 1
        elif ref == 1:
            offset += self.ptr

        if not (0 <= offset < token_count):
            raise ValueError("Offset (%d) out of range (0 - %d)" % (offset, token_count - 1))

        self.ptr = offset

    @staticmethod
    def compare_tokens(got: list[t.Token], expected: list[type[t.Token]]) -> bool:
        for token, exp in zip(got, expected):
            if exp is not None and type(token) is not exp:
                return False

        return True

    def parse_identifier(self) -> t.TIdentifier | None:
        value = ""
        nexttoken = self.peek_single_token()
        while nexttoken and isinstance(nexttoken, (t.TIdentifier, t.TLiteralLong)):
            value += str(nexttoken.value)
            self.read_single_token()
            nexttoken = self.peek_single_token()

        if value == "":
            return None

        return t.TIdentifier(value)

    def recover_literal(self) -> t.TLiteralString:
        values: list[t.TIdentifier | t.TLiteralLong | t.TLiteralFloat | t.TLiteralString] = []
        nexttoken = self.peek_single_token()
        while nexttoken and isinstance(nexttoken, (t.TIdentifier, t.TLiteralLong, t.TLiteralFloat, t.TLiteralString)):
            values.append(nexttoken)
            self.read_single_token()
            nexttoken = self.peek_single_token()

        return t.TLiteralString(
            " ".join(
                [
                    ("\"\"%s\"\"" % token.value) if type(token) is t.TLiteralString else str(token.value)
                    for token in values
                ]
            )
        )

    def parse_literal(self) -> data.CFGString | data.CFGInt | data.CFGFloat:
        items: list[t.Token] = []
        nexttoken = self.peek_single_token()
        while (
            nexttoken
            and not isinstance(nexttoken, (t.TComma, t.TSemicolon, t.TBraceClose))
        ):
            items.append(nexttoken)
            self.read_single_token()
            nexttoken = self.peek_single_token()

        match items:
            case []:
                return data.CFGString("")
            case [t.TLiteralString() as token]:
                return data.CFGString(token.value)
            case [t.TLiteralLong() as token]:
                return data.CFGInt(token.value)
            case [t.TLiteralFloat() as token]:
                return data.CFGFloat(token.value)
            case [token]:
                return data.CFGString(str(token))
            case [t.TPlus() | t.TMinus() as signtoken, t.TLiteralLong() as token]:
                sign = 1 if isinstance(signtoken, t.TPlus) else -1
                return data.CFGInt(token.value * sign)
            case [t.TPlus() | t.TMinus() as signtoken, t.TLiteralFloat() as token]:
                sign = 1 if isinstance(signtoken, t.TPlus) else -1
                return data.CFGFloat(token.value * sign)

        return data.CFGString(
            " ".join([("\"%s\"" % token) if isinstance(token, t.TLiteralString) else str(token) for token in items])
        )

    def parse_array(self, main: data.CFGClass, propname: t.TIdentifier) -> data.CFGArray:
        if not isinstance(self.read_single_token(), t.TBraceOpen):
            raise data.CFG_Error(
                "Unexpected token at array start of property (%s) in (%s)" % (
                    propname,
                    main.get_path()
                )
            )

        nexttoken = self.peek_single_token()
        if nexttoken and isinstance(nexttoken, t.TBraceClose):
            self.read_single_token()
            return data.CFGArray([])

        members: list[data.CFGValue] = []
        while nexttoken and type(nexttoken) is not t.TBraceClose:
            if isinstance(nexttoken, t.TBraceOpen):
                members.append(self.parse_array(main, propname))
            else:
                members.append(self.parse_literal())

            nexttoken = self.peek_single_token()
            if type(nexttoken) is t.TComma:
                self.read_single_token()
                nexttoken = self.peek_single_token()

        self.read_single_token()

        return data.CFGArray(members)

    def parse_property(self, main: data.CFGClass) -> data.CFGProperty:
        name = self.parse_identifier()
        if not name:
            raise data.CFG_Error("Could not parse property name in (%s)" % (main.get_path()))

        if isinstance(self.peek_single_token(), t.TEquals):
            self.read_single_token()
            literalvalue = self.parse_literal()
            end = self.read_single_token()
            if not end or not isinstance(end, t.TSemicolon):
                raise data.CFG_Error(
                    "Expected semicolon instead of (%s) after assignment of property (%s) in (%s)" % (
                        end,
                        name,
                        main.get_path()
                    )
                )

            return data.CFGProperty(name.value, literalvalue)

        elif self.compare_tokens(self.peek_tokens(2), [t.TBracketOpen, t.TBracketClose]):
            self.read_tokens(2)
            operator = self.read_single_token()
            extends = False
            if (
                not operator
                or not isinstance(operator, (t.TEquals, t.TPlus))
                or isinstance(operator, t.TPlus) and not isinstance(self.peek_single_token(), t.TEquals)
            ):
                raise data.CFG_Error(
                    "Unexpected array assignment operator (%s) for property (%s) in (%s)" % (
                        operator,
                        name,
                        main.get_path()
                    )
                )

            if isinstance(operator, t.TPlus):
                self.read_single_token()
                extends = True

            array = self.parse_array(main, name)
            array.extends = extends

            end = self.read_single_token()
            if not end or not isinstance(end, t.TSemicolon):
                raise data.CFG_Error(
                    "Expected semicolon instead of (%s) after assignment of property (%s) in (%s)" % (
                        end,
                        name,
                        main.get_path()
                    )
                )

            return data.CFGProperty(name.value, array)

        raise data.CFG_Error(
            "Could not parse property (%s) in (%s)" % (name, main.get_path())
        )

    def parse_class_header(self, main: data.CFGClass | None = None) -> data.CFGClass:
        path = main.get_path() if main else ""
        self.read_single_token()  # skip class keyword
        name = self.parse_identifier()
        if not name:
            raise data.CFG_Error("Could not parse class name in (%s)" % path)

        delimiter = self.read_single_token()
        delimitertype = type(delimiter)
        if delimitertype not in (t.TColon, t.TSemicolon, t.TBraceOpen):
            raise data.CFG_Error(
                "Unexpected token (%s) after class name (%s) in (%s)" % (
                    delimiter,
                    name,
                    path
                )
            )

        if delimitertype is t.TSemicolon:
            return data.CFGClass(name.value, None, main, external=True)
        elif delimitertype is t.TBraceOpen:
            return data.CFGClass(name.value, None, main)

        parentname = self.parse_identifier()
        if not parentname:
            raise data.CFG_Error("Could not parse class parent name of (%s) in (%s)" % (name, path))

        parent = data.CFGClass.resolve_parent(main, parentname.value)
        if not parent:
            raise data.CFG_Error(
                "Could not resolve class parent (%s) of (%s) in (%s)" % (
                    parentname,
                    name,
                    path
                )
            )

        end = self.read_single_token()
        if not end or not isinstance(end, t.TBraceOpen):
            raise data.CFG_Error("Unexpected token (%s) in class header in (%s)" % (end, path))

        return data.CFGClass(name.value, parent, main)

    def parse_class(self, main: data.CFGClass | None = None) -> data.CFGClass:
        new = self.parse_class_header(main)
        if new.external:
            return new

        clses: set[str] = set()
        props: set[str] = set()
        newclass: data.CFGClass | None = None
        newprop: data.CFGProperty | None = None

        peeked = self.peek_single_token()
        while peeked and not isinstance(peeked, t.TBraceClose):
            match peeked:
                case t.TDel():
                    raise data.CFG_Error("Class deletion syntax is not supported in (%s)" % (new.get_path()))
                case t.TEnum():
                    raise data.CFG_Error("Enum syntax is not supported in (%s)" % (new.get_path()))
                case t.TClass():
                    newclass = self.parse_class(new)
                    if newclass.name in clses:
                        raise data.CFG_Error("Duplicate class definition (%s) in (%s)" %
                                             (newclass.name, new.get_path()))
                    clses.add(newclass.name)
                    new.classes.append(newclass)
                case _:
                    newprop = self.parse_property(new)
                    if newprop.name not in props:
                        props.add(newprop.name)
                        new.properties.append(newprop)

            peeked = self.peek_single_token()

        end = self.read_tokens(2)
        if not self.compare_tokens(end, [t.TBraceClose, t.TSemicolon]):
            raise data.CFG_Error("Unexpected class ending (%s) in (%s)" %
                                 (", ".join([str(item) for item in end]), new.get_path()))

        return new

    def parse(self) -> data.CFG:
        if t.TUnknown("") in self.tokens:
            raise data.CFG_Error("Cannot parse unknown tokens")
        if t.THashmark() in self.tokens:
            raise data.CFG_Error("Preprocessor directives are not supported")

        root = self.parse_class()
        return data.CFG(root)
