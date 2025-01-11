# Processing functions to import a PAA texture file as an image data block.
# The actual file handling is implemented in the data_paa module.


import os
import time

import bpy

from ..paa import data as paa
from ..utilities.logger import ProcessLogger


def import_file(operator, context, file):
    logger = ProcessLogger()
    logger.start_subproc("PAA import from %s" % operator.filepath)

    wm = context.window_manager
    wm.progress_begin(0, 1000)
    wm.progress_update(0)

    tex = paa.PAA_File.read(file)
    alpha = tex.type == paa.PAA_Type.DXT5

    logger.start_subproc("File report:")
    logger.step("Format: %s" % tex.type.name)
    logger.step("Taggs: %d" % len(tex.taggs))
    logger.start_subproc("Mipmaps:")
    for i, mip in enumerate(tex.mips):
        wm.progress_update(i + 1)
        logger.step("%d x %d" % (mip.width, mip.height))

    logger.end_subproc()
    logger.end_subproc()

    if tex.type not in (paa.PAA_Type.DXT1, paa.PAA_Type.DXT5):
        logger.step(">> Unsupported texture format")
        logger.end_subproc()
        logger.step("PAA import terminated")
        return None, tex

    logger.step("Porcessing 1st mipmap")
    mip = tex.mips[0]
    mip.decompress(tex.type)
    swiztagg = tex.get_tagg("SWIZ")
    if swiztagg is not None:
        mip.swizzle(swiztagg.data)

    img = bpy.data.images.new(os.path.basename(operator.filepath), mip.width, mip.height, alpha=alpha, is_data=operator.color_space == 'DATA')
    img.filepath_raw = operator.filepath
    if alpha:
        img.alpha_mode = 'PREMUL'
    img.pixels = [value for c in zip(*mip.data) for value in c]
    img.update()
    img.pack()

    wm.progress_end()
    logger.end_subproc()
    logger.step("PAA import finished in %f sec" % (time.time() - logger.times.pop()))

    return img, tex
