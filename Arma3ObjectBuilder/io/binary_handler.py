# Wrapper functions to simplify the reading/writing of simple binary data types
# used in the BI file formats, as outlined on the community wiki:
# https://community.bistudio.com/wiki/Generic_FileFormat_Data_Types


import struct


def read_byte(file):
    return struct.unpack('B', file.read(1))[0]
    
def read_bytes(file, count = 1):
    return [read_byte(file) for i in range(count)]

def read_bool(file):
    return read_byte(file) != 0
    
def read_short(file):
    return struct.unpack('<h', file.read(2))[0]

def read_shorts(file, count = 1):
    return struct.unpack('<%dh' % count, file.read(2 * count))
    
def read_ushort(file):
    return struct.unpack('<H', file.read(2))[0]

def read_ushorts(file, count = 1):
    return struct.unpack('<%dH' % count, file.read(2 * count))

def read_long(file):
    return struct.unpack('<i', file.read(4))[0]

def read_longs(file, count = 1):
    return struct.unpack('<%di' % count, file.read(4 * count))

def read_ulong(file):
    return struct.unpack('<I', file.read(4))[0]

def read_ulongs(file, count = 1):
    return struct.unpack('<%dI' % count, file.read(4 * count))

def read_compressed_uint(file):
    output = read_byte(file)
    extra = output
    
    byte_idx = 1
    while extra & 0x80:
        extra = read_byte(file)
        output += (extra - 1) << (byte_idx * 7)
        byte_idx += 1
    
    return output

def read_half(file):
    return struct.unpack('<e', file.read(2))[0]

def read_halfs(file, count = 1):
    return struct.unpack('<%de' % count, file.read(2 * count))
    
def read_float(file):
    return struct.unpack('<f', file.read(4))[0]

def read_floats(file, count = 1):
    return struct.unpack('<%df' % count, file.read(4 * count))
    
def read_double(file):
    return struct.unpack('<d', file.read(8))[0]

def read_doubles(file, count = 1):
    return struct.unpack('<%dd' % count, file.read(8 * count))
    
def read_char(file, count = 1):
    chars = struct.unpack('%ds' % count, file.read(count))[0]
    return chars.decode('ascii')

# In theory all strings in BI files should be strictly ASCII,
# but on the off chance that a corrupt character is present, the method would fail.
# Therefore using UTF-8 decoding is more robust, and gives the same result for valid ASCII values.
def read_asciiz(file):
    res = b''
    
    while True:
        a = file.read(1)
        if a == b'\x00' or a == b'':
            break
            
        res += a
    
    return res.decode('utf8', errors="replace")

def read_asciiz_field(file, field_len):
    field = file.read(field_len)
    if len(field) < field_len:
        raise EOFError("ASCIIZ field ran into unexpected EOF")
    
    result = bytearray()
    for value in field:
        if value == 0:
            break
            
        result.append(value)
    else:
        raise ValueError("ASCIIZ field length overflow")
    
    return result.decode('utf8', errors="replace")
        
def read_lascii(file):
    length = read_byte(file)
    value = file.read(length)
    if len(value) != length:
        raise EOFError("LASCII string ran into unexpected EOF")
    
    return value.decode('utf8', errors="replace")
    
def write_byte(file, *args):
    file.write(struct.pack('%dB' % len(args), *args))
    
def write_bool(file, value):
    write_byte(file, value)
    
def write_short(file, *args):
    file.write(struct.pack('<%dh' % len(args), *args))
    
def write_ushort(file, *args):
    file.write(struct.pack('<%dH' % len(args), *args))
    
def write_long(file, *args):
    file.write(struct.pack('<%di' % len(args), *args))
    
def write_ulong(file, *args):
    file.write(struct.pack('<%dI' % len(args), *args))

def write_compressed_uint(file, value):
    temp = value
    while True:
        if temp < 128:
            write_byte(file, temp)
            break

        write_byte(file, (temp & 127) + 128)
        temp = temp >> 7

def write_half(file, *args):
    file.write(struct.pack('<%de' % len(args), *args))
    
def write_float(file, *args):
    file.write(struct.pack('<%df' % len(args), *args))
    
def write_double(file, *args):
    file.write(struct.pack('<%dd' % len(args), *args))
    
def write_chars(file, values):
    file.write(struct.pack('<%ds' % len(values), values.encode('ascii')))
    
def write_asciiz(file, value):
    file.write(struct.pack('<%ds' % (len(value) + 1), value.encode('ascii')))

def write_asciiz_field(file, value, field_len):
    if (len(value) + 1) > field_len:
        raise ValueError("ASCIIZ value is longer (%d + 1) than field length (%d)" % (len(value), field_len))

    file.write(struct.pack('<%ds' % field_len, value.encode('ascii')))

def write_lascii(file, value):
    length = len(value)
    if length > 255:
        raise ValueError("LASCII string cannot be longer than 255 characters")
    
    file.write(struct.pack('B%ds' % length, length, value.encode('ascii')))
