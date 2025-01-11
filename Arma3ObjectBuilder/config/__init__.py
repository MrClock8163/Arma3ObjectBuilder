# Overall handling module for config related data. Providing
# internal data structures, and IO operations.


from . import data
from . import tokenizer
from . import parser
from . import derapifier


def tokenize(file):
    return tokenizer.CFGTokenizer(file).all()


def tokenize_file(path):
    with open(path, "rt", encoding="utf8") as file:
        return tokenize(file)


def wrap(tokens, wrapper):
    if wrapper == "":
        raise ValueError("Cannot add wrapper tokens with empty class name")

    wrapped = [tokenizer.TClass(), tokenizer.TIdentifier(wrapper), tokenizer.TBraceOpen()]
    wrapped.extend(tokens)
    wrapped.extend([tokenizer.TBraceClose(), tokenizer.TSemicolon()])
    return wrapped


def parse(tokens):
    return parser.CFGParser(tokens).parse()


def from_dict(structure):
    return data.CFG.from_dict(structure)


def derapify(file):
    return derapifier.Derapifier.read(file)


def derapify_file(path):
    return derapifier.Derapifier.read_file(path)


def print_tokens(tokens):
    tokenizer.print_tokens(tokens)
