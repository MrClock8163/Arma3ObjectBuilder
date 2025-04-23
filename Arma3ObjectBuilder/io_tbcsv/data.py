# Class structure and read-write methods for handling the object list format
# used for interoperability with Terrain Builder


class TBCSV_Error(Exception):
    def __str__(self):
        return "TBCSV - %s" % super().__str__()


class TBCSV_Transform:
    def __init__(self, loc = (0, 0, 0), rot = (0, 0, 0), scale = 1):
        self.loc = loc
        self.rot = rot
        self.scale = scale
    
    def print(self):
        east, north, elev = self.loc
        yaw, pitch, roll = self.rot

        return ";".join(["%.8f" % value for value in (east, north, yaw, pitch, roll, self.scale, elev)])


class TBCSV_Object:
    def __init__(self, name = ""):
        self.name = name
        self.transform = TBCSV_Transform()
    
    @classmethod
    def parse(cls, data):
        fields = data.rstrip(";").split(";")
        if len(fields) != 8:
            raise TBCSV_Error("Invalid row, unexpected field count: \"%s\"" % data)
        
        name, east, north, yaw, pitch, roll, scale, elev = fields

        output = cls()
        try:
            output.name = name[1:-1]
            output.transform = TBCSV_Transform((float(east), float(north), float(elev)), (float(yaw), float(pitch), float(roll)), float(scale))
        except Exception as e:
            raise TBCSV_Error(e)

        return output
    
    def print(self):
        return "\"%s\";%s\n" % (self.name, self.transform.print())


class TBCSV_File:
    def __init__(self):
        self.source = ""
        self.objects = []
    
    @classmethod
    def read(cls, file):
        output = cls()

        for line in file:
            if line == "\n":
                continue
            output.objects.append(TBCSV_Object.parse(line.strip()))

        return output
    
    @classmethod
    def read_file(cls, filepath):
        output = None
        with open(filepath, "tr") as  file:
            output = cls.read(file)
        
        output.source = filepath
        
        return output
    
    def write(self, file):
        for obj in self.objects:
            file.write(obj.print())
    
    def write_file(self, filepath):
        with open(filepath, "wt") as file:
            self.write(file)
