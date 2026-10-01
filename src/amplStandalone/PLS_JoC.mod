
#### Nonlinear formulation
# variable definition

var x{J,S} binary;
var pi{i in I, j in J, s in S} >=0 <=1; # choice probability


maximize profit_nonlinear:  sum{i in I,j in J,s in S} omega[i]*(p[j,s]-cost[j])*pi[i,j,s];
s.t. ChoiceProb{i in I, j in J, s in S}: pi[i,j,s]=A[i,j,s]*x[j,s]/(C[i]+sum{jj in J, ss in S} A[i,jj,ss]*x[jj,ss]);
s.t. OnlyOnePrice{j in J}: sum{s in S}x[j,s]<=1;
s.t. MaxNumberOfProducts: sum{j in J, s in S}x[j,s]<=num_products_max;

#### Linear formulation
param BigM{i in I} default 1/C[i];

var v{I} >=0;
var w{I,J,S} >=0;
var u{I} >=0;

maximize profit_linear: sum{i in I,j in J,s in S} omega[i]*(p[j,s]-cost[j])*pi[i,j,s];
s.t. ChoiceProb_linear{i in I, j in J, s in S}: pi[i,j,s]=A[i,j,s]*w[i,j,s];
s.t. marketsharesumtoone{i in I}: C[i]*v[i]+sum{j in J, s in S}pi[i,j,s]=1;
s.t. BigM1{i in I, j in J, s in S}: w[i,j,s]<=v[i];
s.t. BigM2{i in I, j in J, s in S}: w[i,j,s]<=BigM[i]*x[j,s];
s.t. BigM3{i in I, j in J, s in S}: v[i]-w[i,j,s]<=BigM[i]*(1-x[j,s]);

subject to Conic1{i in I}: u[i]=(C[i] + sum {jj in J, ss in S} A[i,jj,ss] * x[jj,ss]);
subject to Conic2{i in I}: v[i]*u[i]>=1;
subject to Conic3{i in I, j in J, s in S}: w[i,j,s]*u[i]>=(x[j,s])^2;
 
s.t. McCormick1{i in I,j in J,s in S}: w[i,j,s]<=v_max_1[i,j,s]*x[j,s];
s.t. McCormick2{i in I,j in J,s in S}: w[i,j,s]>=v_min_1[i,j,s]*x[j,s];
s.t. McCormick3{i in I,j in J,s in S}: w[i,j,s]<=v[i]-v_min_0[i,j,s]*(1-x[j,s]);
s.t. McCormick4{i in I,j in J,s in S}: w[i,j,s]>=v[i]-v_max_0[i,j,s]*(1-x[j,s]);







