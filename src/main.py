from input import Input

import empiricalData.input_Emp as input_Emp
import exactMethods.bigM as bigM
import exactMethods.conic as conic
import exactMethods.conicCut as conicCut
import exactMethods.mendez_diaz_adopted as mendez_diaz_adopted
import heuristicMethods.GeneticAlgorithmAO as gaAO
import heuristicMethods.GeneticAlgorithmPLD as gaPLD
import heuristicMethods.twoStepHeuristic as twoStep
import numericalExperiment as numericalExperiment
import modelSettings as modelSettings

### Single instance creation and solving
print('Test a random instance')
settings = modelSettings.ModelSettings() 
input = Input().get()

#### Remove comments to update McCormick values
#input.updateYBound()
#input.addFOConditionalYBoundSimple()

# Settings
solverNames = ['conic','conicBC','gaAO']
solver = [conicCut,conicCut,gaAO]
settings = [modelSettings.ModelSettings() for sol in solver]
settings[0].useCallback = False
settings[0].maxTime = 30
settings[1].useCallback = True
settings[1].maxTime = 30
settings[2].stopAfterTime = True
settings[2].maxTimeHeuristic = 30

# Solve
results = []
for id,sol in enumerate(solver):
    results.append(sol.solve(input=input, settings=settings[id]).__dict__)

# Print results
print('\n')
for r in results:
    print(r)


### Test Experiment --> Please remove commend if you want to run the test experiment with sample files
#numericalExperiment.conductExperiment(name = 'test_experiment', attributes= 1, attributeLevels= 1, products = 250, pldStructure = False)




