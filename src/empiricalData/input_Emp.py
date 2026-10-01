import copy
import itertools
import math
from input import Input
import amplpy
import pandas as pd
import numpy

# Input from paper Ref 1
def getInputPaetz2019():
    utilIKL = [[[-0.167,-0.018,0.184],[-0.186,0.033,0.153],[-0.121,-0.006,0.126],[-0.164,0.114,0.05],[-0.089,0.049,0.04],[-0.072,-0.079,0.15],[-0.278,-0.032,0.105,0.164,0.042],[0.038,-0.104,-0.11,0.057,0.173,0.061]],[[-0.385,-0.062,0.323],[-0.27,0.051,0.218],[-0.107,-0.072,0.179],[-0.142,-0.051,0.193],[-0.111,-0.018,0.13],[-0.463,-0.024,0.487],[-2.002,-0.69,0.29,0.803,1.599],[-0.052,-0.19,-0.002,-0.032,0.061,0.214]],[[-1.939,0.432,1.507],[-1.157,0.294,0.863],[-0.36,0.013,0.347],[-0.257,0.019,0.238],[-0.203,0.02,0.183],[-0.103,-0.054,0.157],[-0.643,-0.154,0.131,0.333,0.332],[0.01,-0.006,-0.314,0.077,0.148,0.085]],[[-0.51,0.171,0.339],[-0.29,0.042,0.248],[-0.15,0.052,0.098],[-0.197,0.035,0.161],[-0.194,-0.005,0.198],[-0.107,-0.019,0.126],[-0.614,-0.14,0.082,0.357,0.314],[-0.229,-0.224,-0.477,-0.158,0.658,0.431]],[[-0.182,0.061,0.121],[-0.195,0.033,0.162],[-0.14,0.028,0.112],[-0.187,0.11,0.076],[-0.096,0.015,0.081],[-0.278,0.009,0.269],[-0.845,-0.309,0.165,0.527,0.462],[0.151,0.05,-0.083,-0.077,-0.027,-0.015]]]

    utilPrice = [[-0.317,0.065,0.189,0.075,-0.011],[0.221,0.227,0.173,0.027,-0.648],[0.045,0.144,0.004,0.06,-0.254],[0.255,0.171,0.096,-0.2,-0.322],[1.736,1.161,0.379,-0.644,-2.632]]

    utilOutside = [0,0,0,0,0]

    name = "Paetz2019" 

    prices = [38,42,47,52,56]

    omega = [0.186,0.211,0.236,0.145,0.172]

    return get(utilIKL, utilPrice, utilOutside, prices, omega, name)

# Create 
def get(utilIKL, utilPrice, utilOutside, prices, omega, name, costPerAttribute = None, cardinality = None):
    input = Input()
    input.maxPrice = max(prices)
    input.priceLevels = len(prices)
    input.segments = len(utilOutside)
    input.products = 1
    attributeListLength = []
    for i in utilIKL:
        for l in i:
            input.products *= len(l)
            attributeListLength.append(len(l))
        break
    input.priceList = [[prices[s] for s in range(len(prices))] for j in range(input.products)]
    input.omega = omega
    print('instance has', input.products, 'products')

    # Choices
    if cardinality == None:
        input.cardinality = input.products
    else:
        input.cardinality = cardinality
    input.weight = [1 for j in range(input.products)]


    # Attraction
    input.Ai0 = [math.exp(utilOutside[i]) for i in range(input.segments)]
    input.attributes = len(attributeListLength)
    input.attributeLevels = max(attributeListLength) # maximal attribute levels
    input.attributeListLength = attributeListLength

    # Create K L mapping
    input.klMapping = [[[] for l in range(input.attributeLevels)]
                    for k in range(input.attributes)]

    # Create a j k mapping to l
    input.levelMapping = [[[] for k in range(input.attributes)]
                    for j in range(input.products)]

    input.cost = [0 for j in range(input.products)]
    # Create a two dimensional list to reflect the attribute levels indexes and create each attribute combination through the cartesian product
    j = 0
    input.attractionArray = []
    attributeList = [[l for l in range(attributeListLength[k])] for k in range(input.attributes)]
    for attributeCombination in itertools.product(*attributeList):

        # Update costs
        if costPerAttribute != None:
            for k, attLevelIndex in enumerate(attributeCombination):
                input.cost[j] += costPerAttribute[k][attLevelIndex]

        # Update utility
        for i in range(input.segments):
            # Calculate base utility of each attribute combination
            baseUtility = 0
            for k, attLevelIndex in enumerate(attributeCombination):
                baseUtility += utilIKL[i][k][attLevelIndex]
                
            # Calculate attraction from base utility and price
            for s in range(input.priceLevels):
                attraction = math.exp(baseUtility + utilPrice[i][s])
                input.attractionArray.append(
                    [i, j, s, attributeCombination, attraction])

        # Add this product to the klMapping variable
        for k, attLevelIndex in enumerate(attributeCombination):
            input.klMapping[k][attLevelIndex].append(j)
            input.levelMapping[j][k] = [attLevelIndex]

        # Increase product index
        j += 1

        if j % 1000 == 0:
            print('create AO model, iteration', j)

    # Ampl representation
    # Rename the columns
    attractionPandas = pd.DataFrame(input.attractionArray, columns=[
        'I', 'J', 'S', 'attributes', 'A', ])
    print('pandas set set')

    # Create a amplpy DataFrame from pandas and add it
    input.attraction = amplpy.DataFrame(('I', 'J', 'S'), 'A')

    # Add row by row
    j = 0
    for index, row in attractionPandas[['I', 'J', 'S', 'A']].iterrows():
        input.attraction._addRow(row.to_list())
        # Increase product index
        j += 1

        if j % 1000 == 0:
            print('create AO model, iteration', j)


    print('attraction set')
    #input.locations = input.calcMaxLocations(input.weight, input.cardinality)
    input.locations = input.cardinality
    
    # Attraction Array
    input.attractionArray = [[[0 for s in range(input.priceLevels)] for j in range(input.products)] for i in range(input.segments)]
    for att in input.attraction.toList():
        input.attractionArray[int(att[0])][int(att[1])][int(att[2])] = att[3]
        
    print('attractionArray set')
    #Other
    input.name = name
    input.betaRange = -1
    input.outsideOptionRange = -1
    input.attributeUtilityRange = -1
    
    #Scale omega to 1
    totalSize = 0
    print('original omega', omega)
    for i in range(input.segments):
        totalSize += omega[i] 
    for i in range(input.segments):
        omega[i] = omega[i]/totalSize
    print('normalized omega', omega)

    #adjust segment size
    totalOmega = 0
    for i in range(input.segments):
        totalOmega += input.omega[i]
    
    input.omega = [input.omega[i]/totalOmega for i in range(input.segments)]

    #Update Bounds
    input.yL = [0.000000001 for i in range(input.segments)]
    input.yU = [1/input.Ai0[i] for i in range(input.segments)]
    input.yLFO = [[[[0.000000001 for s in range(input.priceLevels)] for j in range(input.products)] for i in range(input.segments)] for b in range(2)]
    input.yUFO = [[[[1/input.Ai0[i] for s in range(input.priceLevels)] for j in range(input.products)] for i in range(input.segments)] for b in range(2)]
    input.updateYBound()
    input.addFOConditionalYBoundSimple()
    return input