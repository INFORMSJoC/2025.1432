# Sets
set J; # product
set I; # segments
set Pj; # set of price index

# Parameter
param p{j in J,s in Pj};  # allowed prices         
param Ai0{i in I};        # outside option
param omega{i in I};    # segment population
param A{i in I, j in J, s in Pj}; # Attraction of the products
param phat; # highest price level
param cardinality; # max number of products
param weight{j in J}; # weight of each product
param cost{j in J}; # Cost of each product

# Parameter - McCormick
param yLowerX0{i in I, j in J, s in Pj}; # lower bound of y
param yLowerX1{i in I, j in J, s in Pj}; # lower bound of y

# Decision variables
var y{I} >= 0;
var z{I,J,Pj} >= 0;
var x{J,Pj} binary;

# Objective function
maximize profit: sum{i in I, j in J,s in Pj} omega[i] * (p[j,s] - cost[j]) * A[i,j,s] * z[i,j,s];

# Constraints
s.t. OnlyOnePrice{j in J}: sum{s in Pj} x[j,s] <= 1; # Allow inly one price
s.t. marketsharesumtoone{i in I}: Ai0[i]*y[i] + sum{j in J, s in Pj} A[i,j,s] * z[i,j,s] = 1; # The total market share is equal to one
s.t. BigM1{i in I, j in J, s in Pj}: z[i,j,s] <= y[i]; # Big M Constraints
s.t. BigM2{i in I, j in J, s in Pj}: z[i,j,s] <= 1 / Ai0[i] * x[j,s]; # Big M Constraints
s.t. BigM3{i in I, j in J, s in Pj}: y[i] - z[i,j,s] <= 1 / Ai0[i] * (1 - x[j,s]); # Big M Constraints
s.t. MaxNumberOfProducts: sum{j in J, s in Pj} weight[j] * x[j,s] <= cardinality; # Cardinality constraint

# Constraints  - McCormick
s.t. McCormick1{i in I, j in J, s in Pj}: z[i,j,s] <= (1/(Ai0[i]+A[i,j,s]))*x[j,s];
s.t. McCormick2{i in I, j in J, s in Pj}: z[i,j,s] >= yLowerX1[i,j,s] * x[j,s];
s.t. McCormick3{i in I, j in J, s in Pj}: z[i,j,s] <= y[i] - yLowerX0[i,j,s] * (1-x[j,s]);
s.t. McCormick4{i in I, j in J, s in Pj}: z[i,j,s] >= y[i]-(1/Ai0[i])*(1-x[j,s]);

