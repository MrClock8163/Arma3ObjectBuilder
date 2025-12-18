# Class structure, read-write methods and conversion functions for handling
# the ASCII Esri GRID raster format. Format specifications:
# https://en.wikipedia.org/wiki/Esri_grid
from typing import TextIO, Self
from enum import Enum


class ASC_Error(Exception):
    def __str__(self) -> str:
        return "ASC - %s" % super().__str__()


class ASC_Type(Enum):
    RASTER = 0
    GRID = 1


class ASC_File():
    def __init__(self) -> None:
        self.pos: tuple[float, float] = (0, 0)
        self.cellsize: float = 1
        self.nodata: float | None = None
        self.data: list[list[float]] = []
        self.type: ASC_Type = ASC_Type.RASTER

    def assign_props(self, props: dict[str, float]) -> tuple[int, int]:
        nrows = props.get("nrows")
        ncols = props.get("ncols")
        xllcorner = props.get("xllcorner")
        xllcenter = props.get("xllcenter")
        yllcorner = props.get("yllcorner")
        yllcenter = props.get("yllcenter")
        cellsize = props.get("cellsize")
        nodata = props.get("nodata_value")

        if ncols is None:
            raise ASC_Error("Missing column count property")
        if nrows is None:
            raise ASC_Error("Missing row count property")
        if cellsize is None:
            raise ASC_Error("Missing cell size property")
        elif cellsize <= 0:
            raise ASC_Error("Invalid cell size property")

        self.cellsize = cellsize

        if xllcorner is not None and yllcorner is not None:
            self.type = ASC_Type.GRID
            self.pos = (xllcorner, yllcorner)
        elif xllcenter is not None and yllcenter is not None:
            self.type = ASC_Type.RASTER
            self.pos = (xllcenter, yllcenter)
        else:
            raise ASC_Error("Missing valid georeference")

        if nodata is not None:
            self.nodata = nodata

        return int(nrows), int(ncols)

    def assign_data(self, nrows: int, ncols: int, data: list[float]) -> None:
        if len(data) != (nrows * ncols):
            raise ASC_Error("Data length (%d) not matching raster dimensions (%d x %d)" % (len(data), nrows, ncols))

        row = []
        for item in data:
            row.append(item)

            if len(row) == ncols:
                self.data.append(row)
                row = []

    @classmethod
    def read(cls, file: TextIO) -> Self:
        output = cls()

        lines = file.readlines()

        props: dict[str, float] = {}
        data: list[float] = []
        for line in lines:
            values = line.split()
            if len(values) == 2 and values[0][0].isalpha():
                props[values[0].lower()] = float(values[1])
            else:
                data.extend([float(item) for item in values])

        if not len(data) > 0:
            raise ASC_Error("Cannot import raster without data")

        nrows, ncols = output.assign_props(props)
        output.assign_data(nrows, ncols, data)

        return output

    @classmethod
    def read_file(cls, filepath: str) -> Self:
        with open(filepath, "r") as file:
            output = cls.read(file)

        return output

    def write(self, file: TextIO) -> None:
        file.write("nrows %d\n" % len(self.data))
        file.write("ncols %d\n" % len(self.data[0]))
        x, y = self.pos
        if self.type is ASC_Type.RASTER:
            file.write("xllcenter %s\n" % str(x))
            file.write("yllcenter %s\n" % str(y))
        elif self.type is ASC_Type.GRID:
            file.write("xllcorner %s\n" % str(x))
            file.write("yllcorner %s\n" % str(y))
        file.write("cellsize %s\n" % str(self.cellsize))

        if self.nodata is not None:
            file.write("nodata_value %s\n" % str(self.nodata))

        for row in self.data:
            row_string = ["%.4f" % item for item in row]
            file.write(" ".join(row_string) + "\n")

    def write_file(self, filepath: str) -> None:
        with open(filepath, "wt") as file:
            self.write(file)

    def get_dimensions(self) -> tuple[int, int]:
        nrows = len(self.data)
        if nrows == 0:
            return 0, 0

        ncols = len(self.data[0])

        return nrows, ncols
