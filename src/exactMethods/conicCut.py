# Load libraries
import random
import sys
import gurobipy as gp
from gurobipy import GRB
import os
import pandas as pd
import pandas as pd
from input import Input
from modelSettings import ModelSettings
import time
from result import Result
import psutil
import gc

# Solve model
def solve(input: Input, settings: ModelSettings):
    # Make model settings accessible 
    setModelSettings(settings)

    # Initialize
    initializeVariables(input)

    # Load ampl model with all fixed values
    loadModel()

    # Solve the specific instance and returns all information about the result
    return solveAmpl()

# Sets the settings to being global
def setModelSettings(settings: ModelSettings):
    # Make model settings accessible 
    global modelSettings
    modelSettings = settings

# Adds a constraint, where all variables in the list are forced to 0
def setXVariablesZero(listOfX: list):
    global model
    model.addConstrs((x[j,s] == 0 for s in range(priceLevels) for j in list),'zeroX')

# Method to load the gurobi model
def loadModel():
    # Measure time
    startTime = time.time()

    # Create gurobi model
    global model
    model = gp.Model("conicCut")

    # Create decision variables
    global x
    global y
    global z
    global w
    x = model.addVars([(j,s) for j in range(products) for s in range(priceLevels)], name="x", vtype=GRB.BINARY)
    y = model.addVars([i for i in range(segments)], name="y")
    z = model.addVars([(i,j,s) for i in range(segments) for j in range(products) for s in range(priceLevels)], name="z")
    w = model.addVars([i for i in range(segments)], name="w")
    print('Loading variables after:',time.time() - startTime)

    # Add objective:
    #model.setObjective(priceLevels - gp.quicksum(omega[i] * Ai0[i] * priceLevels * y[i] for i in range(segments)) - gp.quicksum(omega[i] * (priceLevels - priceList[j][s] + cost[j]) * attractionArray[i][j][s] * z[(i,j,s)] for i in range(segments) for j in range(products) for s in range(priceLevels)), GRB.MAXIMIZE)
    model.setObjective(maxPrice - gp.quicksum(omega[i] * Ai0[i] * maxPrice * y[i] for i in range(segments)) - gp.quicksum(omega[i] * (maxPrice - priceList[j][s] + cost[j]) * attractionArray[i][j][s] * z[(i,j,s)] for i in range(segments) for j in range(products) for s in range(priceLevels)), GRB.MAXIMIZE)
    
    # Add Constraints:
    model.addConstrs((gp.quicksum(x[j,s] for s in range(priceLevels)) <= 1 for j in range(products)),"constraint1")
    if modelSettings.fixedCardinality and cardinality <= products:
        model.addConstr((gp.quicksum(x[j,s]*weight[j] for j in range(products) for s in range(priceLevels)) == cardinality ),"cardinality")
    else:
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
        if (not modelSettings.mcCormickIndividual[0] and modelSettings.useCallback) or not modelSettings.useCallback:
            model.addConstrs((z[i,j,s] <= (1/(Ai0[i]+attractionArray[i][j][s]))*x[j,s] for j in range(products) for s in range(priceLevels) for i in range(segments)),"McCormick1")
            print('McCormick1 added after:',time.time() - startTime)
            
        # If a cut 2 is used in callback don't add it beforehand
        if (not modelSettings.mcCormickIndividual[1] and modelSettings.useCallback) or not modelSettings.useCallback:
            model.addConstrs((z[i,j,s] >= yLFO[1][i][j][s] * x[j,s] for j in range(products) for s in range(priceLevels) for i in range(segments)),"McCormick2")
            print('McCormick2 added after:',time.time() - startTime)

        # If a cut 3 is used in callback don't add it beforehand
        if (not modelSettings.mcCormickIndividual[2] and modelSettings.useCallback) or not modelSettings.useCallback:
            model.addConstrs((z[i,j,s] <= y[i] - yLFO[0][i][j][s] * (1 - x[j,s]) for j in range(products) for s in range(priceLevels) for i in range(segments)),"McCormick3")
            print('McCormick3 added after:',time.time() - startTime)

        # If a cut 4 is used in callback don't add it beforehand
        if (not modelSettings.mcCormickIndividual[3] and modelSettings.useCallback) or not modelSettings.useCallback:
            model.addConstrs((z[i,j,s] >= y[i]-(1/Ai0[i])*(1-x[j,s]) for j in range(products) for s in range(priceLevels) for i in range(segments)),"McCormick4")
            print('McCormick4 added after:',time.time() - startTime)
        
    # If the number of new products should be fixed
    if modelSettings.newProductsEqualCardinality:
        model.addConstr((gp.quicksum(x[j,s]*weight[j] for j in range(products) for s in range(priceLevels)) == cardinality),"cardinalityFixed")

    # Update model
    model.update()
    model._cutsNr = [0 for cutNr in range(5)]
    model._cutsNr[0] = [0 for mcCut in range(4)]
    model._timeInCallback = 0

    # Uncomment if outer approximation should be used
    #model.setParam('MIQCPMethod',1)
    #model.setParam('Method',5)
    #model.setParam('MIPFocus',0)
    #model.setParam('Heuristics',0)

    if modelSettings.restrictMaxTime:
        model.setParam('TimeLimit',modelSettings.maxTime)

    # Print total time
    print('Loading McCormick after:',time.time() - startTime)
    
# Define my callback function
def myCallback(model, where):
    # MIP node callback
    if where == GRB.Callback.MIPNODE:
        startTimeCallback = time.time()
        
        # Check if it is the root node and this function is required to do something
        if model.cbGet(GRB.Callback.MIPNODE_NODCNT) == 0:
            model._rootNodeIteration += 1

            # Precalculate all offered products
            varXjs = [(j, s) for j in range(products) for s in range(priceLevels) if model.cbGetNodeRel(model._varsX[j][s]) > 0.001]
            
            #Check McCormick 
            if modelSettings.mcCormickIndividual[0]:
                checkMcCormick1(model)

            #Check McCormick 
            if modelSettings.mcCormickIndividual[1]:
                checkMcCormick2(model)

            #Check McCormick 
            if modelSettings.mcCormickIndividual[2]:
                checkMcCormick3(model)

            if modelSettings.mcCormickIndividual[3]:
                checkMcCormick4(model,varXjs)

            #Check prop 2
            if modelSettings.useCuts[1]:
                checkProp2(model, varXjs)

            #Check prop 3
            if modelSettings.useCuts[2]:
                checkProp3(model, varXjs)

            #Check prop 4
            if modelSettings.useCuts[3]:
                checkProp4(model,varXjs)

            #Check prop 5
            if modelSettings.useCuts[4]:
                checkProp5(model)

            del varXjs
            # Print current progress
            print('ROOT: cuts',model._rootNodeIteration, model._cutsNr, psutil.virtual_memory(), model._timeInCallback/(time.time() - startTime)  )

        elif model.cbGet(GRB.Callback.MIPNODE_STATUS) == GRB.OPTIMAL:
            #Check McCormick 
            model._rootNodeIteration += 1
            if model._rootNodeIteration % 3 == 0:

                # Precalculate all offered products
                varXjs = [(j, s) for j in range(products) for s in range(priceLevels) if model.cbGetNodeRel(model._varsX[j][s]) > 0.001]
                
                if modelSettings.mcCormickIndividual[3]:
                    checkMcCormick4(model,varXjs)
                
                if model._rootNodeIteration % 6 == 0:
                    #Check prop 2
                    if modelSettings.useCuts[1]:
                        checkProp2(model, varXjs)

                    #Check prop 3
                    if modelSettings.useCuts[2]:
                        checkProp3(model, varXjs)

                    #Check prop 4
                    #if modelSettings.useCuts[3]:
                        #checkProp4(model, varXjs)

                    # Print current progress
                    if model._rootNodeIteration % 60 == 0:
                        print('NODE:',model._rootNodeIteration ,model._cutsNr, psutil.virtual_memory(), model._timeInCallback/(time.time() - startTime) )
                        gc.collect()

                del varXjs

        model._timeInCallback +=  time.time() - startTimeCallback
        del startTimeCallback
                
# Method which checks mcCormick 1
def checkMcCormick1(model):
    global mcKormickSet
    mcKormickSet[0] = [ele for ele in mcKormickSet[0] if not testMcCormick1(model, ele[0], ele[1], ele[2])]

# Tests if the McCormick 1 is violated
def testMcCormick1(model, i, j, s):
    lhs = model.cbGetNodeRel(model._varsZ[i][j][s]) - APlusAi0Inverse[i][j][s] * model.cbGetNodeRel(model._varsX[j][s])
    # Returns if the equation is violated
    if lhs > 0.00001:
        addMcCormick1Lazy(model, i, j, s)
        return True
    else:
        return False

# Adds McKormick 1 lazily
def addMcCormick1Lazy(model, i, j, s):
    model.cbLazy((model._varsZ[i][j][s] <= APlusAi0Inverse[i][j][s] * model._varsX[j][s]))
    model._cutsNr[0][0] += 1

# Method which checks mcCormick 2
def checkMcCormick2(model):
    global mcKormickSetProducts
    for j in range(len(mcKormickSetProducts[1])):
        for s in mcKormickSetProducts[1][j]:
            if model.cbGetNodeRel(model._varsX[j][s]) > 0.001:
                mcKormickSetProducts[1][j].remove(s)
                for i in range(segments):
                    addMcCormick2Lazy(model, i, j, s)

# Tests if the McCormick 2 is violated
def testMcCormick2(model, i, j, s):
    lhs = model.cbGetNodeRel(model._varsZ[i][j][s]) - yLFO[1][i][j][s] * model.cbGetNodeRel(model._varsX[j][s])
    # Returns if the equation is violated
    if lhs < -0.0001:
        addMcCormick2Lazy(model, i, j, s)
        return True
    else:
        return False

# Adds McKormick 2 lazily
def addMcCormick2Lazy(model, i, j, s):
    model.cbLazy((model._varsZ[i][j][s] >= yLFO[1][i][j][s] * model._varsX[j][s]))
    model._cutsNr[0][1] += 1

# Method which checks mcCormick 3
def checkMcCormick3(model):
    global mcKormickSet
    mcKormickSet[2] = [ele for ele in mcKormickSet[2] if not testMcCormick3(model, ele[0], ele[1], ele[2])]

# Tests if the McCormick 3 is violated
def testMcCormick3(model, i, j, s):
    lhs = model.cbGetNodeRel(model._varsZ[i][j][s]) - model.cbGetNodeRel(model._varsY[i]) +  yLFO[0][i][j][s] * (1 - model.cbGetNodeRel(model._varsX[j][s]))
    # Returns if the equation is violated
    if lhs > 0.0001:
        addMcCormick3Lazy(model, i, j, s)
        return True
    else:
        return False

# Adds McKormick 3 lazily
def addMcCormick3Lazy(model, i, j, s):
    model.cbLazy((model._varsZ[i][j][s] <= model._varsY[i] - yLFO[0][i][j][s] * (1 - model._varsX[j][s])))
    model._cutsNr[0][2] += 1

# Method which checks mcCormick 4
def checkMcCormick4(model, varXjs: list):
    global mcKormickSetProducts
    for (j,s) in varXjs:
        if s in mcKormickSetProducts[3][j]:
            mcKormickSetProducts[3][j].remove(s)
            for i in range(segments):
                addMcCormick4Lazy(model, i, j, s)
                
# Tests if the McCormick 4 is violated
def testMcCormick4(model, i, j, s):
    # Returns if the equation is violated (calculation of lhs)
    if model.cbGetNodeRel(model._varsZ[i][j][s]) - model.cbGetNodeRel(model._varsY[i]) + Ai0Inverse[i] - Ai0Inverse[i] * model.cbGetNodeRel(model._varsX[j][s]) < -0.001:
        addMcCormick4Lazy(model, i, j, s)
        return True
    else:
        return False

# Adds McKormick 4 lazily
def addMcCormick4Lazy(model, i, j, s):
    model.cbLazy((model._varsZ[i][j][s] >= model._varsY[i] - Ai0Inverse[i] + Ai0Inverse[i] * model._varsX[j][s]))
    model._cutsNr[0][3] += 1
        

# Method which checks prop 2
def checkProp2(model, varXjs: list):
    # Do this process for each segment
    for i in range(segments):
        # Calculate all Values per product
        influenceLeft = [] # which is for parts with j,s
        influenceRight = [] # which is for parts with j2,s2

        for (j,s) in varXjs:
            # Overestimate 
            infLeft = yLInverse[i] * model.cbGetNodeRel(model._varsZ[i][j][s])  - model.cbGetNodeRel(model._varsX[j][s])
            infRight = APlusAi0[i][j][s] * model.cbGetNodeRel(model._varsZ[i][j][s]) - model.cbGetNodeRel(model._varsX[j][s]) 
            influenceLeft.append((j,s,infLeft))
            influenceRight.append((j,s,infRight))

        # Sort
        influenceLeft = sorted(influenceLeft, key = lambda tup: tup[2])
        influenceRight = sorted(influenceRight, key = lambda tup: tup[2], reverse=True)

        # Test
        for (j, s, infRight) in influenceLeft:
            for (j2, s2, infLeft) in influenceRight:
                if infRight - infLeft < -0.00001:
                    addProp2Lazy(model, i, j, s, j2, s2)
                    # If one combination does not work, then break the loop
                else:
                    break

    del influenceLeft
    del influenceRight
    del infLeft
    del infRight

# Tests if the cut 2 is violated
def testProp2(model, i, j, s, j2, s2):
    lhs = model.cbGetNodeRel(model._varsZ[i][j][s]) * yLFOInverse[0][i][j2][s2] - APlusAi0[i][j2][s2] * model.cbGetNodeRel(model._varsZ[i][j2][s2]) - model.cbGetNodeRel(model._varsX[j][s]) + model.cbGetNodeRel(model._varsX[j2][s2])
    
    # Returns if the equation is violated
    if lhs < -0.001:
        return True
    else:
        return False

# Adds Prop 2 lazily
def addProp2Lazy(model, i, j, s, j2, s2):
    model.cbLazy((model._varsZ[i][j][s] * yLFOInverse[0][i][j2][s2] - APlusAi0[i][j2][s2] * model._varsZ[i][j2][s2] - model._varsX[j][s] + model._varsX[j2][s2]) >= 0)
    model._cutsNr[1] += 1

# Method to check Prop 3 and adds it if violated
def checkProp3(model, varXjs: list):
    # Do this process for each segment
    for i in range(segments):
    # Calculate all Values per product
        influence = []
        totalInfluence = 0
        for (j,s) in varXjs:
            inf = attractionArray[i][j][s] * model.cbGetNodeRel(model._varsX[j][s]) - ATimesAPlusAi0[i][j][s] * model.cbGetNodeRel(model._varsZ[i][j][s])
            influence.append((j, s, inf))
            totalInfluence += inf
        # Sort
        influence = sorted(influence, key = lambda tup: tup[2], reverse=True)
        
        # Test
        for (j, s, inf) in influence:
            if totalInfluence - inf < inf - 0.00001:
                addProp3Lazy(model, i, j, s)
            else:
                break

    del influence
    del totalInfluence
    del inf

# Adds Prop 3 lazily
def addProp3Lazy(model, i, j, s):
        model.cbLazy(((gp.quicksum(ATimesAPlusAi0[i][k][t] * model._varsZ[i][k][t] for k in range(products) for t in range(priceLevels)) - 2 * ATimesAPlusAi0[i][j][s] * model._varsZ[i][j][s] -  gp.quicksum(attractionArray[i][k][t] * model._varsX[k][t] for k in range(products) for t in range(priceLevels)) + 2 * attractionArray[i][j][s] * model._varsX[j][s] <= 0)))
        model._cutsNr[2] += 1
  
# Tests if the cut 3 is violated
def testProp3(model, i: int, j: int, s: int):
    lhs = 0
    for k in range(products): 
        for t in range(priceLevels):
            lhs += ATimesAPlusAi0[i][k][t] * model.cbGetNodeRel(model._varsZ[i][k][t]) - attractionArray[i][k][t] * model.cbGetNodeRel(model._varsX[k][t])
    
    lhs -= 2 * ATimesAPlusAi0[i][j][s] * model.cbGetNodeRel(model._varsZ[i][j][s])
    lhs += 2 * attractionArray[i][j][s] * model.cbGetNodeRel(model._varsX[j][s])
    
    # Gives a small room of margin for numerical inaccuracy
    if lhs <= 0.0001:
        return False
    else:
        return True

# Method which checks prop 4
def checkProp4(model, varXjs: list):
    # Calculate the number of products that could be offered
    productsIncluded = 0
    jDummy = -1
    for (j,s) in varXjs:
        if j != jDummy:
            jDummy = j
            productsIncluded += 1

    # Check every segment
    for i in range(segments):
        indexVarZ = [[j,0] for j in range(products)]
        for (j,s) in varXjs:
            indexVarZ[j][1] = model.cbGetNodeRel(model._varsZ[i][j][s])

        # Sort by value
        indexVarZ.sort(key = lambda x: x[1], reverse = True)

        # Test both index orders
        if testProp4(model, i, indexVarZ, productsIncluded):
            addProp4Lazy(model, i, indexVarZ)

# Adds Prop 4 lazily
def addProp4Lazy(model, i: int, index: list):
    model.cbLazy(gp.quicksum(-  ATimesAPlusAi0[i][index[0][0]][s] * model._varsZ[i][index[0][0]][s] for s in range(priceLevels)) 
                 + gp.quicksum(ATimesAPlusAi0[i][index[1][0]][s] * model._varsZ[i][index[1][0]][s] for s in range(priceLevels)) 
                 + gp.quicksum(part3ListCut4[j][s] * model._varsZ[i][j][s] for [j,x] in index[2:] for s in range(priceLevels)) 
                >= 
                gp.quicksum(- attractionArray[i][index[0][0]][s] * model._varsX[index[0][0]][s] for s in range(priceLevels)) 
                + gp.quicksum(attractionArray[i][j][s]* model._varsX[j][s] for [j,x] in index[1:] for s in range(priceLevels)))
    model._cutsNr[3] += 1

# Tests if cut 4 is violated
def testProp4(model, i: int, index: list, productsIncluded: int):
    # Create inner list first
    twoSumAij0 = []
    currentValue = 0
    for [j,x] in index[1:]:
        currentValue += 2* highestAttraction[i][j]
        twoSumAij0.append(currentValue)

    # Parts of the inequality
    lhs = 0

    # Access precalculated from part 3 later
    global part3ListCut4

    for s in range(priceLevels):
        #part1
        lhs -= ATimesAPlusAi0[i][index[0][0]][s] * model.cbGetNodeRel(model._varsZ[i][index[0][0]][s])
        #part2
        lhs += ATimesAPlusAi0[i][index[1][0]][s] * model.cbGetNodeRel(model._varsZ[i][index[1][0]][s])
        #part 4
        lhs += attractionArray[i][index[0][0]][s] * model.cbGetNodeRel(model._varsX[index[0][0]][s])
        #part 5
        for [j,x] in index[1:productsIncluded]:
            lhs -= attractionArray[i][j][s] * model.cbGetNodeRel(model._varsX[j][s])

    # part3 
    for s in range(priceLevels):
        for id,[j, x] in enumerate(index[1:]):
            # Calculate only if the multiplication is greater zero
            part3ListCut4[j][s] = (APlusAi0[i][j][s] + twoSumAij0[id]) * attractionArray[i][j][s]
            lhs += model.cbGetNodeRel(model._varsZ[i][j][s]) * part3ListCut4[j][s]
            
            #only if it is possible
            if lhs > -0.0001:
                return False
    
    # Else return True
    return True

# Method which checks prop 4
def checkProp5(model):

    # Check all x variables 
    for j1 in range(products):
        for s,x in enumerate(model.cbGetNodeRel(model._varsX[j1])):
            # Only with a high x value it should be tested
            if x > 0.5 and x < 1:
                for i in range(segments):
                    # Check if the two main variables would satisfy the constraint by neglecting the others
                    if model.cbGetNodeRel(model._varsZ[i][j1][s]) * APlusAi0[i][j1][s] < x:
                        # Check again all x variables
                        for j2 in range(products):
                            for s2,x2 in enumerate(model.cbGetNodeRel(model._varsX[j2])):
                                if x2 > 0.25 and x2 < 1:
                                    index = [j for j in range(products) if j not in [j1,j2]]
                                    # Test first if the cut is violated
                                    if testProp5(model, i, j1, j2, index):
                                        addProp5Lazy(model, i, j1, j2, index)
                                        random.shuffle(index)
                                        if testProp5(model, i, j1, j2, index):
                                            addProp5Lazy(model, i, j1, j2, index)
                                
# Adds Prop 5 lazily
def addProp5Lazy(model, i: int, j1: int, j2: int, index: list):
    model.cbLazy(
    gp.quicksum((ATimesAPlusAi0[i][j1][s] * A2PlusAi0[i][j2][priceLevels-1] * model._varsZ[i][j1][s] 
    + ATimesAPlusAi0[i][j2][s] * A2PlusAi0[i][j1][priceLevels-1] * model._varsZ[i][j2][s] 
    + gp.quicksum(part3ListCut5[j][s] * model._varsZ[i][j][s] 
    for j in index) for s in range(priceLevels))) 
    <= 2 * attractionArray[i][j2][0] * attractionArray[i][j1][0]
    + gp.quicksum(ATimesAi0[i][j1][s] * model._varsX[j1][s] for s in range(priceLevels))
    - gp.quicksum(ATimesAi0[i][j][s] * model._varsX[j][s] for j in index for s in range(priceLevels)))
    model._cutsNr[4] += 1

# Tests if cut 5 is violated
def testProp5(model, i: int, j1: int, j2: int, index: list):
    lhs = 0
    part1 = 0
    part2 = 0
    part3 = 0
    rhs = 0

    # Precalculated list for adding the constraint later
    global part3ListCut5

    for s in range(priceLevels):
        part1 += ATimesAPlusAi0[i][j1][s] * A2PlusAi0[i][j2][priceLevels-1] * model.cbGetNodeRel(model._varsZ[i][j1][s])
        part2 += ATimesAPlusAi0[i][j2][s] * A2PlusAi0[i][j1][priceLevels-1] * model.cbGetNodeRel(model._varsZ[i][j2][s])
        # part 3
        for x,j in enumerate(index):
            part3Dummy = ATimesAi0TimesAi0PlusA[i][j][s] - 2 * attractionArray[i][j][s] * attractionArray[i][j1][priceLevels-1] * attractionArray[i][j2][priceLevels-1]
            attractionSum = 0
            for jh in index[0:x]:
                attractionSum += attractionArray[i][jh][0]
            part3Dummy += attractionSum * 2 * ATimesAi0[i][j][s]

            part3ListCut5[j][s] = part3Dummy
            part3 += model.cbGetNodeRel(model._varsZ[i][j][s]) * part3Dummy

        # Last sum first
        for s in range(priceLevels):
            for jh in index:
                rhs -= ATimesAi0[i][j][s] * model.cbGetNodeRel(model._varsX[j][s])

            rhs += ATimesAi0[i][j1][s] * model.cbGetNodeRel(model._varsX[j1][s])

        rhs += 2 * attractionArray[i][j2][0] * attractionArray[i][j1][0]

    
    lhs =  part1 + part2 - part3 - rhs

    # Checks if constrained is violated
    if lhs >= 0.0001:
        return True
    else:
        return True

# Method which resolves the model with new model settings
def resolve(settings: ModelSettings):
    # Make model settings accessible 
    global modelSettings
    modelSettings = settings
    #model.setParam('Cuts',0)
    model.reset()
    model._cutsNr = [0 for cut in range(5)]
    model._cutsNr[0] = [0 for mcCut in range(4)]
    model._rootNodeIteration = 0
    model._timeInCallback = 0

    # Add McKormick inequalities for resolve
    startTime = time.time()

    if modelSettings.mcCormickIndividual[0]:
        model.addConstrs((z[i,j,s] <= 1/(Ai0[i]+attractionArray[i][j][s])*x[j,s] for j in range(products) for s in range(priceLevels) for i in range(segments)),"McCormick1")

    # If a cut 2 is used in callback don't add it beforehand
    if modelSettings.mcCormickIndividual[1]:
        model.addConstrs((z[i,j,s] >= yLFO[1][i][j][s] * x[j,s] for j in range(products) for s in range(priceLevels) for i in range(segments)),"McCormick2")

    # If a cut 3 is used in callback don't add it beforehand
    if modelSettings.mcCormickIndividual[2]:
        model.addConstrs((z[i,j,s] <= y[i] - yLFO[0][i][j][s] * (1 - x[j,s]) for j in range(products) for s in range(priceLevels) for i in range(segments)),"McCormick3")

    if modelSettings.mcCormickIndividual[3]:
        model.addConstrs((z[i,j,s] >= y[i]-(1/Ai0[i])*(1-x[j,s]) for j in range(products) for s in range(priceLevels) for i in range(segments)),"McCormick4")

    print('Loading McCormick after:',time.time() - startTime)

    return solveAmpl()

# precalculates values for the callback function and propares the model adjustments
def prepareCallback(model):
    startTime = time.time()

    # Pass data into the callback function
    model._rootNode = True
    model._rootNodeIteration = 0
    model._vars = model.getVars()
    model._varsXAll = model._vars[0 : products*priceLevels]
    model._varsY = model._vars[products*priceLevels : products*priceLevels+segments]
    model._varsZAll = model._vars[products*priceLevels+segments : products*priceLevels+segments + products*priceLevels*segments]
    model._varsW = model._vars[ products*priceLevels+segments + products*priceLevels*segments : products*priceLevels+segments + products*priceLevels*segments + segments]
    model._varsX = [model._vars[j*priceLevels : (j+1)*priceLevels] for j in range(products)]
    model._varsZ = [[model._vars[products*priceLevels+segments + (j + i * products) * priceLevels: products*priceLevels+segments + +(j + i * products + 1) * priceLevels] for j in range(products)] for i in range(segments)]

    # Set lazy constraint parameter to 1 as else it would not work
    model.setParam('LazyConstraints', 1)

    # Precalculate values for faster execution
    global ATimesAPlusAi0
    global APlusAi0
    global ATimesAi0
    global A2PlusAi0
    global ATimesAi0TimesAi0PlusA
    global yLFOInverse
    global yUFOInverse
    global yLInverse
    global APlusAi0Inverse
    global Ai0Inverse
    global part3ListCut4
    global part3ListCut5
    global mcKormickSet
    global mcKormickSetProducts
    global prop3Set
    global prop3SetProduct
    global highestAttraction

    part3ListCut5 = [[0 for s in range(priceLevels)] for j in range(products)]
    part3ListCut4 = [[0 for s in range(priceLevels)] for j in range(products)]
    APlusAi0 = [[[attractionArray[i][j][s] + Ai0[i] for s in range(priceLevels)] for j in range(products)] for i in range(segments)]
    A2PlusAi0 = [[[attractionArray[i][j][s]*2 + Ai0[i] for s in range(priceLevels)] for j in range(products)] for i in range(segments)]
    ATimesAPlusAi0 = [[[attractionArray[i][j][s] * (attractionArray[i][j][s] + Ai0[i]) for s in range(priceLevels)] for j in range(products)] for i in range(segments)]
    ATimesAi0 = [[[(attractionArray[i][j][s] * Ai0[i]) for s in range(priceLevels)] for j in range(products)] for i in range(segments)]
    ATimesAi0TimesAi0PlusA = [[[attractionArray[i][j][s] * Ai0[i] *(attractionArray[i][j][s] + Ai0[i]) for s in range(priceLevels)] for j in range(products)] for i in range(segments)]
    yLFOInverse = [[[[1/yLFO[b][i][j][s] for s in range(priceLevels)] for j in range(
            products)] for i in range(segments)] for b in range(2)]
    yUFOInverse = [[[[1/yUFO[b][i][j][s] for s in range(priceLevels)] for j in range(
            products)] for i in range(segments)] for b in range(2)]
    yLInverse = [1/yL[i] for i in range(segments)]
    Ai0Inverse = [1/Ai0[i] for i in range(segments)]
    APlusAi0Inverse = [[[1/(attractionArray[i][j][s] + Ai0[i]) for s in range(priceLevels)] for j in range(products)] for i in range(segments)]
    mcKormickSet = [[(i,j,s) for s in range(priceLevels) for j in range(products) for i in range(segments)] for mcCut in range(4)]
    mcKormickSetProducts = [[[s for s in range(priceLevels)] for j in range(products)] for mcCut in range(4)]
    prop3Set = [[[i for i in range(segments)] for s in range(priceLevels)] for j in range(products)] 
    prop3SetProduct = [[s for s in range(priceLevels)] for j in range(products)] 
    highestAttraction = [[max(attractionArray[i][j]) for j in range(products)] for i in range(segments)]

    # Print loading time
    print('Loading callback preparation function:',time.time() - startTime)
        
# Method to solve the method
def solveAmpl():    
    # Add Callback
    global solverName
    global startTime
    solverName = 'conicCut'
    startTime = time.time()
    if modelSettings.useCallback:
        solverName = 'conicCut+Callback'
        print(modelSettings.__dict__)
        prepareCallback(model)
        model.optimize(myCallback)
    else:
        model.optimize()

    #print(model.getVars())
    finalTime = time.time() - startTime

    # Output
    geneOffering = []
    print("\n Final time=", finalTime, 'with gap', model.MIPGap)
    print('Nr of cuts:', model._cutsNr)
    numberOfProducts = 0
    if model.status == GRB.OPTIMAL:
        print('\nObjective: %g' % model.ObjVal)
        for j in range(products):
            for s in range(priceLevels):
                if x[j,s].X > 0.0001:
                    geneOffering.append((j,s))
                    print('%s %g' % ((j,s)), x[j,s].X)
                    numberOfProducts += 1   
    else:
        print('No solution')

    # Create results object
    result = Result(solverName = solverName, objective = model.ObjVal, time = finalTime, numberOfProducts = numberOfProducts)
    result.cutMc4 = model._cutsNr[0][3]
    result.cutProp2 = model._cutsNr[1]
    result.cutProp3 = model._cutsNr[2]
    result.cutProp4 = model._cutsNr[3]
    result.addCallbackTime(model._timeInCallback)
    result.mipGap = model.MIPGap
    result.nodes = model.NodeCount
    addPriceStatisticsToResult(result,geneOffering)
    print(result.__dict__, '\n')
    #print(maxPrice)
    #print('geneOffering', geneOffering)
    #print(evaluatePrint(geneOffering))
    #evaluateModelFunction(geneOffering)

    return result

def addPriceStatisticsToResult(result: Result, geneOffering: list):
    averagePrice = 0
    weightedPrice = 0
    if model.status == GRB.OPTIMAL and result.numberOfProducts > 0:
        # Calculating the average price
        for (j,s) in geneOffering:
            averagePrice += priceList[j][s]
        averagePrice = averagePrice/result.numberOfProducts

        # Calculating the sum of all attraction values * x
        sumAtr = [0 for i in range(segments)] 
        for i in range(segments):
            for (j,s) in geneOffering:
                sumAtr[i] = sumAtr[i] + attractionArray[i][j][s]

        # Calculating the weighted price sum price * x * product objective contribution
        productObjectiveList = []
        for (j,s) in geneOffering:
            productObjective = 0
            for i in range(segments):
                productObjective += (omega[i] * attractionArray[i][j][s] * (priceList[j][s] -  cost[j]))/(Ai0[i] + sumAtr[i])
            productObjectiveList.append(productObjective)
            weightedPrice += priceList[j][s]*productObjective/result.objective

    result.averagePrice = averagePrice
    result.weightedPrice = weightedPrice

# Method to evaluate a offering list
def evaluateModelFunction(geneOffering: list):
    print()
    print('evalFunction')

    sumAtr = [0 for i in range(segments)] 
    for i in range(segments):
        for (j,s) in geneOffering:
            sumAtr[i] = sumAtr[i] + attractionArray[i][j][s]

    yVal = [0 for i in range(segments)]
    for i in range(segments):
        yVal[i] = 1/(sumAtr[i] + Ai0[i])
        print("y[i].X,sumAtr[i],Ai0[i]",y[i].X,sumAtr[i],Ai0[i])
        print("w[i].X,1/w[i].X",w[i].X,1/w[i].X)

    print(yVal)

# Evaluation function
def evaluatePrint(geneOffering: list):

    sumAtr = [0 for i in range(segments)] 
    # Code for ... functionc
    for i in range(segments):
        for (j,s) in geneOffering:
            sumAtr[i] = sumAtr[i] + attractionArray[i][j][s]
            print(j,s,sumAtr)

    print('obj')
    objective = 0
    for i in range(segments):
        for (j,s) in geneOffering:
            objective += (omega[i] * attractionArray[i][j][s] * (priceList[j][s] -  cost[j]))/(Ai0[i] + sumAtr[i])
            print(j,s,objective)
    return(objective)

# Initializes solution procedure
def initializeVariables(input: input):
    # Initialize all variables as global
    global weight
    global segments 
    global products 
    global priceLevels
    global cardinality
    global Ai0
    global omega
    global attractionArray
    global yLFO
    global yUFO
    global quasiProducts
    global cost
    global yL
    global yU
    global priceList
    global maxPrice

    # Set data
    weight = input.weight
    cost = input.cost
    segments = input.segments
    products = input.products
    priceLevels = input.priceLevels
    maxPrice = input.priceLevels
    cardinality = input.cardinality
    Ai0 = input.Ai0
    omega = input.omega
    attractionArray = input.attractionArray
    yLFO = input.yLFO
    yUFO = input.yUFO
    quasiProducts = products * priceLevels
    yL = input.yL
    yU = input.yU

    #Scale omega
    totalSize = 0
    print('old omega', omega)
    for i in range(segments):
        totalSize += omega[i] 
    for i in range(segments):
        omega[i] = omega[i]/totalSize
    print('new omega', omega)
    # Create prices if not provided
    if not hasattr(input, 'priceList'):
        priceList = [[s+1 for s in range(priceLevels)] for j in range(products)]
    else:
        priceList = input.priceList
        maxPrice = -100
        for j in priceList:
            if maxPrice < max(j):
                maxPrice = max(j)
