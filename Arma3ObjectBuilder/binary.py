# Wrapper functions to simplify the reading/writing of simple binary data types
# used in the BI file formats, as outlined on the community wiki:
# https://community.bistudio.com/wiki/Generic_FileFormat_Data_Types


import struct
import functools
import itertools
from typing import BinaryIO


def read_byte(file: BinaryIO) -> int:
    return struct.unpack('B', file.read(1))[0]  # type: ignore[no-any-return]


def read_bytes(file: BinaryIO, count: int = 1) -> tuple[int, ...]:
    return struct.unpack('<%dB' % count, file.read(count))


def read_bool(file: BinaryIO) -> bool:
    return read_byte(file) != 0


def read_short(file: BinaryIO) -> int:
    return struct.unpack('<h', file.read(2))[0]  # type: ignore[no-any-return]


def read_shorts(file: BinaryIO, count: int = 1) -> tuple[int, ...]:
    return struct.unpack('<%dh' % count, file.read(2 * count))


def read_ushort(file: BinaryIO) -> int:
    return struct.unpack('<H', file.read(2))[0]  # type: ignore[no-any-return]


def read_ushorts(file: BinaryIO, count: int = 1) -> tuple[int, ...]:
    return struct.unpack('<%dH' % count, file.read(2 * count))


def read_long(file: BinaryIO) -> int:
    return struct.unpack('<i', file.read(4))[0]  # type: ignore[no-any-return]


def read_longs(file: BinaryIO, count: int = 1) -> tuple[int, ...]:
    return struct.unpack('<%di' % count, file.read(4 * count))


def read_ulong(file: BinaryIO) -> int:
    return struct.unpack('<I', file.read(4))[0]  # type: ignore[no-any-return]


def read_ulongs(file: BinaryIO, count: int = 1) -> tuple[int, ...]:
    return struct.unpack('<%dI' % count, file.read(4 * count))


def read_compressed_uint(file: BinaryIO) -> int:
    output = read_byte(file)
    extra = output

    byte_idx = 1
    while extra & 0x80:
        extra = read_byte(file)
        output += (extra - 1) << (byte_idx * 7)
        byte_idx += 1

    return output


def read_half(file: BinaryIO) -> float:
    return struct.unpack('<e', file.read(2))[0]  # type: ignore[no-any-return]


def read_halfs(file: BinaryIO, count: int = 1) -> tuple[float, ...]:
    return struct.unpack('<%de' % count, file.read(2 * count))


def read_float(file: BinaryIO) -> float:
    return struct.unpack('<f', file.read(4))[0]  # type: ignore[no-any-return]


def read_floats(file: BinaryIO, count: int = 1) -> tuple[float, ...]:
    return struct.unpack('<%df' % count, file.read(4 * count))


def read_double(file: BinaryIO) -> float:
    return struct.unpack('<d', file.read(8))[0]  # type: ignore[no-any-return]


def read_doubles(file: BinaryIO, count: int = 1) -> tuple[float, ...]:
    return struct.unpack('<%dd' % count, file.read(8 * count))


def read_char(file: BinaryIO, count: int = 1) -> str:
    chars: bytes = struct.unpack('%ds' % count, file.read(count))[0]
    return chars.decode('ascii')

# In theory all strings in BI files should be strictly ASCII,
# but on the off chance that a corrupt character is present, the method would fail.
# Therefore using UTF-8 decoding is more robust, and gives the same result for valid ASCII values.
# https://stackoverflow.com/a/32775270


def read_asciiz(file: BinaryIO) -> str:
    eof = iter(functools.partial(file.read, 1), "")
    return b"".join(itertools.takewhile(b"\x00".__ne__, eof)).decode('utf8', errors="replace")


def read_asciiz_field(file: BinaryIO, field_len: int) -> str:
    field = file.read(field_len)
    if len(field) < field_len:
        raise EOFError("ASCIIZ field ran into unexpected EOF")

    parts = field.split(b"\x00")
    if len(parts) < 2:
        raise ValueError("ASCIIZ field length overflow")

    return parts[0].decode('utf8', errors="replace")


def read_lascii(file: BinaryIO) -> str:
    length = read_byte(file)
    value = file.read(length)
    if len(value) != length:
        raise EOFError("LASCII string ran into unexpected EOF")

    return value.decode('utf8', errors="replace")


def write_byte(file: BinaryIO, *args: int) -> None:
    file.write(struct.pack('%dB' % len(args), *args))


def write_bool(file: BinaryIO, value: bool) -> None:
    write_byte(file, value)


def write_short(file: BinaryIO, *args: int) -> None:
    file.write(struct.pack('<%dh' % len(args), *args))


def write_ushort(file: BinaryIO, *args: int) -> None:
    file.write(struct.pack('<%dH' % len(args), *args))


def write_long(file: BinaryIO, *args: int) -> None:
    file.write(struct.pack('<%di' % len(args), *args))


def write_ulong(file: BinaryIO, *args: int) -> None:
    file.write(struct.pack('<%dI' % len(args), *args))


def write_compressed_uint(file: BinaryIO, value: int) -> None:
    temp = value
    while True:
        if temp < 128:
            write_byte(file, temp)
            break

        write_byte(file, (temp & 127) + 128)
        temp = temp >> 7


def write_half(file: BinaryIO, *args: float) -> None:
    file.write(struct.pack('<%de' % len(args), *args))


def write_float(file: BinaryIO, *args: float) -> None:
    file.write(struct.pack('<%df' % len(args), *args))


def write_double(file: BinaryIO, *args: float) -> None:
    file.write(struct.pack('<%dd' % len(args), *args))


def write_chars(file: BinaryIO, values: str) -> None:
    file.write(struct.pack('<%ds' % len(values), values.encode('ascii')))


def write_asciiz(file: BinaryIO, value: str) -> None:
    file.write(struct.pack('<%ds' % (len(value) + 1), value.encode('ascii')))


def write_asciiz_field(file: BinaryIO, value: str, field_len: int) -> None:
    if (len(value) + 1) > field_len:
        raise ValueError(
            "ASCIIZ value is longer (%d + 1) than field length (%d)" % (len(value), field_len))

    file.write(struct.pack('<%ds' % field_len, value.encode('ascii')))


def write_lascii(file: BinaryIO, value: str) -> None:
    length = len(value)
    if length > 255:
        raise ValueError("LASCII string cannot be longer than 255 characters")

    file.write(struct.pack('B%ds' % length, length, value.encode('ascii')))
