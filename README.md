[![INFORMS Journal on Computing Logo](https://INFORMSJoC.github.io/logos/INFORMS_Journal_on_Computing_Header.jpg)](https://pubsonline.informs.org/journal/ijoc)

# Capacitated Assortment and price Optimization under the Mixed Multinominal Logit Model

This archive is distributed in association with the [INFORMS Journal on
Computing](https://pubsonline.informs.org/journal/ijoc) under the [MIT License](LICENSE.txt).

The software and data in this repository are a snapshot of the software and data
that were used in the research reported on the paper
[Capacitated Assortment and price Optimization under the Mixed Multinominal Logit Model](https://doi.org/10.1287/ijoc.2025.1432) by Oliver Vetter, Niloufar Sadeghi, and Cornelia Schön.

## Cite

To cite the contents of this repository, please cite both the paper and this repo, using their respective DOIs.

https://doi.org/10.1287/ijoc.2025.1432

https://doi.org/10.1287/ijoc.2025.1432.cd

Below is the BibTex for citing this snapshot of the repository.
```
@misc{vetter2025,
  author =        {Oliver Vetter, Niloufar Sadeghi, Cornelia Schön},
  publisher =     {INFORMS Journal on Computing},
  title =         {Capacitated Assortment and price Optimization under the Mixed Multinominal Logit Model},
  year =          {2025},
  doi =           {10.1287/ijoc.2025.1432.cd},
  url =           {https://github.com/INFORMSJoC/2025.1432},
  note =          {Available for download at https://github.com/INFORMSJoC/2025.1432},
}
```

## Repository structure

| Path | Description |
| --- | --- |
| `input.py` | Generates input instances. |
| `modelSettings.py` | Stores solver configuration options. Set `useCallback` to False if you want to use ConicCut without the cutting.|
| `result.py` | Defines the result object returned by solver methods. |
| `exactMethods/` | Multiple methods returning the optimal solution. `ConicCut` as the main optimization model. `BigM` and `Conic` as control method for the result. |
| `heuristicMethods/` | Genetic algorithms and two-step heuristic methods.  |
| `empiricalData/` | Input definitions for empirical instances. |
| `amplModels/` | AMPL model files used by AMPL-based solvers. |
| `numericalExperiment.py` | Creates and conducts numerical experiments. |
| `experiments/` | Contains experiment data and results. A sample experiment with five representative instances is provided.|
| `main.py` | File for testing purposes - currently configured to generate a random instance and solve it using several solvers. |
| `amplStandalone` | Folder with a standalone ampl implementation in using mod and run files. This folder is independent of the python code and includes some code snippets that we used to get the exact solution as a verification method during experimental phase. An explanation to get it running can be found below. |

## Requirements

The project requires:

- Python 3.6.12
- `amplpy` (any version)
- AMPL and an available AMPL solver/license for AMPL-based methods and calculation of McCormick values
- `gurobipy` 9.1.2. (tested with this version. In my experience, more recent versions may cause the solver to get stuck.)
- A Gurobi installation and valid Gurobi license for Gurobi-based methods

AMPL and Gurobi are external solver dependencies. Their installation,
license configuration, and executable paths must be configured separately
according to the local machine or HPC environment.


## Main functionalities

| Path | Description |
| --- | --- |
| `input.py` | `getRandomFromPLDStructure()` creates an instance based on the PLD structure (attributes and attribute levels). This instance is transformed to the AO structure, such that the conic approach can be used as well. `getRandomExample()` creates an instance based on the AO structure. `updateYBound()` and `addFOConditionalYBoundSimple()` calculate tighter values for the McCormick values - AMPL licence required. Else some reading and printing functionalities. |
| `exactMethods/` | All solvers can be started with `solve(input: input, settings: ModelSettings)`, the instance (input) and the settings that shall be used for the solution (modelSettings). |
| `heuristicMethods/` | All solvers can be started with `solve(input: input, settings: ModelSettings)`, the instance (input) and the settings that shall be used for the solution (modelSettings). |
| `numericalExperiment.py` | The main methods are `createExperiment(.)` to create an experimental setting and `conductExperiment(.)` to run an experiment. |


## Running a single instance

`main.py` creates the default input instance and runs the configured example solvers:

```bash
python main.py
```

The default generated instance is configured in `Input.get()` in
`input.py`. To change the instance size or parameter ranges, adjust that method or call one of the input-generation methods directly.

Solver settings are controlled through `modelSettings.py`. A short test code for the full functionality is:

```python
from input import Input
from modelSettings import ModelSettings
from exactMethods import bigM

instance = Input().get()
input.updateYBound()
input.addFOConditionalYBoundSimple()
settings = ModelSettings()
result = conicCut.solve(input=instance, settings=settings)
print(result.objective, result.time)
```

You can use every solver in `exactMethods/` and `heuristicMethods/` with the `solverName.solve(input,settings)` interface.

## Running numerical experiments

Use `numericalExperiment.py` to generate input
files, conduct experiments, and save result data under the `experiments/`
directory.

The `numericalExperiment.py` script contains a example configurations near the bottom of the
file. Enable or adapt the required experiment configuration, then run:

```bash
python numericalExperiment.py
```

The `numericalExperiment.py` may create output directories and log files in
`experiments/`. Each created instance is saved in a `.txt` file in `__dict__` format. Additionally, the run experiment saves the solver logs, the results and an Excel containing all major statistics. Synthetic input generation uses a fixed random seed in `input.py` by default.

Exemplary experiment setup:
```bash
solverNames = ['conic','conicBC','gaAO']
solver = [conicCut,conicCut,gaAO]
settings = [ModelSettings() for sol in solver]
settings[0].useCallback = False
settings[0].maxTime = 60
settings[1].useCallback = True
settings[1].maxTime = 60
settings[2].stopAfterTime = True
settings[2].maxTimeHeuristic = 60

createExperiment(name= 'medium_20_5', segmentsList=[20,50], priceLevelsList=[10], cardinalityList=[20], attributeUtilityRangeList=[8], betaRangeList=[1], attributes=3, attributeLevels=3, products = 250, outsideOptionRangeList=[5], equalWeight = True, costRangeList=[3], pldStructure= False, repetitions=20)

conductExperiment(name = 'medium_20_5', attributes = 3, attributeLevels = 3, products = 250, pldStructure = False)
```

## Test experiment
The experimental datasets used in the paper are not included in this repository because their total size exceeds several gigabytes. The data can be requested from the authors. To ensure reproducibility, the paper provides sufficient information to generate comparable test instances. In particular, the `createExperiment(...)` function can be used to recreate the underlying experiment structure. Additionally, this repository contains a sample test experiment `test_experiment 250` with some sample files from the paper. Running the experiment generates solver outputs for each method, detailed result files (`.txt`) for every instance-solver combination, and a consolidated Excel summary. To execute the sample experiment, run the command below (also provided in `main.txt`).

```bash
numericalExperiment.conductExperiment(name = 'test_experiment', attributes= 1, attributeLevels= 1, products = 250, pldStructure = False)
```

## AMPL standalone
To run the `amplStandalone` solver you can use the ampl IDE provided with an AMPL license. To run this file you can run `include PLS_JoC.run` from the command line or in the AMPL IDE.

## Notes
- The code is available under the MIT License.
- The code has not been refactored as requested by the journal, so some variable names differ from those used in the final paper. We recommend thoroughly familiarizing yourself with the paper before using the code, as this will make it easier to understand the purpose of each function and variable.
- The code has not been cleaned up (e.g., by removing auxiliary methods) as requested by the journal. This was intentional to keep it as close as possible to the code used in the experimental setup. However, the code contains sufficient comments to help readers understand its structure and functionality.
- The experimental results and further details are provided in the main paper.
- Please contact the authors if you have any questions.
