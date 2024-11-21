class Token:
    pass


class TUnknown(Token):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class TClass(Token):
    def __str__(self):
        return "class"


class TDel(Token):
    def __str__(self):
        return "del"


class TEnum(Token):
    def __str__(self):
        return "enum"


class TParOpen(Token):
    def __str__(self):
        return "("


class TParClose(Token):
    def __str__(self):
        return "("


class TBracketOpen(Token):
    def __str__(self):
        return "["


class TBracketClose(Token):
    def __str__(self):
        return "]"


class TBraceOpen(Token):
    def __str__(self):
        return "{"


class TBraceClose(Token):
    def __str__(self):
        return "}"


class TComma(Token):
    def __str__(self):
        return ","


class TColon(Token):
    def __str__(self):
        return ":"


class TSemicolon(Token):
    def __str__(self):
        return ";"


class TEquals(Token):
    def __str__(self):
        return "="


class TPlus(Token):
    def __init__(self):
        self.value = "+"

    def __str__(self):
        return "+"


class TMinus(Token):
    def __init__(self):
        self.value = "-"

    def __str__(self):
        return "-"


class TPlusEquals(Token):
    def __str__(self):
        return "+="


class TIdentifier(Token):
    def __init__(self, value):
        self.value = value.lower()

    def __str__(self):
        return self.value


class TLiteralString(Token):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "\"%s\"" % self.value


class TLiteralLong(Token):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class TLiteralFloat(Token):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Tokenizer:
    symbols = {
        "(": TParOpen,
        ")": TParClose,
        "[": TBracketOpen,
        "]": TBracketClose,
        "{": TBraceOpen,
        "}": TBraceClose,
        ",": TComma,
        ":": TColon,
        ";": TSemicolon,
        "=": TEquals,
        "+": TPlus,
        "-": TMinus
    }

    kwrds = {
        "class": TClass,
        "del": TDel,
        "enum": TEnum
    }

    def __init__(self, stream):
        self.stream = stream

    def peek_char(self, count=1):
        pos = self.stream.tell()
        chars = self.stream.read(count)
        self.stream.seek(pos)
        return chars

    def read_char(self, count=1):
        return self.stream.read(count)

    def consume_whitespace(self):
        if self.peek_char() not in ("\n", "\t", " "):
            return

        posback = self.stream.tell()
        newchar = self.read_char()
        while newchar in ("\n", "\r", "\t", " "):
            posback = self.stream.tell()
            newchar = self.read_char()

        if newchar != "":
            self.stream.seek(posback)

        return

    def consume_line_comment(self):
        if self.peek_char(2) != "//":
            return

        while self.read_char() not in ("", "\n", "\r"):
            pass

    def consume_block_comment(self):
        if self.peek_char(2) != "/*":
            return

        self.read_char(2)
        newchar = self.read_char()
        while newchar != "":
            if newchar == "*" and self.read_char() == "/":
                return

            newchar = self.read_char()

    def consume_unneeded(self):
        self.consume_whitespace()

        while True:
            newchars = self.peek_char(2)
            if newchars == "//":
                self.consume_line_comment()
            elif newchars == "/*":
                self.consume_block_comment()
            else:
                return

            self.consume_whitespace()

    def next_float_decimal(self, continuefrom=""):
        value = continuefrom
        posback = self.stream.tell()
        newchar = self.read_char()
        found_decimal = "." in value
        while newchar.isdigit() or (newchar == "." and not found_decimal):
            value += newchar
            found_decimal |= newchar == "."
            posback = self.stream.tell()
            newchar = self.read_char()

        if newchar != "":
            self.stream.seek(posback)

        return TLiteralFloat(float(value))

    def next_num(self):
        value = ""
        posback = self.stream.tell()
        newchar = self.read_char()
        while newchar.isdigit():
            value += newchar
            posback = self.stream.tell()
            newchar = self.read_char()

        if newchar == ".":
            return self.next_float_decimal(value + ".")

        if newchar != "":
            self.stream.seek(posback)

        return TLiteralLong(int(value))

    def next_string(self):
        self.read_char()
        value = ""
        newchar = self.read_char()
        while newchar != "" and (newchar != "\"" or self.peek_char() == "\""):
            value += newchar
            if newchar == self.peek_char() == "\"":
                self.read_char()
            newchar = self.read_char()

        return TLiteralString(value)

    def next_identifier(self):
        value = ""
        posback = self.stream.tell()
        newchar = self.read_char()
        while newchar != "" and (newchar.isalnum() or newchar == "_"):
            value += newchar
            posback = self.stream.tell()
            newchar = self.read_char()

        if newchar != "":
            self.stream.seek(posback)

        kwrd = self.kwrds.get(value)
        if kwrd:
            return kwrd()

        return TIdentifier(value)

    def next(self):
        if self.peek_char() == "":
            return None

        self.consume_unneeded()

        if self.peek_char() == "":
            return None

        posback = self.stream.tell()
        nextchar = self.read_char()
        syntaxtoken = self.symbols.get(nextchar)
        if syntaxtoken:
            return syntaxtoken()
        elif nextchar == "+" and self.read_char() == "=":
            return TPlusEquals()

        self.stream.seek(posback)

        if nextchar == ".":
            return self.next_float_decimal()
        elif nextchar.isdigit():
            return self.next_num()
        elif nextchar == "\"":
            return self.next_string()
        elif nextchar.isidentifier():
            return self.next_identifier()

        self.read_char()
        return TUnknown(nextchar)

    def all(self):
        tokens = []
        newtoken = self.next()
        while newtoken:
            tokens.append(newtoken)
            newtoken = self.next()

        return tokens


def print_tokens(tokens):
    for item in tokens:
        print(str(type(item)).ljust(50), str(item))


def count_unknown(tokens):
    count = 0

    for item in tokens:
        if type(item) is TUnknown:
            count += 1

    return count