# atomistic_oscillator_strength

This repo is a collection of notebooks that explains how to calculate the [electron transition density atomic contribution matrix (ETDAC)](https://pubs.rsc.org/en/content/articlelanding/2025/cp/d4cp04615c) from the [xas-qmol-parser](https://github.com/caraortizmah/x-ray_scripting_out) outputs.

There are two folders for two part of the post processing data (already parsed by the [xas-qmol-parser](https://github.com/caraortizmah/x-ray_scripting_out)) from the X-ray Absorption Spectroscopy (XAS) calculations obtained by the [ORCA](https://www.kofo.mpg.de/en/research/services/orca) quantum chemical software.

## Architecture folders
### plot/

Here all the notebooks are intented to plot XAS directly from the ORCA outputs

### pop_matrices/

#### 1. Pre-requisites

Check the [xas-qmol-parser](https://github.com/caraortizmah/x-ray_scripting_out) program that parses specific data from ORCA XAS calculations. The [xas-qmol-parser](https://github.com/caraortizmah/x-ray_scripting_out) program is a python package to parse the output files from the ORCA calculations. The core of the parser workflow is written in shell.

#### 2. Post-processing

Here, notebooks take the outputs (parsed data) from the [x-ray_scripting_out](https://github.com/caraortizmah/x-ray_scripting_out) repository (for python as xas-qmol-parser) and calculate the electron transition decomposition atomic contribution (ETDAC) matrix.

#### 3. Core

The ETDAC matrix is calculated by the following equation:

[$$ \huge \tilde{\gamma}^{[l,m]}_{AA^{\prime}} $$](https://pubs.rsc.org/en/content/articlelanding/2025/cp/d4cp04615c)

This cperation is simple, you can do it by your own in your own program languages or check the notebooks.
I recommend to check out [this one](popmatrices/Bigscale/ETDAC_matrix_calculator.ipynb).

#### 4. Specifications

There are two specific examples for the pair amino acid system Phe-Tyr for the first 17 excited states (FY_1-17) and for the first 26 excited states (newFY_1-26).
The **standard case** of the postanalysis is the template in the folder:

`Standard_analysis/` as `postanalysis_generalcase.ipynb` [file](popmatrices/Standard_analysis/postanalysis_generalcase.ipynb).

## Supporting information

Several post-analyses were performed applying the calculation of the core-electron transition atomic contributions (the ETDAC analysis) that uses parsed XAS calculated data by the [xas-qmol-parser](https://github.com/caraortizmah/x-ray_scripting_out) program.
As result of these post-analyses, it was possible to quantify excited-state charge transfer in π-stacked aromatic interactions.
Check the following publication for further information regarding the theoretical concepts and applications in chemistry:

#### *X-ray absorption spectroscopy reveals charge transfer in π-stacked aromatic amino acids*:<br> https://doi.org/10.1039/D4CP04615C
