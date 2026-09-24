# Load libraries
import os
import pandas as pd
import amplpy
from input import Input
from modelSettings import ModelSettings
import time
from result import Result
from datetime import datetime as dt

# Solve model
def solve(input: Input, settings: ModelSettings):
    print('bigM',dt.now())
    # Make model settings accessible 
    global modelSettings
    modelSettings = settings

    # Initialize
    initializeVariables(input)

    # Load ampl model with all fixed values
    loadAmpl()

    # Solve the specific instance and returns all information about the result
    return solveAmpl()


# Method to load ampl instance

def loadAmpl():
    # Create ampl instance and read model
    global ampl
    ampl = amplpy.AMPL()
    ampl.read(os.path.join(os.path.realpath(''),
              'amplModels/exact', 'bigM.mod'))

    # Load all constants that are fixed
        # Set sets
    ampl.getSet('J').setValues([j for j in range(products)])
    ampl.getSet('I').setValues([i for i in range(segments)])
    ampl.getSet('Pj').setValues([s for s in range(priceLevels)])

    # Set parameters
    ampl.getParameter('p').setValues(
                {(j, s): priceList[j][s] for s in range(priceLevels) for j in range(products)})
    ampl.getParameter('cardinality').setValues([cardinality])
    ampl.getParameter('phat').setValues([priceLevels])
    ampl.getParameter('Ai0').setValues(Ai0)
    ampl.getParameter('omega').setValues(omega)
    ampl.getParameter('weight').setValues(weight)
    ampl.getParameter('cost').setValues(cost)
    ampl.setData(attraction)

    # Adjust for McCormick:
    if modelSettings.mcCormick:
        # Load data for McCormick inequalities
        ampl.getParameter('yLowerX0').setValues(
                {(i, j, s): yLFO[0][i][j][s] for i in range(segments) for j in range(products) for s in range(priceLevels)})
        ampl.getParameter('yLowerX1').setValues(
                {(i, j, s): yLFO[1][i][j][s] for i in range(segments) for j in range(products) for s in range(priceLevels)})

    else:
        # Remove McCormick inequalities from the model if not used
        ampl.getConstraint('McCormick1').drop()
        ampl.getConstraint('McCormick2').drop()
        ampl.getConstraint('McCormick3').drop()
        ampl.getConstraint('McCormick4').drop()

    # Set options
    # Max time:
    if modelSettings.restrictMaxTime:
        ampl.setOption('gurobi_options','timelim ='+  str(modelSettings.maxTime))

    # Solver settings:
    ampl.setOption('solver', 'gurobi')  # alternative 'cplexamp' or 'cplex'
    ampl.setOption('show_stats', '1') # Shows details about the model
    ampl.setOption('gurobi_options','outlev = 1 timelim ='+  str(modelSettings.maxTime))


# Method to solve the method
def solveAmpl():    
    # Solve
    startTime = time.time()
    ampl.solve()
    finalTime = time.time() - startTime

    # Output
    print("\n Final time=", finalTime)
    objective = ampl.getObjective('profit').value()
    print("Objective is:", objective)
    decisionVariables = pd.DataFrame(ampl.getVariable('x').getValues(), columns=[ 'j', 's', 'x'])
    decision = decisionVariables[decisionVariables['x'] > 0]
    print('The best set has', len(decision), 'products:')
    print(decision)
    decisionVariablesZ = pd.DataFrame(ampl.getVariable('z').getValues())
    print(decisionVariablesZ[decisionVariablesZ[3] > 0.000001])

    # Return all results
    return Result(solverName = 'bigM', objective = objective, time = finalTime, numberOfProducts=len(decision))

# Initializes solution procedure
def initializeVariables(input: input):
    # Initialize all variables as global
    global weight
    global segments 
    global products 
    global locations
    global priceLevels
    global cardinality
    global Ai0
    global omega
    global attraction 
    global yLFO
    global yUFO
    global cost
    global priceList
    global maxPrice


    # Set data
    weight = input.weight
    cost = input.cost
    segments = input.segments
    products = input.products
    locations = input.locations
    priceLevels = input.priceLevels
    cardinality = input.cardinality
    Ai0 = input.Ai0
    omega = input.omega
    attraction = input.attraction
    yLFO = input.yLFO
    yUFO = input.yUFO

    # Create prices if not provided
    if not hasattr(input, 'priceList'):
        priceList = [[s+1 for s in range(priceLevels)] for j in range(products)]
    else:
        priceList = input.priceList
        maxPrice = -100
        for j in priceList:
            if maxPrice < max(j):
                maxPrice = max(j)
