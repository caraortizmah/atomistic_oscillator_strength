"""
Algebra operations that enables the electron transition decomposition atomic contribution
(ETDAC) calculation.

Read  https://doi.org/10.1039/D4CP04615C : 
"X-ray absorption spectroscopy reveals charge transfer in π-stacked aromatic amino acids"
for further information
"""

import numpy as np
import pandas as pd
import csv as csv

# %%
import matplotlib.pyplot as plt
import seaborn as sns

# %%
import h5py


class Operations:
    """
    Takes the dictionary data from Scheme class and run the eq. 5 of the paper:
    "X-ray absorption spectroscopy reveals charge transfer in π-stacked aromatic amino acids"
    
    ETDAC results are return to Scheme.
    
    This class operates transformations over data. 
    
    Mandatory parameters: core matrix, virtual matrix, electron transition matrix (3)
    Optional parameters: None
    """

    def __init__(self):
        """
        Class expected to be used in object.data of Scheme class
        object.data is a dictionary if three dictionaries that contains the raw data 
        of core MOs population, virtual MOs population and electron transition matrix.
        How to acces to object.data (self):
        self['corepop']: Dict
        self['virtualpop']: Dict
        self['etrans']: Dict
        """

        trim_data = {
        'corepop': Dict,
        'virtualpop': Dict
        }

        trim_data['corepop'] = remove_noncontrb(self['corepop'])
        trim_data['virtualpop'] = remove_noncontrb(self['virtualpop'])    
    
    def is_trimmed(self, key: str = 'corepop') -> bool:
        if not self[key] == trim_data[key]:
            return True
        return False
    
    def report_trimmed(self, key: str = 'corepop') -> bool:
        
        typemo = 'core' if key == 'corepop' else 'virtual' if key == 'virtualpop' else 'error'

        if typemo == 'error':
            printf(f"Wrong key assignment: use only 'corepop' or 'virtualpop'\n")
            return False

        if self.is_trimmed(key):
            print(f"There were found non-contributing {typemo} MOs\n")
            print(f"Non-contributing {typemo} MOs are not considered in the ETDAC calculation\n")
        else:
            print(f"There were not found non-contributing {typemo} MOs\n")
        return True

    def is_empty(self, key: str = 'corepop') -> bool:
        if not self[key]:
            return True
            
    def remove_noncontrb(dict_data_raw) -> Dict:
        """
        Drops off the non-contributing elements to avoid
        zero or nan spread on the following linear algebra 
        operations.
        This function depends on the nonzero_mo_matrix()
        to work.
        Args:
        dict_data_raw (dict): the pd.frames inside can have zeroes
        or nan values.
        Output (dict): dict_data only with nonzero elements.
        """
        dict_data = {}
        for key, value in dict_data_raw.items():
            dict_data.update({key: nonzero_mo_matrix(value)})
        return dict_data
    
    def nonzero_mo_matrix(df):
        """
        it returns MO matrix (df) having just non-zero MO population.
        """
        return df.loc[:, (df != 0).any(axis=0)] #removing zero columns

#calculate_etdac
    def heatmap_ETDAC(core_MO, virt_MO, fosce_mo_trans):
        """
    Runs the ts_psb_acore_bvirt() function to calculate the
     electron transition density atomic contribution matrix 
     by performing some matrix transformations in the 
     core_MO and virt_MO pd.frames that are stored as
     values in dictionary.
    Args:
    core_MO (dict): core MO and atom population matrices 
     obtained by load_dict_data() and remove_noncontrb()
    virt_MO (dict): virtual MO and atom population matrices 
     obtained by load_dict_data()
    fosce_mo_trans (dict): electronic transition
     (oscillator strength) MO matrices obtained by the pipeline
     (github.com/caraortizmah/x-ray_scripting_out) and 
     formated by load_dict_data()
    Output:
    heatmap_raw (dict): The electron transition density 
     atomic contribution (ETDAC) matrix in pd.frame format.
        """
        # WSM case
        # Exploiting the fact that all data share same order of the keys (hashes)
        heatmap_raw = {}
        for key in virt_MO.keys(): 
            # it can be any of the created dictionaries, they have same keys and in the same order
            heatmap_raw.update({
                key:
                ts_psb_acore_bvirt(
                    core_MO[key].T[2:].T,
                    virt_MO[key].T[2:].T,
                    fosce_mo_trans[key])
                    })
        return heatmap_raw



def selecting_atm_matrix(df, atoms_list):
    """
    it returns MO matrix (df) having just the atoms in atoms_list.
    """
    col_list = df.index.tolist() #listing index (elements from column 0)
    #dff = df.loc[:, (df != 0).any(axis=0)] #removing zero columns
    return df.loc[[i for i in atoms_list if i in col_list]] #returning just columns in the both lists intersection
#atoms_core=resa_mocore_GFG9Y_raw.index.tolist() #all C-core atoms
#[i for i in atoms_a if i in atoms_core] #atoms_a intersection atoms_core

# %%
def crop_by_loewdin_p(df,pop):
    """
    it returns MO matrix (df) having just a Loewdin MO population contribution greater than (100*pop)%.
    pop is a number between 0 and 1.
    """
    #cols = [col for col, val in df.sum()[2:].iteritems() if val > (pop*100)]
    cols = [col for col, val in df.sum()[2:].items() if val > (pop*100)]
    #iteritem() create a zip with the index_col and the values
    cols.insert(0,'lvl')
    cols.insert(0,'sym')
    #to add on the top the first two columns removed in the previous sum() evaluation
    return df[cols] #showing the fisrt two columns and those having population greater than pop*100%

# %%

# %%
def cropping_matrix(df, df1, df2):
    """
    it returns a cropped MO matrix from df using as parameters the indices in df1 and df2.
    df1 index are column names from df and df2 index are the rows from df
    """
    try:
        dff = df[df1.axes[1][2:].tolist()] #saving specific columns
    except KeyError:
        tmp_mo = [item for item in df1.axes[1][2:].tolist() if item in df.axes[1][0:].tolist()]
        #removing items in the first list that are not in the second one
        dff = df[tmp_mo]
    try:
        return dff.loc[[int(i) for i in df2.axes[1][2:].tolist()]] #returning specific rows
    except KeyError:
        tmp_mo2 = [item for item in df2.axes[1][2:].tolist() if int(item) in dff.T.axes[1][0:].tolist()]
        # dff.T to obtain the index_col as the head row
        return dff.loc[[int(i) for i in tmp_mo2]] #returning specific rows
# the first two elements in df2.axes[1] and df1.axes[1] are "sym" and "lvl", that's why I used df.axes[1][2:]

# %%


# %% [markdown]
# #### Main functions: ETDAC matrix calculation

# %% [markdown]
# ##### Building heatmaps of $\tilde{\gamma}^{[l,m]}_{AA^{\prime}}$

# %%
def ts_psb_acore_bvirt(acore, bvirt, abcorevirt, atm_to_virtmo=False):
    """
    Do a matrix multiplication between the core-to-virt transition 
    probabilities matrix and the core MO matrix, then the resulting matrix
    is multiplied by the virtual MO matrix.
    if atm_to_virtmo is True, then the two resulting matrices in the 
    multiplication process are returned.
    By the default, just the last matrix is returned.
    """
    abcorevirt.index = abcorevirt.index.astype('str') 
    #to make possible the dot product in pandas, the indexes involved in each
    #product have to "match" in name and type
    
    i = j = 0
    dff = pd.DataFrame(np.zeros((acore.shape[0], abcorevirt.shape[0])), \
                       index=acore.index, columns=abcorevirt.index)
    for j in range(abcorevirt.shape[1]):
        for i in range(acore.shape[1]):
            try:
                dff += acore.T[i:i+1].T.dot(abcorevirt.iloc[:].T[j:j+1])
            except:
                pass
            
    dff = dff/100
    i = j = 0
    dff2 = pd.DataFrame(np.zeros((dff.shape[0], bvirt.shape[0])), \
                        index=dff.index, columns=bvirt.index)
    for i in range(dff.shape[1]):
        for j in range(bvirt.shape[1]):
            try:
                dff2 += dff.T[i:i+1].T.dot(bvirt.T[j:j+1])
            except:
                pass
    
    if atm_to_virtmo:
        return dff, dff2
    else:
        return dff2

# %%


# %%
def crop_heatmap_byatm(etdac_m, row_cond, col_cond):
    """
    Crop the electron transition density atomic 
     contribution matrix by using a range of atoms
     that are in the core space and in the virtual
     space.
    Args:
    etdac_m (pd.frame): Electron transition density atomic 
     contribution matrix.
    row_cond (lambda): if-statement using the range of 
     atoms of the core space.
    col_cond (lambda): if-statement using the range of
     atoms of the virtual space.
    Outputs:
     etdac_m cropped by using two lambda functions.
    """
    return etdac_m.loc[
    [i for i in etdac_m.index.values if row_cond(i)],
    [i for i in etdac_m.columns.values if col_cond(i)]
    ]
