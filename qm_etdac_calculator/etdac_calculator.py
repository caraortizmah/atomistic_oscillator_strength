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


# %% [markdown]
# ______________________________________________

# %%
#Data in .csv format

# %%
# resA core MO - $$\boldsymbol{\text{N}}_{A,i} $$
resa_mocore_raw = load_dict_data('resA_MOcore_list.log', 'num-1')

# %%
# resB virt MO - $$\boldsymbol{\text{N}}_{A^{\prime},a} $$
resb_movirt_raw = load_dict_data('resB_MOvirt_list.log', 'num-1')


# %%
# Transition density state matrix (core/virt MO) 
#  as function of the oscillator strength using electronic dipole moment as operator
#  only presented by weighted (WSM): fosce
#  $$ \gamma^{[l,m]}_{ia} $$
corevirtMO_fosce_raw = load_dict_data('corevirt_fosce_AB_list.log', 'virt\core')

# %%
# Reducing Löwdin Population MO matrices by removing non-contributing MO

# %%
#  Case for core MO in the resA 
resa_mocore = remove_noncontrb(resa_mocore_raw)

# %%
# Case for virtual MO in the resB
resb_movirt = remove_noncontrb(resb_movirt_raw)

# %% [markdown]
# ___________________________

# %% [markdown]
# ### Results

# %%
"""
Final calculation: $$ \huge \tilde{\gamma}^{[l,m]}_{AA^{\prime}} $$
"""

# %%
# WSM case, it is the official representation by the domain-knowledge
heatmap_raw = heatmap_ETDAC(resa_mocore, resb_movirt_raw, corevirtMO_fosce_raw)

# %%
for key in heatmap_raw.keys():
    heatmap_raw[key].index.names = ['core-atom']
    heatmap_raw[key].columns.names = ['virtual-atom']

# %%
heatmap = {}
for key in heatmap_raw.keys():
    heatmap.update({
        key:
        heatmap_raw[key].apply(pd.to_numeric).sort_index(ascending=True)
    })

# %%
# Saving data
save_ETDAC_matrix(heatmap, data_set_name="data_etdac_matrix.h5")
