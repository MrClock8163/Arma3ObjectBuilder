import struct
    
def read_byte(file):
    return struct.unpack('B',file.read(1))[0]
    
def read_bytes(file,count = 1):
    return [read_byte(file) for i in range(count)]

def read_bool(file):
    return read_byte(file) != 0
    
def read_short(file):
    return struct.unpack('<h',file.read(2))[0]
    
def read_ushort(file):
    return struct.unpack('<H',file.read(2))[0]

def read_long(file):
    return struct.unpack('<i',file.read(4))[0]

def read_ulong(file):
    return struct.unpack('<I',file.read(4))[0]
    
def read_float(file):
    return struct.unpack('<f',file.read(4))[0]
    
def read_double(file):
    return struct.unpack('<d',file.read(8))[0]
    
def read_char(file,count = 1):
    chars = struct.unpack(f'{count}s',file.read(count))[0]
    return chars.decode('utf-8')
    
def read_asciiz(file):
    res = b''
    
    while True:
        a = file.read(1)
        if a == b'\000':
            break
            
        res += a
    
    return res.decode("utf-8")
    
def write_byte(file,value):
    file.write(struct.pack('B',value))
    
def write_bytes(file,values):
    file.write(struct.pack('%dB' % len(values),*values))
    
def write_bool(file,value):
    write_byte(file,value)
    
def write_short(file,value):
    file.write(struct.pack('<h',value))
    
def write_ushort(file,value):
    file.write(struct.pack('<H',value))
    
def write_long(file,value):
    file.write(struct.pack('<i',value))
    
def write_ulong(file,value):
    file.write(struct.pack('<I',value))
    
def write_float(file,value):
    file.write(struct.pack('<f',value))
    
def write_double(file,value):
    file.write(struct.pack('<d',value))
    
def write_chars(file,values):
    file.write(struct.pack('<%ds' % len(values),values.encode('ASCII')))
    
def write_asciiz(file,value):
    file.write(struct.pack('<%ds' % (len(value)+1),value.encode('ASCII')))