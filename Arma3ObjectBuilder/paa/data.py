# Class structure, read-write methods and conversion functions for handling
# the PAA binary data structure. Format specifications
# can be found on the community wiki (although not without errors):
# https://community.bistudio.com/wiki/PAA_File_Format


import struct
from enum import IntEnum
from io import BytesIO, BufferedReader
from copy import deepcopy

from .. import binary
from ..compression import dxt1_decompress, dxt5_decompress, lzo1x_decompress


class PAA_Error(Exception):
    def __str__(self):
        return "PAA - %s" % super().__str__()


class PAA_Type(IntEnum):
    UNKNOWN = -1
    DXT1 = 0xff01
    DXT2 = 0xff02
    DXT3 = 0xff03
    DXT4 = 0xff04
    DXT5 = 0xff05
    RGBA4 = 0x4444
    RGBA5 = 0x1555
    RGBA8 = 0x8888
    GRAY = 0x8080


class PAA_TAGG():
    def __init__(self):
        self.name = ""
        self.data = None
    
    @classmethod
    def read(cls, file):
        output = cls()

        output.name = file.read(4).decode("utf8")[::-1]
        length = binary.read_ulong(file)
        output.data = file.read(length)

        return output


class PAA_MIPMAP():
    def __init__(self):
        self.width = 0
        self.height = 0
        self.data = None
        self.data_raw = None
        self.lzo_compressed = False
    
    @classmethod
    def read(cls, file):
        output = cls()

        output.width, output.height = binary.read_ushorts(file, 2)
        if output.width == output.height == 0:
            return output
        
        if output.width & 0x8000:
            output.lzo_compressed = True
            output.width ^= 0x8000

        length = struct.unpack('<I', file.read(3) + b"\x00")[0]
        output.data_raw = bytearray(file.read(length))

        return output
    
    def decompress(self, format):
        if format == PAA_Type.DXT1:
            decompressor = dxt1_decompress
            lzo_expected = self.width * self.height // 2
        elif format == PAA_Type.DXT5:
            decompressor = dxt5_decompress
            lzo_expected = self.width * self.height
        else:
            raise PAA_Error("Unsupported format for decompression: %s", format)
        
        data = self.data_raw
        if self.lzo_compressed:
            stream_lzo = BytesIO(self.data_raw)
            reader_lzo = BufferedReader(stream_lzo)
            _, data = lzo1x_decompress(reader_lzo, lzo_expected)

        stream_dxt = BytesIO(data)
        reader_dxt = BufferedReader(stream_dxt)
        self.data = decompressor(reader_dxt, self.width, self.height)

    def swizzle(self, code):
        if self.data is None or len(self.data) != 4:
            raise PAA_Error("No properly decompressed data found to swizzle")
        
        if len(code) != 4:
            raise PAA_Error("Unexpected swizzle code length: %s", code)

        r, g, b, a = self.data
        trg = [a, r, g, b]
        src = deepcopy(trg)

        for op, source, target_idx in zip(code, src, [0, 1, 2, 3]):
            if op == target_idx:
                continue

            target = trg[op & 0b00000011]
            if op & 0b00001000:
                for i in range(len(target)):
                    target[i] = 1
            elif op & 0b00000100:
                for i in range(len(target)):
                    target[i] = 1 - source[i]


class PAA_File():
    def __init__(self):
        self.source = ""
        self.type = PAA_Type.UNKNOWN
        self.taggs = []
        self.mips = []
        self.alpha = False

    @classmethod
    def read(cls, file):
        output = cls()

        data_type = binary.read_ushort(file)
        try:
            output.type = PAA_Type(data_type)
            if output.type == PAA_Type.UNKNOWN:
                raise  Exception()
        except Exception as e:
            raise PAA_Error("Unknown format type: %d" % data_type)

        while True:
            if file.read(4) != b"GGAT":
                file.seek(-4, 1)
                break
            
            output.taggs.append(PAA_TAGG.read(file))

        if binary.read_ushort(file) != 0:
            raise PAA_Error("Indexed palettes are not supported")
        
        while True:
            mip = PAA_MIPMAP.read(file)
            if mip.width == mip.height == 0:
                break

            output.mips.append(mip)
        
        eof = binary.read_ushort(file)
        if eof != 0:
            raise PAA_Error("Unexpected EOF value: %d" % eof)
        
        return output
    
    @classmethod
    def read_file(cls, filepath):
        output = None
        with open(filepath, "rb") as file:
            output = cls.read(file)

        output.source = filepath

        return output
    
    def get_tagg(self, name):
        for tagg in self.taggs:
            if tagg.name == name:
                return tagg
        
        return None
