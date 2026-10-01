# Class that contains all default options regarding model settings
class ModelSettings:

    # Default settings
    def __init__(self):
        # Fix the number of new products to the cardinality (True, sum( products introduced) = cardinality, else <= cardinality)
        self.newProductsEqualCardinality = False

        # Max allowed time to calculate
        self.restrictMaxTime = True
        self.maxTime = 3600

        # Use of McCormick Inequalities:
        self.mcCormick = True

        # pldPls Settings:
        self.symmetryValueRandom = False
        self.symmetryConstraint = False
        self.fixedCost = True

        # upperBoundSettings
        self.UBepsilon = 0.01
        self.step1MaxIterations = 2
        self.step2MaxIterations = 2
        self.UBmaxTime = 15

        # Cut settings
        self.useCallback = True
        self.mcCormickIndividual = [False, False, False, True]
        self.useCuts = [False, True, True, True, False]
        self.fixedCardinality = False

        # hybrid heuristic
        self.productsToAdd = 1
        self.productsAddedForNextIteration = 10
        self.hybridMaxTime = 3000
        self.hybridProductsInSet = 100

        # Heuristic GA
        self.stopAfterTime = False
        self.stopAfterIterations =False
        self.stopAfterConvergence = True
        self.maxConvergenceChange = 0.0001 # percentage how much objective needs to change in 100 iterations
        self.maxTimeHeuristic = 60
        self.iterations = 10000
        self.populationSize = 500 # 500 Belloni
        self.nrOfChildsAdded = 200
        self.mutationAttribute = 1/5/10
        self.mutationPrice = 1/5/10
        self.mutateReduceSize = 0.005
        self.mutationProductDefault = 0.05
        self.sizeReduction = 1
        self.tournamentSelectionProbability = 0.8
        self.displayResult = False

        # Heuristic twoStep
        self.productsInSet = 10 # Needs to be adjusted, dependent on instance
        self.heuristicMcCormick = True
        self.twoStepIteration = 1
        self.twoStepRestrictMaxTime = True
        self.twoStepStopAfterTime = False
        self.twoStepStopAfterIterations = True
        self.twoStepMaxTimeSolver = 600

        #In product-line design, the mutation rate is typically set to 1 divided by the number of attributes and the number of new products (see, e.g., Reeves, 2003).
