# atomistic_oscillator_strength
There are two folders for two part of the post processing data from the ORCA outputs

### plot/

Here all the notebooks are intented to plot XAS directly from the ORCA outputs

### pop_matrices/

Here notebooks take the outputs from the [x-ray_scripting_out](https://github.com/caraortizmah/x-ray_scripting_out) 
repository and calculate the electron transition density atomic contribution matrix.

There are two specific examples for the pair amino acid system Phe-Tyr for the first 17 excited states (FY_1-17) and 
for the first 26 excited states (newFY_1-26).
The **standard case** of the postanalysis is the template in the folder:

`Standard_analysis/` as `postanalysis_generalcase.ipynb` file.


## Standard post-analysis to calculate 
$$ \huge \tilde{\gamma}^{[l,m]}_{AA^{\prime}} $$

Standard_analysis/postanalysis_generalcase.ipynb

Check this paper for further information regardinf the theoretical concepts:

#### *X-ray absorption spectroscopy reveals charge transfer in π-stacked aromatic amino acids*:<br> https://doi.org/10.1039/D4CP04615C
