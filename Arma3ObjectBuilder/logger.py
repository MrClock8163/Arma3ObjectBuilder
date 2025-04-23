# Simple logger class to provide console based feedback
# for I/O and other complex operations.


from time import time


class ProcessLogger:
    def __init__(self, depth = 0):
        self.times = [time()]
        self.depth = depth

    def start_subproc(self, message = ""):
        if message:
            self.step(message)
        
        self.depth += 1
        self.times.append(time())
    
    def end_subproc(self, showtime = False):
        endtime = self.times.pop()
        if showtime:
            self.step(">> Done in %.3f sec" % (time() - endtime))

        self.depth -= 1

    def step(self, message):
        print("\t"*self.depth, message, sep="")


class ProcessLoggerNull():
    def __init__(self, depth = 0):
        pass

    def start_subproc(self, message = ""):
        pass

    def end_subproc(self, showtime = False):
        pass

    def step(self, message):
        pass
