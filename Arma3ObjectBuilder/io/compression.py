# Algorithms for handling compressed data blocks in Arma 3 file formats.


import struct
from array import array


class LZO_Error(Exception):
    def __str__(self):
        return "LZO - %s" % super().__str__()


# Decompression algorithm for bit streams compressed with the LZO1X algorithm.
# Implementation is based on the LZO stream format documentation included in the Linux kernel documentations:
# https://docs.kernel.org/staging/lzo.html
# Some inspiration was taken from the C implementation found in the FFMPEG libavutil library:
# https://github.com/FFmpeg/FFmpeg/blob/master/libavutil/lzo.c
# The original LZO implementations as defined by Markus F.X.J. Oberhumer:
# https://www.oberhumer.com/opensource/lzo/
def lzo1x_decompress(file, expected):
    state = 0
    start = file.tell()
    output = bytearray()

    struct_le16 = struct.Struct('<H')

    def check_free_space(length):
        free_space = expected - len(output)
        if free_space < length:
            raise LZO_Error("Output overrun (free buffer: %d, match length: %d)" % (free_space, length))
    
    def copy_match(distance, length):
        check_free_space(length)
        
        # It is valid to have length that is longer than the back pointer distance, which creates a repeating pattern,
        # copying the same bytes that were copied in this same command.
        # For this reason, we cannot simply take a slice of the output at the given point with the given length, as
        # some of the bytes might not yet be there. We have to copy in chunks with size of the backpointer distance.
        start = len(output) - distance
        output.extend(output[start:] * (length // distance)) # copy as many whole chunks as possible
        output.extend(output[start:(start + (length % distance))]) # copy remainder
    
    def get_length(x, mask):
        length = x & mask
        if not length:
            while True:
                x = file.read(1)[0]
                if x:
                    break
                
                length += 255
            length += mask + x
        return length
    
    # # First byte is handled separately, as the output buffer is empty at this point.
    x = file.read(1)[0]
    if x > 17:
        length = x - 17
        check_free_space(length)
        output.extend(file.read(length))
        state = min(4, length)
        x = file.read(1)[0]
    
    while True:
        if x <= 15:
            if not state:
                length = 3 + get_length(x, 15)
                check_free_space(length)
                output.extend(file.read(length))
                state = 4
            elif state < 4:
                length = 2
                state = x & 3
                distance = (file.read(1)[0] << 2) + (x >> 2) + 1
                copy_match(distance, length)
                check_free_space(state)
                output.extend(file.read(state))
            elif state == 4:
                length = 3
                state = x & 3
                distance = (file.read(1)[0] << 2) + (x >> 2) + 2049
                copy_match(distance, length)
                check_free_space(state)
                output.extend(file.read(state))
        elif x > 127:
            state = x & 3
            length = 5 + ((x >> 5) & 3)
            distance = (file.read(1)[0] << 3) + ((x >> 2) & 7) + 1
            copy_match(distance, length)
            check_free_space(state)
            output.extend(file.read(state))
        elif x > 63:
            state = x & 3
            length = 3 + ((x >> 5) & 1)
            distance = (file.read(1)[0] << 3) + ((x >> 2) & 7) + 1
            copy_match(distance, length)
            check_free_space(state)
            output.extend(file.read(state))
        elif x > 31:
            length = 2 + get_length(x, 31)
            extra = struct_le16.unpack(file.read(2))[0]
            distance = (extra >> 2) + 1
            state = extra & 3
            copy_match(distance, length)
            check_free_space(state)
            output.extend(file.read(state))
        else:
            length = 2 + get_length(x, 7)
            extra = struct_le16.unpack(file.read(2))[0]
            distance = 16384 + ((x & 8) << 11) + (extra >> 2)
            state = extra & 3
            if distance == 16384:
                if length != 3:
                    raise LZO_Error("Invalid End Of Stream (expected match length: 3, got: %s)" % length)
                # End of Stream reached
                break
            
            copy_match(distance, length)
            check_free_space(state)
            output.extend(file.read(state))

        x = file.read(1)[0]

    if expected - len(output):
        raise LZO_Error("Stream provided shorter output than expected (expected: %d, got: %d)" % (expected, len(output)))
    
    return file.tell() - start, output


class DXT_Error(Exception):
    def __str__(self):
        return "DXT - %s" % super().__str__()


# Decompression algorithms for textures compressed with the S3TC DXT1 and DXT5 algorithms.
# Implementations are based on the publicly available descriptions of the format:
# https://en.wikipedia.org/wiki/S3_Texture_Compression
# https://www.khronos.org/opengl/wiki/S3_Texture_Compression
def dxt5_decompress(file, width, height):
    if width % 4 != 0 or height % 4 != 0:
        raise DXT_Error("Unexpected resolution: %d x %d" % (width, height))

    red = array('f', bytearray(width * height * 4))
    green = array('f', bytearray(width * height * 4))
    blue = array('f', bytearray(width * height * 4))
    alpha = array('f', bytearray(width * height * 4))
    struct_block_color = struct.Struct('<HHI')
    struct_block_alpha = struct.Struct('BB')

    # Interpolation coefficients
    acoef67 = 6/7
    acoef17 = 1/7
    acoef57 = 5/7
    acoef27 = 2/7
    acoef47 = 4/7
    acoef37 = 3/7

    acoef45 = 4/5
    acoef15 = 1/5
    acoef35 = 3/5
    acoef25 = 2/5

    coef23 = 2/3
    coef13 = 1/3

    block_count_w = width // 4
    block_count_h = height // 4

    # Decompression of blocks from left->right, top->bottom
    for brow in range(block_count_h):
        for bcol in range(block_count_w):
            a0, a1, = struct_block_alpha.unpack(file.read(2))
            atable = struct.unpack('<Q', file.read(6) + b"\x00\x00")[0]
            v0, v1, table = struct_block_color.unpack(file.read(8))

            # Expanding directly stored colors
            r0 = (v0 >> 11) / 31
            g0 = ((v0 >> 5) & 0x3f) / 63
            b0 = (v0 & 0x1f) / 31
            
            r1 = (v1 >> 11) / 31
            g1 = ((v1 >> 5) & 0x3f) / 63
            b1 = (v1 & 0x1f) / 31
            
            # Color interpolation
            if v0 > v1:
                r2 = coef23 * r0 + coef13 * r1
                g2 = coef23 * g0 + coef13 * g1
                b2 = coef23 * b0 + coef13 * b1

                r3 = coef13 * r0 + coef23 * r1
                g3 = coef13 * g0 + coef23 * g1
                b3 = coef13 * b0 + coef23 * b1
            else:
                r2 = 0.5 * (r0 + r1)
                g2 = 0.5 * (g0 + g1)
                b2 = 0.5 * (b0 + b1)
                r3 = g3 = b3 = 0
            
            # Alpha interpolation
            if a0 > a1:
                a0 /= 255
                a1 /= 255
                a2 = acoef67 * a0 + acoef17 * a1
                a3 = acoef57 * a0 + acoef27 * a1
                a4 = acoef47 * a0 + acoef37 * a1
                a5 = acoef37 * a0 + acoef47 * a1
                a6 = acoef27 * a0 + acoef57 * a1
                a7 = acoef17 * a0 + acoef67 * a1
            else:
                a0 /= 255
                a1 /= 255
                a2 = acoef45 * a0 + acoef15 * a1
                a3 = acoef35 * a0 + acoef25 * a1
                a4 = acoef25 * a0 + acoef35 * a1
                a5 = acoef15 * a0 + acoef45 * a1
                a6 = 0
                a7 = 1
            
            # Color code
            codes = (
                table & 0x3,
                table >> 2 & 0x3,
                table >> 4 & 0x3,
                table >> 6 & 0x3,
                table >> 8 & 0x3,
                table >> 10 & 0x3,
                table >> 12 & 0x3,
                table >> 14 & 0x3,
                table >> 16 & 0x3,
                table >> 18 & 0x3,
                table >> 20 & 0x3,
                table >> 22 & 0x3,
                table >> 24 & 0x3,
                table >> 26 & 0x3,
                table >> 28 & 0x3,
                table >> 30 & 0x3
            )
            # Alpha codes
            acodes = (
                atable & 0x7,
                atable >> 3 & 0x7,
                atable >> 6 & 0x7,
                atable >> 9 & 0x7,
                atable >> 12 & 0x7,
                atable >> 15 & 0x7,
                atable >> 18 & 0x7,
                atable >> 21 & 0x7,
                atable >> 24 & 0x7,
                atable >> 27 & 0x7,
                atable >> 30 & 0x7,
                atable >> 33 & 0x7,
                atable >> 36 & 0x7,
                atable >> 39 & 0x7,
                atable >> 42 & 0x7,
                atable >> 45 & 0x7
            )
            # Color lookup
            lut = (
                (r0, g0, b0),
                (r1, g1, b1),
                (r2, g2, b2),
                (r3, g3, b3)
            )
            # Alpha lookup
            alut = (a0, a1, a2, a3, a4, a5, a6, a7)

            # Block interpretation
            bstartrow = brow * 4
            bstartcol = bcol * 4
            for row in range(4):
                for col in range(4):
                    pix = row * 4 + col # pixel index inside current flattened block
                    r, g, b = lut[codes[pix]]
                    a = alut[acodes[pix]]
                    idx = ((bstartrow + row) * width) + bstartcol + col # target index in flattened channel arrays
                    red[idx] = r
                    green[idx] = g
                    blue[idx] = b
                    alpha[idx] = a

    return red, green, blue, alpha


def dxt1_decompress(file, width, height):
    if width % 4 != 0 or height % 4 != 0:
        raise DXT_Error("Unexpected resolution: %d x %d" % (width, height))

    red = array('f', bytearray(width * height * 4))
    green = array('f', bytearray(width * height * 4))
    blue = array('f', bytearray(width * height * 4))
    alpha = array('f', bytearray(width * height * 4))
    struct_block = struct.Struct('<HHI')

    # Interpolation coefficients
    coef0 = 2/3
    coef1 = 1/3
    
    block_count_w = width // 4
    block_count_h = height // 4

    a0 = a1 = a2 = 1

    # Decompression of blocks from left->right, top->bottom
    for brow in range(block_count_h):
        for bcol in range(block_count_w):
            v0, v1, table = struct_block.unpack(file.read(8))

            # Expanding directly stored colors
            r0 = (v0 >> 11) / 31
            g0 = ((v0 >> 5) & 0x3f) / 63
            b0 = (v0 & 0x1f) / 31
            
            r1 = (v1 >> 11) / 31
            g1 = ((v1 >> 5) & 0x3f) / 63
            b1 = (v1 & 0x1f) / 31
            
            # Color interpolation
            if v0 > v1:
                r2 = coef0 * r0 + coef1 * r1
                g2 = coef0 * g0 + coef1 * g1
                b2 = coef0 * b0 + coef1 * b1

                r3 = coef1 * r0 + coef0 * r1
                g3 = coef1 * g0 + coef0 * g1
                b3 = coef1 * b0 + coef0 * b1
                
                a3 = 1
            else:
                r2 = 0.5 * (r0 + r1)
                g2 = 0.5 * (g0 + g1)
                b2 = 0.5 * (b0 + b1)

                r3 = g3 = b3 = a3 = 0
            
            # Color codes
            codes = (
                table & 0x3,
                table >> 2 & 0x3,
                table >> 4 & 0x3,
                table >> 6 & 0x3,
                table >> 8 & 0x3,
                table >> 10 & 0x3,
                table >> 12 & 0x3,
                table >> 14 & 0x3,
                table >> 16 & 0x3,
                table >> 18 & 0x3,
                table >> 20 & 0x3,
                table >> 22 & 0x3,
                table >> 24 & 0x3,
                table >> 26 & 0x3,
                table >> 28 & 0x3,
                table >> 30 & 0x3
            )
            # Color lookup
            lut = (
                (r0, g0, b0, a0),
                (r1, g1, b1, a1),
                (r2, g2, b2, a2),
                (r3, g3, b3, a3)
            )

            # Block interpretation
            bstartrow = brow * 4
            bstartcol = bcol * 4
            for row in range(4):
                for col in range(4):
                    r, g, b, a = lut[codes[row * 4 + col]]
                    idx = ((bstartrow + row) * width) + bstartcol + col # target index in flattened channel arrays
                    red[idx] = r
                    green[idx] = g
                    blue[idx] = b
                    alpha[idx] = a

    return red, green, blue, alpha
