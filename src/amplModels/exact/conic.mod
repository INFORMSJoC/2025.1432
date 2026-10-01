# Sets
set J; # product
set I; # segments
set Pj; # set of price index

# Parameter
param p{j in J,s in Pj};  # allowed prices         
param Ai0{i in I};        # outside option
param omega{i in I};    # segment population
param A{i in I, j in J, s in Pj}; # Attraction of the products
param maxPrice; # highest price level
param cardinality; # max number of products
param weight{j in J};
param cost{j in J};

# Parameter - McCormick
param yLowerX0{i in I, j in J, s in Pj}; # lower bound of y
param yLowerX1{i in I, j in J, s in Pj}; # lower bound of y
param yUpperX1{i in I, j in J, s in Pj}; # upper bound of y under the condition that x[j,s] = 1

# Decision variables
var x{j in J,s in Pj} binary;
var y{I} >=0;
var z{I,J,Pj} >=0;
var w{I}>=0;

# Objective function
maximize profit: maxPrice - (sum{i in I} omega[i] * Ai0[i] * maxPrice * y[i] + sum{i in I,j in J,s in Pj} omega[i] * (maxPrice - p[j,s] + cost[j]) * A[i,j,s] * z[i,j,s]);

# Constraints
s.t. constraint1{j in J}: sum{s in Pj} x[j,s] <=1;
s.t. constraint2: sum{j in J, s in Pj} weight[j] * x[j,s] <= cardinality; 
s.t. constraint1prime{i in I}: Ai0[i] + sum{j in J, s in Pj} A[i,j,s] * x[j,s] = w[i];
s.t. constraint2prime{i in I, j in J, s in Pj}: z[i,j,s] * w[i] >= x[j,s] * x[j,s];
s.t. constraint3prime{i in I}: y[i] * w[i] >= 1;
s.t. constraint4prime{i in I}: Ai0[i] * y[i] + sum{j in J, s in Pj} A[i,j,s] * z[i,j,s] >= 1;

# Constraints  - McCormick
s.t. McCormick1{i in I, j in J, s in Pj}: z[i,j,s] <= (1/(Ai0[i]+A[i,j,s]))*x[j,s];
s.t. McCormick2{i in I, j in J, s in Pj}: z[i,j,s] >= yLowerX1[i,j,s] * x[j,s];
s.t. McCormick3{i in I, j in J, s in Pj}: z[i,j,s] <= y[i] - yLowerX0[i,j,s] * (1-x[j,s]);
s.t. McCormick4{i in I, j in J, s in Pj}: z[i,j,s] >= y[i]-(1/Ai0[i])*(1-x[j,s]);