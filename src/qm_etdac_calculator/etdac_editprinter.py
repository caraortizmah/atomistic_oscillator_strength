# %% [markdown]
# #### Big data sampling of the standard post analysis
# 
# Data presented here, as new inputs for this jupyter-notebook, comes from the written-shell pipeline created to extract X-ray excited-state features from some specific pair of atoms group (e.g. pair amino acid). Outputs here are filtered features that account for specific transitions (coreMO -> virtualMO) for the specific pair of atoms group

# %% [markdown]
# ###### Check out the paper of this work <br>
# ##### *X-ray absorption spectroscopy reveals charge transfer in π-stacked aromatic amino acids*:<br> https://doi.org/10.1039/D4CP04615C

# %%
import numpy as np
import pandas as pd
import csv as csv

# %%
import matplotlib.pyplot as plt
import seaborn as sns

# %%
import h5py

# %%
# Saving data
save_ETDAC_matrix(heatmap, data_set_name="data_etdac_matrix.h5")
# load format of saved_data
# %%


# %%
## test purposes
rel_list = []
tmp_keys = [key for key in heatmap.keys()][10:58] #from 3.5 to 9.0 A
for ii in tmp_keys: 
    rel_list.append(heatmap[ii].max().max())
relmax = max(rel_list)
relmin = min(rel_list)
relmin, relmax

# %% [markdown]
# ##### Plot electron transition density atomic contribution (ETDAC) matrices

# %%
fig, ax = plt.subplots(figsize=(17,10)) 
test = (heatmap['f13'] - heatmap['f13'].min().min())/(heatmap['f13'].max().max() - heatmap['f13'].min().min())
sns.heatmap(test, annot=False, cmap='Oranges', vmin=0, vmax=1, ax=ax)

# %% [markdown]
# #### Definition of amino acids using range of atoms
# ##### Example is the same Phe --- Tyr

# %% [markdown]
# ##### Set atoms

# %%
atomAi = 0
atomAf = 22
atomBi = 23
atomBf = 46

# %%
atomAi, atomAf, atomBi, atomBf

# %% [markdown]
# #### Delitimation of atoms of the aromatic rings

# %%
atomFi = 6
atomFf = 11
atomYi = 29
atomYf = 33
atomYf2 = 35

# %% [markdown]
# #### Calculating the 4 (more) terms of the transition intensities

# %%
inter_fosce = []
all_fosce = []
FYpi_inter_fosce = []
YFpi_inter_fosce = []
aropi_inter_fosce = []
keys = []

for key in heatmap.keys():
    keys.append(key)
    row_cond_1, col_cond_1 = lambda i: i > atomAf, lambda i: i < atomBi
    row_cond_2, col_cond_2 = lambda i: i <= atomAf, lambda i: i >= atomBi
    inter_fosce.append(
        crop_heatmap_byatm(heatmap[key], row_cond_1, col_cond_1).sum().sum() +
        crop_heatmap_byatm(heatmap[key], row_cond_2, col_cond_2).sum().sum()
    )
    row_cond_1 = lambda i: i >= atomFi and i <= atomFf
    col_cond_1 = lambda i: (i >= atomYi and i <= atomYf) or i == atomYf2
    FYpi_inter_fosce.append(
        crop_heatmap_byatm(heatmap[key], row_cond_1, col_cond_1).sum().sum()
        )
    row_cond_1 = lambda i: (i >= atomYi and i <= atomYf) or i == atomYf2
    col_cond_1 = lambda i: i >= atomFi and i <= atomFf
    YFpi_inter_fosce.append(
        crop_heatmap_byatm(heatmap[key], row_cond_1, col_cond_1).sum().sum()
        )
    
    aropi_inter_fosce = [FYpi_inter_fosce[i] + YFpi_inter_fosce[i] for i in range(len(inter_fosce))]
    
    all_fosce.append(heatmap[key].sum().sum())
    
intra_fosce = [all_fosce[i] - inter_fosce[i] for i in range(len(inter_fosce))]

# %%
max(inter_fosce), max(intra_fosce), max(all_fosce)

# %%
dfftotal_fosce = pd.DataFrame({'hash': [i for i in keys],\
                               'inter_fosce': [i for i in inter_fosce],\
                               'intra_fosce': [i for i in intra_fosce],\
                               'all_fosce': [i for i in all_fosce],\
                               'FY_pi':[i/max(inter_fosce) for i in FYpi_inter_fosce],\
                               'YF_pi':[i/max(inter_fosce) for i in YFpi_inter_fosce],\
                               'pi_pi':[i/max(inter_fosce) for i in aropi_inter_fosce],\
                               'abs_pi_pi':[i for i in aropi_inter_fosce]
                              })

# %%
dfftotal_fosce

# %% [markdown]
# #### Data to be saved

# %%
plt.rc('font', size=26)
ax = dfftotal_fosce.loc[10:55,:].plot(
    x="hash",
    y=["inter_fosce","intra_fosce","abs_pi_pi", "all_fosce"],
    kind="line",
    figsize=(16, 12))
ax.set_xlabel('Sample unique identificator')
ax.set_ylabel('Transition intensity')

plt.show()

# %% [markdown]
# #### That's it :)

# %%



