import math
import os
import numpy as np
import pandas as pd
import amplpy
import random
import itertools
from datetime import datetime as dt
import copy

# Class to retrieve an input instance
class Input:

    # Input parameters
    random.seed(1)  # Seed used

    # Returns the now relevant input parameters
    def get(self):
        return Input.getRandomFromPLDStructure(self, segments=5, priceLevels=10, cardinality=20, attributeUtilityRange=0.2, betaRange=1.5, attributes=3, attributeLevels=4, outsideOptionRange = 1, costRange = 0.05, equalWeight = True)
        #return Input.getRandomExample(self, segments = 5, products = 25, priceLevels = 25, cardinality = 10, baseUtilityRange = 8, betaRange = 10, outsideOptionRange = 10, costRange = 3, equalWeight = True)

            
    # Creates a random input product set based on PLD structure
    def getRandomFromPLDStructure(self, segments: int, priceLevels: int, cardinality: int, attributeUtilityRange: float, betaRange: float, attributes: int, attributeLevels: int, outsideOptionRange: float, costRange: float, equalWeight: bool):
        self.segments = segments
        self.attributeUtilityRange = attributeUtilityRange
        self.betaRange = betaRange
        self.outsideOptionRange = outsideOptionRange
        self.products = attributeLevels ** attributes
        print('The number of products:', self.products,
              'with priceLevels:', priceLevels)
        self.priceLevels = priceLevels
        self.cardinality = cardinality
        self.repetition = -1
        self.priceList = [[10*(s+1)/self.priceLevels for s in range(self.priceLevels)] for j in range(self.products)]
        self.attributeUtility = [[Input.createAttributeUtility(
            self, attributeLevels, attributeUtilityRange) for l in range(attributes)] for i in range(segments)]
        self.beta = [[random.random()*betaRange for j in range(self.products)]
                     for i in range(segments)]
        self.Ai0 = [random.random()*outsideOptionRange for i in range(segments)]
        self.omega = [random.random() for i in range(segments)]
        dummy = sum(self.omega)
        self.omega = [self.omega[i]/dummy for i in range(segments)]
        self.weight = [random.random() for j in range(self.products)]
        if equalWeight:
            self.weight = [1 for j in range(self.products)]
        self.locations = self.calcMaxLocations(self.weight, cardinality)
        self.yL = [0.000000001 for i in range(segments)]
        self.yU = [1/self.Ai0[i] for i in range(segments)]
        self.yLFO = [[[[0.000000001 for s in range(priceLevels)] for j in range(
            self.products)] for i in range(segments)] for b in range(2)]
        self.yUFO = [[[[1/self.Ai0[i] for s in range(priceLevels)] for j in range(
            self.products)] for i in range(segments)] for b in range(2)]
        self.attributes = attributes
        self.attributeLevels = attributeLevels
        self.repetition = -1
        self.name = 'single'

        # Create costs per attribute and level
        costAttribute = [[] for l in range(attributes)]
        for l in range(attributes):
            costDummy = 0
            for k in range(attributeLevels):
                costDummy += random.random() * costRange
                costAttribute[l].append(costDummy)

        self.cost = []


        # Create the attraction for each product price combination
        attractionArray = []
        # Create K L mapping
        klMapping = [[[] for l in range(attributeLevels)]
                     for k in range(attributes)]

        # Create a j k mapping to l
        levelMapping = [[[] for k in range(attributes)]
                        for j in range(self.products)]

        j = 0  # product index
        # Create a two dimensional list to reflect the attribute levels indexes and create each attribute combination through the cartesian product
        attributeList = [
            [l for l in range(attributeLevels)] for k in range(attributes)]
        for attributeCombination in itertools.product(*attributeList):
           
            # Calculate costs
            productCost = 0
            for k, attLevelIndex in enumerate(attributeCombination):
                productCost += costAttribute[k][attLevelIndex]

            self.cost.append(productCost)

            for i in range(segments):
                # Calculate base utility of each attribute combination
                baseUtility = 0
                productCost = 0
                for k, attLevelIndex in enumerate(attributeCombination):
                    baseUtility += self.attributeUtility[i][k][attLevelIndex]
                    

                # Calculate attraction from base utility and price
                for s in range(priceLevels):
                    attraction = math.exp(baseUtility-self.beta[i][j]*self.priceList[j][s])
                    attractionArray.append(
                        [i, j, s, attributeCombination, attraction])

            # Add this product to the klMapping variable
            for k, attLevelIndex in enumerate(attributeCombination):
                klMapping[k][attLevelIndex].append(j)
                levelMapping[j][k] = [attLevelIndex]

            # Increase product index
            j += 1

        self.klMapping = klMapping
        self.levelMapping = levelMapping

        self.attractionArray = [[[0 for s in range(self.priceLevels)] for j in range(self.products)] for i in range(self.segments)]
        for att in attractionArray:
            self.attractionArray[int(att[0])][int(att[1])][int(att[2])] = att[4]




        # Create a amplpy DataFrame
        self.attraction = amplpy.DataFrame(('I', 'J', 'S'), 'A')

        numpyArray = np.asarray(self.attractionArray)
        I, J, K = numpyArray.shape

        i_col = np.repeat(np.arange(I), J*K)
        j_col = np.tile(np.repeat(np.arange(J), K), I)
        k_col = np.tile(np.arange(K), I*J)
        v_col = numpyArray.ravel(order="C")

        self.attraction.setColumn('I',i_col)
        self.attraction.setColumn('J',j_col)
        self.attraction.setColumn('S',k_col)
        self.attraction.setColumn('A',v_col)
        
        # Return this input object
        return self

    # Turns this object into a dict
    def toDict(self):
        self.attraction = self.attraction.toDict()
        return self.__dict__

    # Turns a dict into an object
    def __fromDict__(self, dict: dict):
        self.weight = dict['weight']
        self.segments = dict['segments']
        self.products = dict['products']
        self.locations = dict['locations']
        self.priceLevels = dict['priceLevels']
        self.cardinality = dict['cardinality']
        self.Ai0 = dict['Ai0']
        self.omega = dict['omega']
        if 'attributeLevels' in dict:
            self.attributeLevels = dict['attributeLevels']
        if 'attributes' in dict:
            self.attributes = dict['attributes']
        if 'klMapping' in dict:
            self.klMapping = dict['klMapping']
        if 'levelMapping' in dict:
            self.levelMapping = dict['levelMapping']
        if 'attributeListLength' in dict:
            self.attributeListLength = dict['attributeListLength']
        self.yL = dict['yL']
        self.yU = dict['yU']
        self.yLFO = dict['yLFO']
        self.yUFO = dict['yUFO']
        self.attraction = amplpy.DataFrame.fromDict(dict['attraction'], index_names=('I', 'J', 'S'),column_names='A')
        self.name = dict['name']
        if 'repetition' in dict:
            self.repetition = dict['repetition']
        else:
            self.repetition = -1
        self.betaRange = dict['betaRange']
        self.outsideOptionRange = dict['outsideOptionRange']
        self.attributeUtilityRange = dict['attributeUtilityRange']
        self.cost = dict['cost']
        self.attractionArray = dict['attractionArray']
        if 'priceList' in dict:
            self.priceList = dict['priceList']

        return self
       
    # Returns increasing values of random utility values, which can be assigned to attributeLevels
    def createAttributeUtility(self, attributeLevels, attributeUtilityRange):
        utilities = []
        value = 0
        for l in range(attributeLevels):
            value += random.random() * attributeUtilityRange
            utilities.append(value)
        return utilities

    # Creates a random input product set
    def getRandomExample(self, segments: int, products: int, priceLevels: int, cardinality: int, baseUtilityRange: float, betaRange: float, outsideOptionRange: float, costRange: float, equalWeight: bool):
        self.segments = segments
        self.products = products
        self.priceLevels = priceLevels
        self.attributeUtilityRange = -1
        self.betaRange = betaRange
        self.baseUtilityRange = baseUtilityRange
        self.outsideOptionRange = outsideOptionRange
        print('The number of products:', self.products,
              'with priceLevels:', priceLevels)
        self.cardinality = cardinality
        self.priceList = [[10*(s+1)/self.priceLevels for s in range(self.priceLevels)] for j in range(self.products)]
        self.baseUtility = [
            [random.random()*baseUtilityRange for j in range(products)] for i in range(segments)]
        self.beta = [[random.random()*betaRange for j in range(products)]
                     for i in range(segments)]
        self.Ai0 = [random.random()*outsideOptionRange for i in range(segments)]
        self.omega = [random.random() for i in range(segments)]
        dummy = sum(self.omega)
        self.omega = [self.omega[i]/dummy for i in range(segments)]
        self.weight = [random.random() for j in range(products)]
        if equalWeight:
            self.weight = [1 for j in range(products)]
        self.locations = self.calcMaxLocations(self.weight, cardinality)
        self.yL = [0.000000001 for i in range(segments)]
        self.yU = [1/self.Ai0[i] for i in range(segments)]
        self.yLFO = [[[[0.000000001 for s in range(priceLevels)] for j in range(self.products)] for i in range(segments)] for b in range(2)]
        self.yUFO = [[[[1/self.Ai0[i] for s in range(priceLevels)] for j in range(self.products)] for i in range(segments)] for b in range(2)]
        self.repetition = -1
        self.name = 'single'
        self.cost = [random.random()*costRange for j in range(products)]

        self.attractionArray = [[[math.exp(self.baseUtility[i][j]-self.beta[i][j]*self.priceList[j][s]) for s in range(priceLevels)] for j in range(products)] for i in range(segments)]
        self.attraction = amplpy.DataFrame(('I', 'J', 'S'), 'A')
        self.attraction.setValues({
            (i, j, s): self.attractionArray[i][j][s]
            for i in range(segments)
            for j in range(products)
            for s in range(priceLevels)
        })
        self.attributeLevels = []
        self.attributes = []
        self.klMapping = []
        self.levelMapping = []

        # Return this input object
        return self
    

    # Defining the number of locations based on cardinality and wight
    def calcMaxLocations(self, weight: list, cardinality):
        weightCopy = weight.copy()
        weightCopy.sort()

        # Summation is the weight summed in order, amount are the number of products
        summation = 0
        amount = 0
        for w in weightCopy:
            amount += 1
            summation += w
            if summation > cardinality :
                print('max number of products are', amount-1)
                return amount - 1
            if amount == self.products:
                print('max number of products are', amount)
                return amount
        return 0

    # Updates upper and lower bounds of y
    def updateYBound(self):
        # Load data into model
        Input.loadAmplYBound(self)

        # Set solver
        ampl.setOption('solver', 'gurobi')

        # Change the problem to a maximization problem, the objective value needs to be multiplied by -1
        ampl.getParameter('minProblem').setValues([-1])
        for i in range(self.segments):
            ampl.getParameter('curSeg').setValues([i])
            ampl.solve()
            self.yL[i] = -1/ampl.getObjective('fMinAndMax').value()

            # Add solution to yLFO and
            decisionVariables = pd.DataFrame(ampl.getVariable('x').getValues(), columns=['j', 's', 'x'])
            for row in decisionVariables.iterrows():
                self.yLFO[int(row[1][2])][i][int(row[1][0])
                                             ][int(row[1][1])] = self.yL[i]

        # Solve the minimization problem for each segment, first set minProblem = 1 to ensure it is minimized
        ampl.getParameter('yL').setValues(self.yL)
        ampl.getParameter('minProblem').setValues([1])
        for i in range(self.segments):
            ampl.getParameter('curSeg').setValues([i])
            ampl.solve()
            self.yU[i] = 1/ampl.getObjective('fMinAndMax').value()

            # Add solution to yUFO and
            decisionVariables = pd.DataFrame(ampl.getVariable(
                'x').getValues(), columns=['j', 's', 'x'])
            for row in decisionVariables.iterrows():
                self.yUFO[int(row[1][2])][i][int(row[1][0])
                                             ][int(row[1][1])] = self.yU[i]

    # Loads all data necessary to update lower bounds of the instance
    def loadAmplYBound(self):
        # Create ampl instance and read model
        global ampl
        ampl = amplpy.AMPL()
        ampl.read(os.path.join(os.path.realpath(''),
                               'amplModels','other', 'yBounds.mod'))

        # Load all constants that are fixed
        ampl.getSet('J').setValues([j for j in range(self.products)])
        ampl.getSet('I').setValues([i for i in range(self.segments)])
        ampl.getSet('Pj').setValues([s for s in range(self.priceLevels)])

        # Create prices if not provided
        if not hasattr(self, 'priceList'):
            self.priceList = [[s+1 for s in range(self.priceLevels)] for j in range(self.products)]

        # Set parameters
        ampl.getParameter('p').setValues(
            {(j, s): self.priceList[j][s] for s in range(self.priceLevels) for j in range(self.products)})
        ampl.getParameter('cardinality').setValues([self.cardinality])
        ampl.getParameter('Ai0').setValues(self.Ai0)
        ampl.getParameter('omega').setValues(self.omega)
        ampl.getParameter('weight').setValues(self.weight)
        ampl.getParameter('yL').setValues(self.yL)
        ampl.getParameter('yU').setValues(self.yU)
        ampl.getParameter('preSetToZero').setValues(
            {(j, s): 0 for s in range(self.priceLevels) for j in range(self.products)})
        ampl.getParameter('preSetToOne').setValues(
            {(j, s): 0 for s in range(self.priceLevels) for j in range(self.products)})

        ampl.setData(self.attraction)

    # Method that calculates first order bounds of y fast
    def addFOConditionalYBoundSimple(self):
        print(dt.now(), 'start addFOConditionalYBound simple version')

        # Generate attraction list, array and highest Attraction
        attractionList = self.attraction.toList()
        attractionArray = [[[0 for s in range(self.priceLevels)] for j in range(self.products)] for i in range(self.segments)]
        highestAttraction = [[] for i in range(self.segments)]

        # Create an array out of attraction as a copy
        for row in attractionList:
            attractionArray[int(row[0])][int(row[1])][int(row[2])] = row[3]

        #sort all values in the copy
        for i in range(self.segments):
            for j in range(self.products):
                attractionArray[i][j].sort(reverse= True)
                highestAttraction[i].append(attractionArray[i][j][0])

        # Sort
        for i in range(self.segments):
            highestAttraction[i].sort(reverse= True)

        counter = 0
               
        # For x = 0 and for x = 1
        for b in range(2):
            for i in range(self.segments):
              # Loop product and price
                for j in range(self.products):
                    for s in range(self.priceLevels):

                        # First update remaining yLFO values
                        if self.yLFO[b][i][j][s] == 0.000000001:

                            # Distinction between x_{js} values forced to 0 (=b) or 1 (=b)
                            if b == 0:
                                sumAttraction = self.Ai0[i]
                                for count in range(self.locations):

                                    if highestAttraction[i][count] != attractionArray[i][j][s]:
                                        sumAttraction += highestAttraction[i][count]
                                    else:
                                        if self.priceLevels == 1:
                                            sumAttraction += highestAttraction[i][min(self.locations, len(highestAttraction[i])-1)]
                                        else:
                                            if highestAttraction[i][min(self.locations, len(highestAttraction[i])-1)] > attractionArray[i][j][s+1]:
                                                sumAttraction += highestAttraction[i][min(self.locations, len(highestAttraction[i])-1)]
                                            else: 
                                                sumAttraction += attractionArray[i][j][s+1]

                                self.yLFO[b][i][j][s] = 1 / sumAttraction

                            if b == 1:
                                sumAttraction = self.Ai0[i] + attractionArray[i][j][s]
                                for count in range(self.locations-1):
                                    if highestAttraction[i][count] != attractionArray[i][j][0]:
                                        sumAttraction += highestAttraction[i][count]
                                    else:
                                        sumAttraction += highestAttraction[i][self.locations-1]

                                self.yLFO[b][i][j][s] = 1 / sumAttraction

                        # Update remaining yUFO values
                        if self.yUFO[b][i][j][s] == 1/self.Ai0[i]:

                            # Use maximization for the minimal y value as 1/y = fMinAndMax
                            ampl.getParameter('minProblem').setValues([1])

                            # Distinction between x_{js} values forced to 0 (=b) or 1 (=b)
                            #if b == 0: do nothing


                            if b == 1:
                                self.yUFO[b][i][j][s] = 1/(self.Ai0[i]+attractionArray[i][j][s])

                        
                        # Fail save: check if values are correct:
                        if self.yUFO[b][i][j][s] < self.yLFO[b][i][j][s]:
                            print('Upper bound < lower bound at first order condition:', b, i, j, s, self.yUFO[b][i][j][s], self.yLFO[b][i][j][s])
                            exit()

                    # Print counter
                    counter += 1
                    if counter % 250 == 0:
                        print(dt.now(), (counter*4), ' solver calls in addFOConditionalYBound')

    # Creates first order yBounds for x_{js} = 0 and x_{js} = 1 and set in to yLFO and yUFO
    def addFOConditionalYBound(self):
        """
        Update all other remaining values for yLFO and yUFO
        b describes if the product price combination is forced to be 0 or 1
        Loop over all dimensions, (x_{js} = 0 or x_{js} = 1), segments , products and price
        Only half of the values must be calculated as the other half is set during updateYBounds 
        as f_{i|x_{js}=x_{js}^*} would remain the same objective value
        """
        # Counter for iterations
        counter = 0
        print(dt.now(), 'start addFOConditionalYBound')

        # For x = 0 and for x = 1
        for b in range(2):
            for i in range(self.segments):

                # Set the current segment to i
                ampl.getParameter('curSeg').setValues([i])

                # Loop product and price
                for j in range(self.products):
                    for s in range(self.priceLevels):

                        # First update remaining yLFO values
                        if self.yLFO[b][i][j][s] == 0.000000001:

                            # Use maximization for the minimal y value as 1/y = fMinAndMax
                            ampl.getParameter('minProblem').setValues([-1])

                            # Distinction between x_{js} values forced to 0 (=b) or 1 (=b)
                            if b == 0:
                                # Set, solve, reset model and save result
                                ampl.getParameter(
                                    'preSetToZero').setValues({(j, s): 1})
                                ampl.solve()
                                ampl.getParameter(
                                    'preSetToZero').setValues({(j, s): 0})
                                self.yLFO[b][i][j][s] = -1 / \
                                    ampl.getObjective('fMinAndMax').value()

                            if b == 1:
                                # Set, solve, reset model and save result
                                ampl.getParameter(
                                    'preSetToOne').setValues({(j, s): 1})
                                ampl.solve()
                                ampl.getParameter(
                                    'preSetToOne').setValues({(j, s): 0})
                                self.yLFO[b][i][j][s] = -1 / \
                                    ampl.getObjective('fMinAndMax').value()

                        # Update remaining yUFO values
                        if self.yUFO[b][i][j][s] == 1/self.Ai0[i]:

                            # Use maximization for the minimal y value as 1/y = fMinAndMax
                            ampl.getParameter('minProblem').setValues([1])

                            # Distinction between x_{js} values forced to 0 (=b) or 1 (=b)
                            if b == 0:
                                # Set, solve, reset model and save result
                                ampl.getParameter(
                                    'preSetToZero').setValues({(j, s): 1})
                                ampl.solve()
                                ampl.getParameter(
                                    'preSetToZero').setValues({(j, s): 0})
                                self.yUFO[b][i][j][s] = 1 / \
                                    ampl.getObjective('fMinAndMax').value()

                            if b == 1:
                                # Set, solve, reset model and save result
                                ampl.getParameter(
                                    'preSetToOne').setValues({(j, s): 1})
                                ampl.solve()
                                ampl.getParameter(
                                    'preSetToOne').setValues({(j, s): 0})
                                self.yUFO[b][i][j][s] = 1 / \
                                    ampl.getObjective('fMinAndMax').value()
                        
                        # Fail save: check if values are correct:
                        if self.yUFO[b][i][j][s] < self.yLFO[b][i][j][s]:
                            print(
                                'Upper bound < lower bound at first order condition:', b, i, j, s, self.yUFO[b][i][j][s], self.yLFO[b][i][j][s])

                            exit()

                    # Print counter
                    counter += 1
                    if counter % 250 == 0:
                        print(dt.now(), (counter*4), ' solver calls in addFOConditionalYBound')
                    
    # A short to string method
    def toStringShort(self):
        return 'segments =' + str(self.segments) + ' priceLevels =' + str(self.priceLevels) + ' cardinality = ' + str(self.cardinality) + ' products = ' + str(self.products) + ' betaRange = ' + str(self.betaRange) + ' outsideOptionRange = ' + str(self.outsideOptionRange) + ' attributeUtilityRange = '+ str(self.attributeUtilityRange) + ' weights = ' + str(self.weight[0])

    # Returns a printable copy
    def getPrintableCopy(self):
        printableInput = copy.deepcopy(self)
        printableInput.attraction = None
        printableInput.weight = printableInput.weight[0]
        printableInput.Ai0 = printableInput.Ai0[0]
        printableInput.attractionArray = printableInput.attractionArray[0][0][0]
        printableInput.attributeUtility = printableInput.attributeUtility[0]
        printableInput.attributeUtility 
        printableInput.yL = printableInput.yL[0][0][0]
        printableInput.yU = printableInput.yU[0][0][0]
        printableInput.yLFO = printableInput.yLFO[0][0][0][0]
        printableInput.yUFO = printableInput.yUFO[0][0][0][0]
        return printableInput
    
    # Create an input file where a subset of products are included
    def createInputWithLessProducts(self, productList):
        input = Input()
        input.productList = productList
        weight = [self.weight[int(j)] for j in productList]
        input.weight = weight
        cost = [self.cost[int(j)] for j in productList]
        input.cost = cost
        attractionArray =  [[[self.attractionArray[i][int(j)][s]
                                  for s in range(self.priceLevels)] for j in productList] for i in range(self.segments)]
        input.attractionArray = attractionArray
        input.products = len(productList)
        input.segments = self.segments
        input.priceLevels = self.priceLevels
        input.attraction = amplpy.DataFrame(('I', 'J', 'S'), 'A')
        input.attraction.setValues({
            (i, j, s): self.attractionArray[i][j][s]
            for i in range(input.segments)
            for j in range(input.products)
            for s in range(input.priceLevels)
        })
        input.yL = [0.000000001 for i in range(input.segments)]
        input.yU = [1/self.Ai0[i] for i in range(input.segments)]
        input.yLFO = [[[[0.000000001 for s in range(input.priceLevels)] for j in range(
            input.products)] for i in range(input.segments)] for b in range(2)]
        input.yUFO = [[[[1/self.Ai0[i] for s in range(input.priceLevels)] for j in range(
            input.products)] for i in range(input.segments)] for b in range(2)]
        input.Ai0 = self.Ai0
        input.locations = self.locations
        input.cardinality = self.cardinality
        input.omega = self.omega

        return input


