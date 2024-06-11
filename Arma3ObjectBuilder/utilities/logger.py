# Simple logger class to provide console based feedback
# for I/O and other complex operations.


class ProcessLogger():
    
    def __init__(self, start_indent = 0):
        self.indent = start_indent
        
    def level_up(self, message = ""):
        self.indent += 1
        if message:
            print("\t" * self.indent, message, sep="")
        
    def level_down(self, message = ""):
        self.indent -= 1
        
        if message:
            print("\t" * self.indent, message, sep="")
            
    def step(self, message, time = -1):
        print("\t" * self.indent, message, sep="")
        
        if time > -1:
            print("\t" * (self.indent + 1), "Done in %f sec" % time, sep="")
            
    def log(self, message = ""):
        print("\t" * (self.indent + 1), message, sep="")


class ProcessLoggerNull():
    def __init__(self, start_indent = 0):
        pass

    def level_up(self, message = ""):
        pass

    def level_down(self, message = ""):
        pass

    def step(self, message, time = -1):
        pass

    def log(self, message = ""):
        pass
