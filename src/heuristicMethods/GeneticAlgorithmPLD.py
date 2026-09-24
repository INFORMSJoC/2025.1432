import random
import time
import input
from modelSettings import ModelSettings
from datetime import datetime as dt
import matplotlib.pyplot as plt
import copy as cp
from operator import itemgetter


from result import Result

# Main solution method
def solve(input: input, settings: ModelSettings):
    print('Genetic Algorithm PLD', dt.now())

    # Make model settings accessible 
    global modelSettings
    modelSettings = settings

    # Update input values
    initializeVariables(input)

    # Parameter for statistics
    startTime = time.time()
    obj_list = []
    iter = 0

    # population is a list of genomes
    global population
    global bestGenome
    population = createPopulation()
    population = sorted(population, key=itemgetter(1), reverse = True)
    bestGenome = population[0]
    obj_list.append(population[0][1])

    # GA loop
    while stoppingCriterion(iter, startTime):
        # Adding all new children to the population
        selectionAndCrossover()

        # Mutate
        mutate()

        # sort population
        population = sorted(population, key=itemgetter(1), reverse = True)
        
        # Reduce the size to population length and keep track of best solution
        population = population[:int((modelSettings.populationSize) * modelSettings.sizeReduction)]

        # Add genes if some are missing
        while len(population) < modelSettings.populationSize:
            population.append(createNewGene(eva = True))

        # Update if better
        if population[0][1] > bestGenome[1]:
            bestGenome = cp.deepcopy(population[0])

        # Current iteration best objective
        obj_list.append(population[0][1])

        # Update iterations
        iter += 1
        if iter % 100 == 0:
            print('iteration:', iter, 'time:',time.time() - startTime, 'bestGenome:', bestGenome)

    # Final Time
    finalTime = time.time() - startTime

    # Show stats if required
    if modelSettings.displayResult:
        plt.plot(obj_list)
        plt.show()

    # Create Result
    print('iteration:', iter, 'time:',finalTime, 'Result:', bestGenome)
    result  = Result(numberOfProducts = len(bestGenome[0]), objective=bestGenome[1],solverName= 'GA-PLD',time = finalTime)
    result.iteration = iter
    print(result.__dict__)
    
    # Return result
    return result

# Stopping criterion returns true if it needs to stop
def stoppingCriterion(iter: int, startTime):
    # stops after max time is reached
    if modelSettings.stopAfterTime:
        return time.time() <= startTime + modelSettings.maxTimeHeuristic
    
    # stops after max iterations are reached
    if modelSettings.stopAfterIterations:
        return iter < modelSettings.iterations
    
    # stops after 100 iterations no greater relative change then maxConvergenceChange
    if modelSettings.stopAfterConvergence:
        global convergenceValue
        if (bestGenome[1] - convergenceValue)/convergenceValue > modelSettings.maxConvergenceChange:
            global convergenceIteration
            convergenceValue = bestGenome[1]
            convergenceIteration = iter
            return True
        else: 
            return iter - convergenceIteration < 100

# Function to add all new children in each iteration
def selectionAndCrossover():
    # Add modelSettings.nrOfChildsAdded children
    for j in range(0,int(modelSettings.nrOfChildsAdded/2)):
        # Select two parents (either the best two genomes, or by tournament selection, or randomly)
        parents = [tournamentSelection(population),tournamentSelection(population)]

        # Crossover
        child1, child2 = crossover(parents[0][0].copy(), parents[1][0].copy(), [random.randint(0, min(len(parents[0][0]), len(parents[1][0])) - 1)])

        # Add new children to the population
        population.append([child1,evaluate(child1)])
        population.append([child2,evaluate(child2)])

# Create population
def createPopulation():
    population = []
    for geneId in range(modelSettings.populationSize):
        population.append(createNewGene(True))
    return population

# Creates a new random gene
def createNewGene(eva: bool):
    newGene =[[],0]

    while len(newGene[0]) < cardinality:
        j = random.randint(0,products-1)
        s = random.randint(0,priceLevels-1)
        
        # Avoid offering the same products twice
        isInGene = False
        for (j2,s2) in newGene[0]:
            if j2 == j:
                isInGene = True
                break
        if not isInGene:
            newGene[0].append((j,s))
        
    # Evaluate the new gene
    if eva:
        newGene[1] = evaluate(newGene[0])

    return newGene
    
# Evaluation function
def evaluate(geneOffering: list):
    sumAtr = [0 for i in range(segments)] 
    # Code for ... functionc
    for i in range(segments):
        for k in range(0,len(geneOffering)):
            j=geneOffering[k][0]
            s=geneOffering[k][1]
            sumAtr[i] = sumAtr[i] + attractionArray[i][j][s]

    objective = 0
    for i in range(segments):
        for k in range(0,len(geneOffering)):
            j=geneOffering[k][0]
            s=geneOffering[k][1]
            objective = objective + (omega[i] * attractionArray[i][j][s] * (priceList[j][s] -  cost[j]))/(Ai0[i] + sumAtr[i])
    return(objective)

# Tournament selection code
def tournamentSelection(population: list):
    # Select two genes randomly
    parents = random.choices(
        population,
        k=2
    )

    # Draw a random number
    rnd = random.random()

    # Return the higher genome
    if  rnd > modelSettings.tournamentSelectionProbability and parents[0][1] < parents[1][1] or rnd < modelSettings.tournamentSelectionProbability and parents[0][1] > parents[1][1]:
        return parents[0]
    else:
        return parents[1]

# Creates two parents first and calls childCreation to create a child
def selection_pair(population: list):
    #weights of choosing a genome is based on its fitness function value
    parents =  random.choices(
        population,
        weights=[gene[1] for gene in population],
        k=2
    )
    return(parents)

# Creates an evaluated child from two parents 
def childCreation(parent1, parent2):
    #new= cp.deepcopy(parent1 + parent2)
    new = parent1 + parent2
    u=[]

    # nlog(n) + 2n < n²
    for i in range(0,len(new)):
        for j in range(i+1,len(new)):
            if new[i][0]==new[j][0]:
                u.append(j)

    u=set(u)
    u=list(u)
    u.sort(reverse=True)
    for i in u:
        new.pop(i)     
    random.shuffle(new)
    while len(new) > cardinality:
        del new[-1]

    return(new)

# Single point crossover
def _singleCrossover(parent1, parent2, index):
    child1 = parent1[:index] + parent2[index:]
    child2 = parent2[:index] + parent1[index:]

    # Create new product based on pld structure at product index
    product1Attribute = idToLevel[parent1[index][0]]
    product2Attribute = idToLevel[parent2[index][0]]
    split = random.randint(1,attributes)
    child1[index] = (getID(product1Attribute[:split] + product2Attribute[split:]),parent1[index][1])
    child2[index] = (getID(product2Attribute[:split] + product1Attribute[split:]),parent1[index][1])
   
    return child1, child2

# k point crossOver 
def crossover(child1, child2, kList: list):
    # For every index k in KList do a single crossover
    for j in kList:
        child1, child2 = _singleCrossover(child1, child2, j)

    
    # Check if a child is not valid
    seen = set()
    for (j,s) in child1:
        if j in seen:
            child1 = createNewGene(eva = False)[0]
            break
        else:
            seen.add(j)

    # Replicate for child 2
    seen = set()
    for (j,s) in child2:
        if j in seen:
            child2 = createNewGene(eva = False)[0]
            break
        else:
            seen.add(j)

    # return two children
    return child1, child2

# Function to mutate the population
def mutate():
    for geneID in range(modelSettings.populationSize):
        mutateGene(population[geneID])
        
# Mutation
def mutateGene(gene):
    # check if gene should be evaluated
    newEvaluate = False

    # Go over each product price combination
    for id,(j,s) in enumerate(gene[0]):
        newProduct = j

        mutatedAttributes = []
        for k in range(attributes):
            rnd = random.random()
            if rnd <= modelSettings.mutationAttribute:
                mutatedAttributes.append([k, random.randint(0,attributeListLength[k]-1)])

        # Copy attribute levels if something changes
        if len(mutatedAttributes) > 0:
            newEvaluate = True
            attributeLevel = idToLevel[id].copy()

            #Change level
            for k,l in mutatedAttributes:
                attributeLevel[k] = l

            # Get new ID
            newProduct = getID(attributeLevel)

            # No duplication
            products_present = [l[0] for l in gene[0]]
            while newProduct in products_present:
                newProduct = random.randint(0,products-1)

            # Replace the product id
            gene[0][id] = (newProduct,s)
            
        # Mutation on price level
        if random.random() < modelSettings.mutationPrice:
            # if new evaluation is required
            newEvaluate = True

            # New price
            gene[0][id] = (newProduct,random.randint(0,priceLevels-1))
                        
    # make shorter genes sometimes if cardinality is not fixed
    if not modelSettings.newProductsEqualCardinality:
        if random.uniform(0,1) < modelSettings.mutateReduceSize:
            # if new evaluation is required
            newEvaluate = True
            population.append(cp.deepcopy(gene))

    # Evaluate if necessary
    if newEvaluate:
        # Update objective
        gene[1] = evaluate(geneOffering  = gene[0])


    return(gene)

# Method that sorts two lists
def sort_list(list1, list2):
    zipped_pairs = zip(list2, list1)
    z = [x for _, x in sorted(zipped_pairs, reverse = True)]
    return z

# Returns the product id with a given pld structure
def getID(levels: list):
    id = 0
    for k,l in enumerate(levels):
        id += attributeToLevelMultiplier[k]*l
    return id

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
    global mutationProduct
    global attributeLevels
    global attributes
    global levelMapping
    global attributeToLevelMultiplier
    global idToLevel
    global convergenceValue
    global convergenceIteration
    global priceList
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
    #attraction = input.attraction
    yLFO = input.yLFO
    yUFO = input.yUFO
    quasiProducts = products * priceLevels
    attractionArray = input.attractionArray
    attributeLevels = input.attributeLevels
    attributes = input.attributes
    levelMapping = input.levelMapping
    convergenceValue = 0.00001
    convergenceIteration = 0 

    # Transforms a product in its pld structure and visa versa

    idToLevel = [[levelMapping[j][k][0] for k in range(attributes)] for j in range(products)]

    # mutation rate per product
    mutationProduct = 1 - (1 - modelSettings.mutationAttribute) ** attributes
    print('likelihood that a product is mutated', mutationProduct)
    print('likelihood that a gene is mutated', 1 - ((1-mutationProduct)**cardinality)*(1-modelSettings.mutationPrice)**cardinality)

    # For the algorithm
    global bestGenome

    # Best Genome
    bestGenome = [[], 0] # Which products to offer and objective value

    # Create prices if not provided
    if not hasattr(input, 'priceList'):
        priceList = [[s+1 for s in range(priceLevels)] for j in range(products)]
    else:
        priceList = input.priceList
        maxPrice = -100
        for j in priceList:
            if maxPrice < max(j):
                maxPrice = max(j)

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