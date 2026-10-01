import os
import sys
from input import Input

import empiricalData.input_Emp as input_Emp
import exactMethods.bigM as bigM
import exactMethods.conic as conic
import exactMethods.conicCut as conicCut
import exactMethods.mendez_diaz_adopted as mendez_diaz_adopted
import heuristicMethods.GeneticAlgorithmAO as gaAO
import heuristicMethods.GeneticAlgorithmPLD as gaPLD
import heuristicMethods.twoStepHeuristic as twoStep
import heuristicMethods.twoStepHeuristicMILP as twoStepMILP

from modelSettings import ModelSettings
import itertools
from pathlib import Path
from datetime import datetime as dt
from result import Result
import csv
from genericpath import isfile
import ast
import random
import amplpy
import math

# Print start time
print(dt.now())

# Method to solve a single instance in an experiment
def singleSolveEmpirical(solverNr: int, experimentName: str):
    # Original print output
    stdoutOrigin=sys.stdout

    # Folder and path
    dirname = os.path.dirname(__file__)
    path = os.path.join(dirname, 'experiments')
    Path(path).mkdir(parents=True, exist_ok=True)
    path = os.path.join(path, experimentName)

    # Location create folder including input folder
    Path(path).mkdir(parents=True, exist_ok=True)
    inputPath =  os.path.join(path, 'input')
    Path(inputPath).mkdir(parents=True, exist_ok=True)
    inputFolder = os.listdir(inputPath)

    # New log path
    mainLogPath = os.path.join(path, experimentName + '.txt')
    #sys.stdout = open(mainLogPath, "w")
    # Input
    # Write the input = instance that you want to solve

    try:

        # print current file id name
        print(dt.now(),input.name)

        # Solve it with each solver
        sol = solver[solverNr]
        id = solverNr

        # Change log file location
        logPath =  os.path.join(path, solverNames[id])
        Path(logPath).mkdir(parents=True, exist_ok=True)
        logPath = os.path.join(logPath, input.name + str(sol.__name__) + str(id) + '.txt')
        sys.stdout = open(logPath, "w")

        # Print current time and input
        print(dt.now())
        print(input.toStringShort())
        modelSettings = settings[id]
        print(modelSettings.__dict__)

        # Solve
        result = sol.solve(input = input, settings = modelSettings)
        result.solverName = solverNames[id]
        
        print(dt.now(),input.name, sol, result.time)

        # Return to main log path
        #sys.stdout= open(mainLogPath, "w")
        sys.stdout=stdoutOrigin

        # Update result and save it
        result.experimentName = experimentName

        saveResult(result, input.__dict__, modelSettings)
    except Exception as e:
        print(e)
        sys.stdout=stdoutOrigin
        print(e)
        raise

    # Reset log path
    sys.stdout=stdoutOrigin

# Method to solve a single input with different solvers
def singleInputSolve():
    # Input
    input = Input().get()
    # Update weight and yBounds including first order
    input.updateYBound()
    #input.addFOConditionalYBound()

    # Fastest Solver
    modelSettings = ModelSettings()

    modelSettings.mcCormick = True

     # Limit time
    modelSettings.maxTime = 10
    
    print('xxxxxxxx Conic')
    resultConic = conic.solve(input = input, settings = modelSettings)


    # Solve with different solvers
    print('xxxxxxxx Pld Conic')
    pldConic = conic.solve(input = input, settings = modelSettings)
    modelSettings.symmetryValueRandom = False
    pldConic1 = conic.solve(input = input, settings = modelSettings)
    modelSettings.symmetryConstraint = True
    pldConic2 = conic.solve(input = input, settings = modelSettings)
    modelSettings.fixedCost = True
    pldConic3 = conic.solve(input = input, settings = modelSettings)
    print('xxxxxxxx pld big M')
    #pldM = pldPlsBigM.solve(input = input, settings = modelSettings)
    print('xxxxxxxx bigM')
    rbigM = bigM.solve(input = input, settings =  modelSettings)
    #rbigM = Result(objective=0,solverName = '', time = 0)
    pldM= Result(objective=0,solverName = '', time = 0)

    # print result
    print('pldConic, pldM, resultConic, rbigM')
    print(pldConic.time,pldConic1.time,pldConic2.time,resultConic.time,rbigM.time)
    print(pldConic.objective,pldConic1.objective,pldConic2.objective,resultConic.objective,rbigM.objective)

# Method to create input files and store them
def createExperiment(name: str, segmentsList:list, priceLevelsList:list, cardinalityList: list, attributeUtilityRangeList: list, betaRangeList: list, attributes: int, attributeLevels: int, products: int, outsideOptionRangeList:list, costRangeList:list, equalWeight: bool, pldStructure:bool, repetitions: int):
        # Quasi products
    if pldStructure:
        products = attributeLevels ** attributes
    
    # Add the number of products to the name
    experimentName = name +' '+ str(products)

    # Original print output
    stdoutOrigin=sys.stdout
    
    # Folder and path
    dirname = os.path.dirname(__file__)
    path = os.path.join(dirname, 'experiments')
    Path(path).mkdir(parents=True, exist_ok=True)
    path = os.path.join(path, experimentName)

    # Location create folder including input folder
    Path(path).mkdir(parents=True, exist_ok=True)
    inputPath =  os.path.join(path, 'input')
    Path(inputPath).mkdir(parents=True, exist_ok=True)

    # New log path
    mainLogPath = os.path.join(path, experimentName + ' creation.txt')
    sys.stdout = open(mainLogPath, "w")

    # Print starting stats
    print('segmentsList =' , segmentsList,'priceLevelsList =', priceLevelsList,'cardinalityList = ', cardinalityList,'attributeUtilityRangeList =', attributeUtilityRangeList,'betaRangeList = ', betaRangeList, 'outsideOptionRangeList = ', outsideOptionRangeList, 'costRangeList =', costRangeList, 'repetitions = ', repetitions)
    print('Create experiment ' + experimentName, 'with', len(segmentsList) * len(priceLevelsList) * len(cardinalityList) * len(attributeUtilityRangeList) * len(betaRangeList) * len(outsideOptionRangeList) * repetitions, 'repetitions and', str(products), 'products \n')

    # Create one input per combination
    for segments, priceLevels, cardinality, attributeUtilityRange, betaRange, outsideOptionRange, costRange in itertools.product(segmentsList, priceLevelsList, cardinalityList, attributeUtilityRangeList, betaRangeList, outsideOptionRangeList, costRangeList):
        # Print current progress
        print(dt.now(),segments, priceLevels, cardinality, attributeUtilityRange, betaRange, outsideOptionRange, '\n')

        # Repeat for each repetition
        for rep in range(repetitions):
            # Create an input file and add name
            if pldStructure:
                input = Input().getRandomFromPLDStructure(segments, priceLevels, cardinality, attributeUtilityRange, betaRange, attributes, attributeLevels, outsideOptionRange, costRange, equalWeight)
            else:
                input = Input().getRandomExample(segments, products, priceLevels, cardinality, attributeUtilityRange, betaRange, outsideOptionRange, costRange, equalWeight)
            input.repetition = rep
            input.name = str(segments) +' '+ str(priceLevels) +' '+ str(cardinality) +' '+ str(attributeUtilityRange) +' '+ str(betaRange) +' '+ str(outsideOptionRange) + ' ' + str(rep)

            # Update yBounds including first order
            input.updateYBound()
            input.addFOConditionalYBoundSimple()

            # Path and saving
            inputFilePath =  os.path.join(inputPath, input.name + ".txt")
            file = open(inputFilePath, 'w+')
            file.write(str(input.toDict()))
            file.close()

    # Close log path or change it
    sys.stdout=stdoutOrigin
    sys.stdout.close()

# Method to conduct an experiment
def conductExperiment(name: str, attributes: int, attributeLevels: int, products: int, pldStructure: bool):
    # Add the number of products to the name
    if pldStructure: 
        products = attributeLevels ** attributes
    experimentName = name +' '+ str(products)

    # Original print output
    stdoutOrigin=sys.stdout

    # Folder and path
    dirname = os.path.dirname(__file__)
    path = os.path.join(dirname, 'experiments')
    Path(path).mkdir(parents=True, exist_ok=True)
    path = os.path.join(path, experimentName)

    # Location create folder including input folder
    Path(path).mkdir(parents=True, exist_ok=True)
    inputPath =  os.path.join(path, 'input')
    Path(inputPath).mkdir(parents=True, exist_ok=True)
    inputFolder = os.listdir(inputPath)

    # New log path
    mainLogPath = os.path.join(path, experimentName + '.txt')
    #sys.stdout = open(mainLogPath, "w")

    # Each file is one input
    for inpFile in inputFolder:
        try:
            
            # Convert the file to input object
            inputFilePath =  os.path.join(inputPath, inpFile)
            file = open(inputFilePath, 'r')
            inputDict = file.readline()
            inputDict =  ast.literal_eval(inputDict)
            file.close()
            input = Input().__fromDict__(inputDict)

            # print current file id name
            print(dt.now(),input.name)

            # Benchmark result
            benchmarkResult = []
            # Solve it with each solver
            for id,sol in enumerate(solver):
                # Change log file location
                logPath =  os.path.join(path, solverNames[id])
                Path(logPath).mkdir(parents=True, exist_ok=True)
                logPath = os.path.join(logPath, input.name + str(sol.__name__) + str(id) + '.txt')
                sys.stdout = open(logPath, "w")

                # Print current time and input
                print(dt.now())
                print(input.toStringShort())
                modelSettings = settings[id]
                print(modelSettings.__dict__)
                print(input.name, sol)

                # Solve
                result = sol.solve(input = input, settings = modelSettings)
                result.solverName = solverNames[id]
                
                # Benchmark and update if it is solvable in time
                if id == 0:
                    benchmarkResult = result

                result.compareToBenchmark(benchmarkResult.objective, benchmarkResult.time)
                print(dt.now(), result.time)

                # Return to main log path
                #sys.stdout= open(mainLogPath, "w")
                sys.stdout=stdoutOrigin

                # Update result and save it
                result.experimentName = experimentName

                saveResult(result, inputDict, modelSettings)
        except Exception as e:
            print(e)
            sys.stdout=stdoutOrigin
            print(e)
            raise
    # Reset log path
    sys.stdout=stdoutOrigin

# Saves a single result
def saveResult(result: Result, inputDict: str, modelSettings: ModelSettings):
    # Create file path
    dirname = os.path.dirname(__file__)
    path = os.path.join(dirname, 'experiments')
    Path(path).mkdir(parents=True, exist_ok=True)
    path = os.path.join(path, result.experimentName)
    Path(path).mkdir(parents=True, exist_ok=True)

    # Save result file
    resultPath = os.path.join(path, 'results')
    Path(resultPath).mkdir(parents=True, exist_ok=True)
    resultPath = os.path.join(resultPath, str(inputDict['name']) + ' '  + result.solverName + '.txt')
    file = open(resultPath, 'w+')
    file.write(str(result.__dict__))
    file.close()

    # CSV
    # Try to save to csv
    try:
        # Open csv File
        csvFilePath = os.path.join(path, 'allOutputs '+ result.experimentName +'.csv')

        # Test if file exists
        exists = isfile(csvFilePath)

        # Create a file and writer
        csvFile = open(csvFilePath,'a',newline='')
        writer = csv.writer(csvFile)

        resultsDict = result.__dict__
        modelSettingsDict = modelSettings.__dict__

        # Write header if not exist
        if not exists:
            # Create a header dependent on the result file
            header = ['time']
            for d in inputDict:
                header.append(d)
            for d in resultsDict:
                header.append(d)
            for d in modelSettingsDict:
                header.append(d)
            writer.writerow(header)

        # Write content
        row = [str(dt.now())]
        for d in inputDict:
            row.append(str(inputDict[d])[0:31])
        for d in resultsDict:
            row.append(resultsDict[d])
        for d in modelSettingsDict:
            row.append(modelSettingsDict[d])
        writer.writerow(row)

    except Exception as e:
        print(e)
        raise

# Function to create all instances for a sensitivity analysis
def createSensitivityAnalysisInstances():
    priceLevelList = [5,10,15,20,25]
    cardinalityList = [5,10,15,20,25]
    repetitions = 20

    for r in range(repetitions):
        # Create one baseline instance
        #v1 and v3
        input = Input().getRandomExample(segments = 5, products = 25, priceLevels = 25, cardinality = 25, baseUtilityRange = 8, betaRange = 1, outsideOptionRange = 5, costRange = 3, equalWeight = True)
        # v2
        #input = Input().getRandomExample(segments = 5, products = 25, priceLevels = 25, cardinality = 25, baseUtilityRange = 8, betaRange = 6, outsideOptionRange = 5, costRange = 3, equalWeight = True)
        input.repetition = r

        # Add the number of products to the name
        experimentName = 'PriceCardinality_v3' +' '+ str(input.products)

        # Folder and path
        dirname = os.path.dirname(__file__)
        path = os.path.join(dirname, 'experiments')
        Path(path).mkdir(parents=True, exist_ok=True)
        path = os.path.join(path, experimentName)

        # Location create folder including input folder
        Path(path).mkdir(parents=True, exist_ok=True)
        inputPath =  os.path.join(path, 'input')
        Path(inputPath).mkdir(parents=True, exist_ok=True)

        # Update every parameter effected by priceLevel and cardinality
        for priceLevels in priceLevelList:
            for cardinality in cardinalityList:
                input.priceLevels = priceLevels
                input.cardinality = cardinality
                input.priceList = [[10*(s+1)/input.priceLevels for s in range(input.priceLevels)] for j in range(input.products)]
                input.locations = input.calcMaxLocations(input.weight, cardinality)
                input.yLFO = [[[[0.000000001 for s in range(priceLevels)] for j in range(input.products)] for i in range(input.segments)] for b in range(2)]
                input.yUFO = [[[[1/input.Ai0[i] for s in range(priceLevels)] for j in range(input.products)] for i in range(input.segments)] for b in range(2)]
                #v3 : (1+input.beta[i][j])*input.priceList[j][s] instead
                input.attractionArray = [[[math.exp(input.baseUtility[i][j]-input.beta[i][j])*input.priceList[j][s] for s in range(priceLevels)] for j in range(input.products)] for i in range(input.segments)]
                input.attraction = []
                input.attraction = amplpy.DataFrame(('I', 'J', 'S'), 'A')
                input.attraction.setValues({
                    (i, j, s): input.attractionArray[i][j][s]
                    for i in range(input.segments)
                    for j in range(input.products)
                    for s in range(priceLevels)
                    })
                input.updateYBound()
                input.addFOConditionalYBoundSimple()
                input.name = str(input.segments) +' '+ str(input.priceLevels) +' '+ str(input.cardinality) +' '+ str(input.attributeUtilityRange) +' '+ str(input.betaRange) +' '+ str(input.outsideOptionRange) + ' ' + str(input.repetition)

                # Path and saving
                inputFilePath =  os.path.join(inputPath, input.name + ".txt")
                file = open(inputFilePath, 'w+')
                file.write(str(input.toDict()))
                file.close()
    

# Define solvers to solve an experiment
solverNames = ['conic','conicBC','gaAO']
solver = [conicCut,conicCut,gaAO]
settings = [ModelSettings() for sol in solver]
settings[0].useCallback = False
settings[0].maxTime = 60
settings[1].useCallback = True
settings[1].maxTime = 60
settings[2].stopAfterTime = True
settings[2].maxTimeHeuristic = 60


#arguments
if len(sys.argv) > 1:
    print('Arguments', sys.argv)
    conductExperiment(name = sys.argv[1], attributes= int(sys.argv[2]), attributeLevels= int(sys.argv[3]), products = int(sys.argv[4]), pldStructure = sys.argv[5] == 'True')
