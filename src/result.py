# A class that holds the result
class Result:

    # Init method
    def __init__(self, solverName: str, objective: float, time: float, numberOfProducts: int):
        self.solverName = solverName
        self.objective = objective
        self.time = time
        self.experimentName = 'single solve'
        self.numberOfProducts = numberOfProducts

    # Compares the result with a benchmark result (like state of the art method)
    def compareToBenchmark(self, objective: float, time: float):
        self.objDiffAbs = objective - self.objective
        self.objDiffRel = (objective - self.objective)/objective
        self.timeDiffAbs = time - self.time
        self.timeDiffRel = (time - self.time)/time

    # Add time spend in callback to result
    def addCallbackTime(self, timeCallAbs: float):
        self.timeCallAbs = timeCallAbs
        self.timeCallRel = timeCallAbs/self.time
        