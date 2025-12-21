# Overall handling module for config related data. Providing
# internal data structures, and IO operations.
from typing import TextIO
from io import BufferedReader

from . import data
from . import tokenizer
from . import parser
from . import derapifier


def tokenize(file: TextIO) -> list[tokenizer.Token]:
    return tokenizer.CFGTokenizer(file).all()


def tokenize_file(path: str) -> list[tokenizer.Token]:
    with open(path, "rt", encoding="utf8") as file:
        return tokenize(file)


def wrap(tokens: list[tokenizer.Token], wrapper: str) -> list[tokenizer.Token]:
    if wrapper == "":
        raise ValueError("Cannot add wrapper tokens with empty class name")

    wrapped = [tokenizer.TClass(), tokenizer.TIdentifier(wrapper), tokenizer.TBraceOpen()]
    wrapped.extend(tokens)
    wrapped.extend([tokenizer.TBraceClose(), tokenizer.TSemicolon()])
    return wrapped


def parse(tokens: list[tokenizer.Token]) -> data.CFG:
    return parser.CFGParser(tokens).parse()


def from_dict(structure: dict[str, data.CFGClassDict]) -> data.CFG:
    return data.CFG.from_dict(structure)


def derapify(file: BufferedReader) -> data.CFG:
    return derapifier.Derapifier.read(file)


def derapify_file(path: str) -> data.CFG:
    return derapifier.Derapifier.read_file(path)


def print_tokens(tokens: list[tokenizer.Token]) -> None:
    tokenizer.print_tokens(tokens)
