import random
import time
import input
from modelSettings import ModelSettings
from datetime import datetime as dt
import matplotlib.pyplot as plt
import copy as cp
from operator import itemgetter
import math
import gurobipy as gp
from gurobipy import GRB
import numpy
from result import Result

# Main solution method
def solve(input: input, settings: ModelSettings):
    print('Two step heuristic', dt.now())

    # Make model settings accessible 
    global modelSettings
    modelSettings = settings

    # Update input values
    initializeVariables(input)

    # Parameter for statistics
    startTime = time.time()
    obj_list = []
    iter = 0

    stepOneSet = createInitialSet()
    obj_list.append(bestSolution[1])
    stepTwoSolution = createStepTwoSolution(stepOneSet)
    obj_list.append(bestSolution[1])

    # loop
    while stoppingCriterion(iter, startTime):
        stepOneSet = updateStepOneSet(stepTwoSolution)
        stepTwoSolution = createStepTwoSolution(stepOneSet)
    
        # Update iterations
        iter += 1
        obj_list.append(bestSolution[1])
        if iter % 10 == 0 or iter < 10:
            print('iteration:', iter, 'time:',time.time() - startTime, 'bestSolution:', bestSolution)

    # Final Time
    finalTime = time.time() - startTime
    print('obj_list',obj_list)
    # Show stats if required
    if modelSettings.displayResult:
        print(obj_list)
        plt.plot([j for j in range(len(obj_list))],obj_list)
        #plt.plot([j for j in range(len(obj_list))],[0 for j in range(len(obj_list))])
        plt.show()

    # Create Result
    print('iteration:', iter, 'time:',finalTime, 'Result:', bestSolution)
    result  = Result(numberOfProducts = len(bestSolution[0]), objective=bestSolution[1],solverName= 'twoStepH',time = finalTime)
    result.iteration = iter

    # Return result
    return result

# Returns the product id with a given pld structure
def getID(levels: list):
    id = 0
    for k,l in enumerate(levels):
        id += attributeToLevelMultiplier[k]*l
    return id

# Add neighboring products
def updateStepOneSet(stepTwoSolution: set):
    print('updateStepOneSet')
    stepOneSet = set()
    stepOneSet =stepTwoSolution.copy()
    
    iter = 0
    while len(stepOneSet) < modelSettings.productsInSet:
        productId = random.sample(stepTwoSolution, 1)[0]
        productAttributes = idToLevel[productId].copy()
        attributeID = random.randint(0,attributes-1)
        plusOrMinus = random.randint(0,1)*2-1
        productAttributes[attributeID] = max(0,min(attributeListLength[attributeID]-1,productAttributes[attributeID] + plusOrMinus))
        newProduct = getID(productAttributes)
        stepOneSet.add(newProduct)
        iter += 1
        if iter > modelSettings.productsInSet:
            break
    print(stepOneSet)
    return stepOneSet

# Solves the restricted problem with gurobi
def createStepTwoSolution(stepOneSet: set):
    print('createStepTwoSolution')
    global bestSolution
    startTime = time.time()
    loadGurobi(stepOneSet)
    print('Loading gurobi model after:',time.time() - startTime)

    model.optimize()

    # Extract solution
    print('\nObjective: %g' % model.ObjVal)

    # Calculate sum of products
    setOfProducts = set()

    for j in stepOneSet:
        for s in range(priceLevels):
            if x[j,s].X > 0.01:
                print('%s %g' % ((j,s)), x[j,s].X)
                setOfProducts.add(j)

    #Update bestSolution
    bestSolution = [setOfProducts, model.ObjVal]
    print('bestSolution', bestSolution)

    # Reset model
    model.dispose()
    
    return setOfProducts

# loads AMPL
def loadGurobi(stepOneSet: set):
    # Measure time
    startTime = time.time()

    # Create gurobi model
    global model
    model = gp.Model("twoStepH")

    # Create decision variables
    global x
    global y
    global z
    global w
    x = model.addVars([(j,s) for j in stepOneSet for s in range(priceLevels)], name="x", vtype=GRB.BINARY)
    y = model.addVars([i for i in range(segments)], name="y")
    z = model.addVars([(i,j,s) for i in range(segments) for j in stepOneSet for s in range(priceLevels)], name="z")
    w = model.addVars([i for i in range(segments)], name="w")
    #model.addConstrs((x[j,s] >= 0 for j in stepOneSet for s in range(priceLevels)) , name="rangeX0")
    #model.addConstrs((x[j,s] <= 1 for j in stepOneSet for s in range(priceLevels)) , name="rangeX1")
    #model.addConstrs((y[i] >= 0 for i in range(segments)) , name="rangeY0")
    #model.addConstrs((z[i,j,s] >= 0 for i in range(segments) for j in stepOneSet for s in range(priceLevels)) , name="rangeZ0")
    #model.addConstrs((w[i] >= 0 for i in range(segments)) , name="rangeW0")
    print('Loading variables after:',time.time() - startTime)
    
    # Add objective:
    model.setObjective(maxPrice - gp.quicksum(omega[i] * Ai0[i] * maxPrice * y[i] for i in range(segments)) - gp.quicksum(omega[i] * (maxPrice - priceList[j][s] + cost[j]) * attractionArray[i][j][s] * z[(i,j,s)] for i in range(segments) for j in stepOneSet for s in range(priceLevels)), GRB.MAXIMIZE)
    
    # Add Constraints:
    model.addConstrs((gp.quicksum(x[j,s] for s in range(priceLevels)) <= 1 for j in stepOneSet),"constraint1")
    model.addConstr((gp.quicksum(x[j,s]*weight[j] for j in stepOneSet for s in range(priceLevels)) == cardinality ),"cardinality")
    model.addConstrs(((Ai0[i] + gp.quicksum(x[j,s] * attractionArray[i][j][s] for j in stepOneSet for s in range(priceLevels)) == w[i]) for i in range(segments)),"constraint1prime")
    model.addConstrs((z[i,j,s] * w[i] >= x[j,s] * x[j,s] for j in stepOneSet for s in range(priceLevels) for i in range(segments)),"constraint2prime")
    model.addConstrs((y[i] * w[i] >= 1 for i in range(segments)),"constraint3prime")
    model.addConstrs((Ai0[i] * y[i] + gp.quicksum(attractionArray[i][j][s] * z[i,j,s] for j in stepOneSet for s in range(priceLevels)) >= 1 for i in range(segments)),"constraint4prime")
    print('Loading constraints after:',time.time() - startTime)

    # Adjust for McCormick:
    # General if McCormick should be used
    if modelSettings.heuristicMcCormick:
        # If a cut 1 is used in callback don't add it beforehand
    
        model.addConstrs((z[i,j,s] <= (1/(Ai0[i]+attractionArray[i][j][s]))*x[j,s] for j in stepOneSet for s in range(priceLevels) for i in range(segments)),"McCormick1")
        print('McCormick1 added after:',time.time() - startTime)
        model.addConstrs((z[0,j,s] <= (1/(Ai0[0]+attractionArray[0][j][s]))*x[j,s] for j in stepOneSet for s in range(priceLevels)),"McCormick11")
        
        # If a cut 2 is used in callback don't add it beforehand
    
        model.addConstrs((z[i,j,s] >= yLFO[1][i][j][s] * x[j,s] for j in stepOneSet for s in range(priceLevels) for i in range(segments)),"McCormick2")
        print('McCormick2 added after:',time.time() - startTime)

        # If a cut 3 is used in callback don't add it beforehand
    
        model.addConstrs((z[i,j,s] <= y[i] - yLFO[0][i][j][s] * (1 - x[j,s]) for j in stepOneSet for s in range(priceLevels) for i in range(segments)),"McCormick3")
        print('McCormick3 added after:',time.time() - startTime)

        # If a cut 4 is used in callback don't add it beforehand
    
        model.addConstrs((z[i,j,s] >= y[i]-(1/Ai0[i])*(1-x[j,s]) for j in stepOneSet for s in range(priceLevels) for i in range(segments)),"McCormick4")
        print('McCormick4 added after:',time.time() - startTime)
        

    # Update model
    model.update()
    model._cutsNr = [0 for cutNr in range(5)]
    model._cutsNr[0] = [0 for mcCut in range(4)]
    model._timeInCallback = 0

    if modelSettings.twoStepRestrictMaxTime:
        model.setParam('TimeLimit',modelSettings.twoStepMaxTimeSolver)

    # Print total time
    print('Loading McCormick after:',time.time() - startTime)

# Method to create an initial set
def createInitialSet():
    print('create initial set')
    global bestSolution    
    global model
    # Measure time
    startTime = time.time()
    loadInitialGurobi()
    print('Loading ampl model after:',time.time() - startTime)

    # Create solution for each segment
    model.optimize()

    #if model.status == GRB.OPTIMAL:
    print('\nObjective: %g' % model.ObjVal)
    
    # Calculate sum of products
    listOfProducts = [0 for j in range(products)]

    for j in range(products):
        for s in range(priceLevels):
            listOfProducts[j] += x[j,s].X
    
    # Create the n largest indexes
    largestIndex = sorted(range(len(listOfProducts)), key=lambda i: listOfProducts[i], reverse=True)[:modelSettings.productsInSet]

    # Create initial set only with values > 0.1
    initialSet = set()
    for j in largestIndex:
        if listOfProducts[j] > 0.1:
            initialSet.add(j)
        else:
            break


    #Update bestSolution
    bestSolution = [initialSet, model.ObjVal]
    print(bestSolution)

    # Reset model
    model.dispose()

    return initialSet
    
# loads AMPL
def loadInitialGurobi():
    # Measure time
    startTime = time.time()

    # Create gurobi model
    global model
    model = gp.Model("twoStepH")

    # Create decision variables
    global x
    global y
    global z
    global w
    x = model.addVars([(j,s) for j in range(products) for s in range(priceLevels)], name="x")
    y = model.addVars([i for i in range(segments)], name="y")
    z = model.addVars([(i,j,s) for i in range(segments) for j in range(products) for s in range(priceLevels)], name="z")
    w = model.addVars([i for i in range(segments)], name="w")
    model.addConstrs((x[j,s] >= 0 for j in range(products) for s in range(priceLevels)) , name="rangeX0")
    model.addConstrs((x[j,s] <= 1 for j in range(products) for s in range(priceLevels)) , name="rangeX1")
    model.addConstrs((y[i] >= 0 for i in range(segments)) , name="rangeY0")
    model.addConstrs((z[i,j,s] >= 0 for i in range(segments) for j in range(products) for s in range(priceLevels)) , name="rangeZ0")
    model.addConstrs((w[i] >= 0 for i in range(segments)) , name="rangeW0")
    
    print('Loading variables after:',time.time() - startTime)

    # Add objective:
    #model.setObjective(priceLevels - gp.quicksum(omega[i] * Ai0[i] * priceLevels * y[i] for i in range(segments)) - gp.quicksum(omega[i] * (priceLevels - priceList[j][s] + cost[j]) * attractionArray[i][j][s] * z[(i,j,s)] for i in range(segments) for j in range(products) for s in range(priceLevels)), GRB.MAXIMIZE)
    model.setObjective(maxPrice - gp.quicksum(omega[i] * Ai0[i] * maxPrice * y[i] for i in range(segments)) - gp.quicksum(omega[i] * (maxPrice - priceList[j][s] + cost[j]) * attractionArray[i][j][s] * z[(i,j,s)] for i in range(segments) for j in range(products) for s in range(priceLevels)), GRB.MAXIMIZE)
    
    # Add Constraints:
    model.addConstrs((gp.quicksum(x[j,s] for s in range(priceLevels)) <= 1 for j in range(products)),"constraint1")
    model.addConstr((gp.quicksum(x[j,s]*weight[j] for j in range(products) for s in range(priceLevels)) <= cardinality ),"cardinality")
    model.addConstrs(((Ai0[i] + gp.quicksum(x[j,s] * attractionArray[i][j][s] for j in range(products) for s in range(priceLevels)) == w[i]) for i in range(segments)),"constraint1prime")
    model.addConstrs((z[i,j,s] * w[i] >= x[j,s] * x[j,s] for j in range(products) for s in range(priceLevels) for i in range(segments)),"constraint2prime")
    model.addConstrs((y[i] * w[i] >= 1 for i in range(segments)),"constraint3prime")
    model.addConstrs((Ai0[i] * y[i] + gp.quicksum(attractionArray[i][j][s] * z[i,j,s] for j in range(products) for s in range(priceLevels)) >= 1 for i in range(segments)),"constraint4prime")
    print('Loading constraints after:',time.time() - startTime)

    # Adjust for McCormick:
    # General if McCormick should be used
    if modelSettings.mcCormick:
        # If a cut 1 is used in callback don't add it beforehand
    
        model.addConstrs((z[i,j,s] <= (1/(Ai0[i]+attractionArray[i][j][s]))*x[j,s] for j in range(products) for s in range(priceLevels) for i in range(segments)),"McCormick1")
        print('McCormick1 added after:',time.time() - startTime)
        model.addConstrs((z[0,j,s] <= (1/(Ai0[0]+attractionArray[0][j][s]))*x[j,s] for j in range(products) for s in range(priceLevels)),"McCormick11")
        
        # If a cut 2 is used in callback don't add it beforehand
    
        model.addConstrs((z[i,j,s] >= yLFO[1][i][j][s] * x[j,s] for j in range(products) for s in range(priceLevels) for i in range(segments)),"McCormick2")
        print('McCormick2 added after:',time.time() - startTime)

        # If a cut 3 is used in callback don't add it beforehand
    
        model.addConstrs((z[i,j,s] <= y[i] - yLFO[0][i][j][s] * (1 - x[j,s]) for j in range(products) for s in range(priceLevels) for i in range(segments)),"McCormick3")
        print('McCormick3 added after:',time.time() - startTime)

        # If a cut 4 is used in callback don't add it beforehand
    
        model.addConstrs((z[i,j,s] >= y[i]-(1/Ai0[i])*(1-x[j,s]) for j in range(products) for s in range(priceLevels) for i in range(segments)),"McCormick4")
        print('McCormick4 added after:',time.time() - startTime)
        

    # Update model
    model.update()
    model._cutsNr = [0 for cutNr in range(5)]
    model._cutsNr[0] = [0 for mcCut in range(4)]
    model._timeInCallback = 0

    if modelSettings.twoStepRestrictMaxTime:
        model.setParam('TimeLimit',modelSettings.twoStepMaxTimeSolver)
        model.setParam('BarHomogeneous',1)
        model.setParam('ScaleFlag',2)

    # Print total time
    print('Loading McCormick after:',time.time() - startTime)

# Stopping criterion returns true if it needs to stop
def stoppingCriterion(iter: int, startTime):
    if modelSettings.twoStepStopAfterTime:
        return time.time() <= startTime + modelSettings.maxTimeHeuristic
    if modelSettings.twoStepStopAfterIterations:
        return iter < modelSettings.twoStepIteration

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
    global quasiProducts
    global attractionArray
    global attributeLevels
    global attributes
    global yL
    global yU
    global maxPrice
    global priceList
    global idToLevel
    global attributeToLevelMultiplier
    global attributeListLength

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
    quasiProducts = products * priceLevels
    attractionArray = input.attractionArray
    attributeLevels = input.attributeLevels
    attributes = input.attributes
    maxPrice = input.priceLevels
    quasiProducts = products * priceLevels
    yL = input.yL
    yU = input.yU


    # Transforms a product in its pld structure and visa versa
    idToLevel = [[input.levelMapping[j][k][0] for k in range(attributes)] for j in range(products)]


    # Create prices if not provided
    if not hasattr(input, 'priceList'):
        priceList = [[s+1 for s in range(priceLevels)] for j in range(products)]
    else:
        priceList = input.priceList
        maxPrice = -100
        for j in priceList:
            if maxPrice < max(j):
                maxPrice = max(j)

    # For the algorithm
    global bestSolution

    # Best Genome
    bestSolution = [[], 0] # Which products to offer and objective value

    # Adjust for different attribute dimensions
    if not hasattr(input, 'attributeListLength'):
        attributeListLength = [attributeLevels for k in range(attributes)]
    else:
        attributeListLength = input.attributeListLength

    attributeToLevelMultiplier = [0 for k in range(attributes)]
    for k in range(attributes):
        if k == 0:
            attributeToLevelMultiplier[attributes-k-1] = 1
        else:
            attributeToLevelMultiplier[attributes-k-1] = attributeToLevelMultiplier[attributes-k]*attributeListLength[attributes-k]
   