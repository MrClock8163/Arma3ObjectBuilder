# Simple logger class to provide console based feedback
# for I/O and other complex operations.


from time import time


class ProcessLogger:
    def __init__(self, depth: int = 0) -> None:
        self.times = [time()]
        self.depth = depth

    def start_subproc(self, message: str = "") -> None:
        if message:
            self.step(message)

        self.depth += 1
        self.times.append(time())

    def end_subproc(self, showtime: bool = False) -> None:
        endtime = self.times.pop()
        if showtime:
            self.step(">> Done in %.3f sec" % (time() - endtime))

        self.depth -= 1

    def step(self, message: str) -> None:
        print("\t" * self.depth, message, sep="")


class ProcessLoggerNull(ProcessLogger):
    def __init__(self, depth: int = 0) -> None:
        pass

    def start_subproc(self, message: str = "") -> None:
        pass

    def end_subproc(self, showtime: bool = False) -> None:
        pass

    def step(self, message: str) -> None:
        pass
