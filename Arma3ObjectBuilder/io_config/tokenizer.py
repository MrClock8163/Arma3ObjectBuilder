# Tokenizer classes and function implementation for reading files
# using the standard config syntax (config.cpp, model.cfg, *.rvmat)
from typing import Any, TextIO
from collections.abc import Callable


class Token:
    pass


class TUnknown(Token):
    def __init__(self, value: str) -> None:
        self.value: str = value

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self))


class TClass(Token):
    def __str__(self) -> str:
        return "class"

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self))


class TDel(Token):
    def __str__(self) -> str:
        return "del"

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self))


class TEnum(Token):
    def __str__(self) -> str:
        return "enum"

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self))


class TParOpen(Token):
    def __str__(self) -> str:
        return "("

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self))


class TParClose(Token):
    def __str__(self) -> str:
        return "("

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self))


class TBracketOpen(Token):
    def __str__(self) -> str:
        return "["

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self))


class TBracketClose(Token):
    def __str__(self) -> str:
        return "]"

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self))


class TBraceOpen(Token):
    def __str__(self) -> str:
        return "{"

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self))


class TBraceClose(Token):
    def __str__(self) -> str:
        return "}"

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self))


class TComma(Token):
    def __str__(self) -> str:
        return ","

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self))


class TColon(Token):
    def __str__(self) -> str:
        return ":"

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self))


class TSemicolon(Token):
    def __str__(self) -> str:
        return ";"

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self))


class TEquals(Token):
    def __str__(self) -> str:
        return "="

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self))


class TPlus(Token):
    def __init__(self) -> None:
        self.value: str = "+"

    def __str__(self) -> str:
        return "+"

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self))


class TMinus(Token):
    def __init__(self) -> None:
        self.value = "-"

    def __str__(self) -> str:
        return "-"

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self))


class THashmark(Token):
    def __init__(self) -> None:
        self.value = "#"

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self))


class TIdentifier(Token):
    def __init__(self, value: str) -> None:
        self.value: str = value

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self)) and self.value == other.value


class TLiteralString(Token):
    def __init__(self, value: str) -> None:
        self.value: str = value

    def __str__(self) -> str:
        return "\"%s\"" % self.value

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self)) and self.value == other.value


class TLiteralLong(Token):
    def __init__(self, value: int) -> None:
        self.value: int = value

    def __str__(self) -> str:
        return str(self.value)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self)) and self.value == other.value


class TLiteralFloat(Token):
    def __init__(self, value: float) -> None:
        self.value: float = value

    def __str__(self) -> str:
        return str(self.value)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self)) and self.value == other.value


class CFGTokenizer:
    symbols: dict[str, type[Token]] = {
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
        "-": TMinus,
        "#": THashmark
    }

    kwrds: dict[str, type[TClass] | type[TDel] | type[TEnum]] = {
        "class": TClass,
        "del": TDel,
        "enum": TEnum
    }

    def __init__(self, stream: TextIO) -> None:
        self.stream: TextIO = stream

    def peek_char(self, count: int = 1) -> str:
        pos = self.stream.tell()
        chars = self.stream.read(count)
        self.stream.seek(pos)
        return chars

    def read_char(self, count: int = 1) -> str:
        return self.stream.read(count)

    def consume_whitespace(self) -> None:
        if self.peek_char() not in ("\n", "\t", " "):
            return

        posback = self.stream.tell()
        newchar = self.read_char()
        while newchar in ("\n", "\r", "\t", " "):
            posback = self.stream.tell()
            newchar = self.read_char()

        if newchar != "":
            self.stream.seek(posback)

    def consume_line_comment(self) -> None:
        if self.peek_char(2) != "//":
            return

        while self.read_char() not in ("", "\n", "\r"):
            pass

    def consume_block_comment(self) -> None:
        if self.peek_char(2) != "/*":
            return

        self.read_char(2)
        newchar = self.read_char()
        while newchar != "":
            if newchar == "*" and self.read_char() == "/":
                return

            newchar = self.read_char()

    def consume_unneeded(self) -> None:
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

    def read_sequence(self, func: Callable[[str], bool]) -> str:
        value = ""
        posback = self.stream.tell()
        newchar = self.read_char()
        while func(newchar):
            value += newchar
            posback = self.stream.tell()
            newchar = self.read_char()

        if newchar != "":
            self.stream.seek(posback)

        return value

    def continue_num_exponential(self, value: str = "") -> TLiteralFloat:
        self.read_char()
        value += "e"
        newchar = self.peek_char()
        if newchar in ("+", "-"):
            value += newchar
            self.read_char()

        value += self.read_sequence(str.isdigit)

        return TLiteralFloat(float(value))

    def continue_num_decimal(self, value: str = "") -> TLiteralFloat:
        value += self.read_char()
        value += self.read_sequence(str.isdigit)

        if self.peek_char() in ("e", "E", "d", "D"):
            return self.continue_num_exponential(value)

        return TLiteralFloat(float(value))

    def continue_num_hex(self) -> TLiteralLong:
        self.read_char()
        return TLiteralLong(int(self.read_sequence(str.isdigit), 16))

    def next_num(self) -> TLiteralLong | TLiteralFloat:
        value = self.read_char()
        if self.peek_char() in ("x", "X"):
            return self.continue_num_hex()

        value += self.read_sequence(str.isdigit)

        peeked = self.peek_char()
        if peeked == ".":
            return self.continue_num_decimal(value)
        elif peeked in ("d", "D", "e", "E"):
            return self.continue_num_exponential(value)

        return TLiteralLong(int(value))

    def next_string(self) -> TLiteralString:
        self.read_char()
        value = ""
        newchar = self.read_char()
        while newchar != "" and (newchar != "\"" or self.peek_char() == "\""):
            value += newchar
            if newchar == self.peek_char() == "\"":
                self.read_char()
            newchar = self.read_char()

        return TLiteralString(value)

    def next_identifier(self) -> TIdentifier | TClass | TDel | TEnum:
        value = self.read_sequence(lambda c: c != "" and (c.isalnum() or c == "_"))
        kwrd = self.kwrds.get(value)
        if kwrd:
            return kwrd()

        return TIdentifier(value)

    def next(self) -> Token | None:
        self.consume_unneeded()

        if self.peek_char() == "":
            return None

        posback = self.stream.tell()
        nextchar = self.read_char()
        syntaxtoken = self.symbols.get(nextchar)
        if syntaxtoken:
            return syntaxtoken()

        self.stream.seek(posback)

        if nextchar == ".":
            return self.continue_num_decimal()
        elif nextchar.isdigit():
            return self.next_num()
        elif nextchar == "\"":
            return self.next_string()
        elif nextchar.isidentifier():
            return self.next_identifier()

        self.read_char()
        return TUnknown(nextchar)

    def all(self) -> list[Token]:
        tokens: list[Token] = []
        newtoken = self.next()
        while newtoken:
            tokens.append(newtoken)
            newtoken = self.next()

        return tokens


def print_tokens(tokens: list[Token]) -> None:
    for item in tokens:
        print(str(type(item)).ljust(50), str(item))


def count_unknown(tokens: list[Token]) -> int:
    count = 0

    for item in tokens:
        if type(item) is TUnknown:
            count += 1

    return count
