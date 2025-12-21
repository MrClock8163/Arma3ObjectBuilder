# Processing functions to import a PAA texture file as an image data block.
# The actual file handling is implemented in the data_paa module.


import os
import time
from typing import BinaryIO

import bpy

from ..io_paa import data as paa
from ..logger import ProcessLogger


def import_file(
    operator: bpy.types.Operator,
    context: bpy.types.Context,
    file: BinaryIO
) -> tuple[bpy.types.Image | None, paa.PAA_File]:
    logger = ProcessLogger()
    logger.start_subproc("PAA import from %s" % operator.filepath)  # type: ignore[attr-defined]

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

    logger.step("Processing 1st mipmap")
    mip = tex.mips[0]
    mip.decompress(tex.type)
    swiztagg = tex.get_tagg("SWIZ")
    if swiztagg is not None and swiztagg.data is not None:
        mip.swizzle(swiztagg.data)

    img = bpy.data.images.new(
        os.path.basename(
            operator.filepath  # type: ignore[attr-defined]
        ),
        mip.width,
        mip.height,
        alpha=alpha,
        is_data=operator.color_space == 'DATA'  # type: ignore[attr-defined]
    )
    img.filepath_raw = operator.filepath  # type: ignore[attr-defined]
    if alpha:
        img.alpha_mode = 'PREMUL'

    assert mip.data is not None
    # img.pixels has incorrect type annotation in stub (`float` instead of `list[float]`)
    img.pixels = [
        value
        for c in zip(mip.data[0], mip.data[1], mip.data[2], mip.data[3])
        for value in c
    ]  # type: ignore[assignment]
    img.update()
    img.pack()

    wm.progress_end()
    logger.end_subproc()
    logger.step("PAA import finished in %f sec" % (time.time() - logger.times.pop()))

    return img, tex
