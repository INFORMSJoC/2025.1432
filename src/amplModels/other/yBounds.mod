# Sets
set J; # products with boolean decision variables
set I; # segments
set Pj; # set of price index

# Parameter
param minProblem; # 1 for minimization problem, -1 for maximization problem
param curSeg; # current segment
param p{j in J, s in Pj};  # allowed prices         
param Ai0{i in I};        # outside option
param omega{i in I};    # segment population
param A{i in I, j in J, s in Pj}; # Attraction of the products
param cardinality; # max number of products
param weight{j in J};
param lambdaa{i in I,j in J,s in Pj}; #Lambda
param yL{i in I}; # lower bound of y
param yU{i in I}; # upper bound of y
param preSetToZero{j in J, s in Pj}; # Variables that are set to zero
param preSetToOne{j in J, s in Pj}; # Variables that are set to one

# Decision variables
var x{J,Pj} binary;#>= 0,<=1;

# Objective function
minimize fMinAndMax: (Ai0[curSeg] + sum{j in J, s in Pj} A[curSeg,j,s] * x[j,s]) * minProblem;

# Constraints 
s.t. constraint1{j in J}: sum{s in Pj} x[j,s] <=1; # Allow only one price
s.t. constraint2: sum{j in J, s in Pj} weight[j] * x[j,s] <= cardinality; # Cardinality constraint
#s.t. constraint3: sum{j in J, s in Pj} A[curSeg,j,s]  * x[j,s] <= 1/yL[curSeg] - Ai0[curSeg]; # Model specific constraint
s.t. setToZero{j in J, s in Pj}: x[j,s] <= 1-preSetToZero[j,s]; # Set decision values to a specific value = 0
s.t. setToOne{j in J, s in Pj}: x[j,s] >= preSetToOne[j,s]; # Set decision values to a specific value = 1


