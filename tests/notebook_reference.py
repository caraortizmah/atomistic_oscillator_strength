# ruff: noqa
"""Frozen copy of the reference notebook's functions. DO NOT EDIT.

Source: popmatrices/Bigscale/ETDAC_matrix_calculator.ipynb (commit 0d75b23).
The function bodies below are copied verbatim from the notebook, including their
style and bare excepts, so the tests compare the package against exactly the code
that produced the published results (ADR 0002). Only `format_heatmaps` wraps the two
formatting loops that follow `heatmap_ETDAC` in the notebook into a function.
`save_ETDAC_matrix` was added in step 5e (same notebook, same commit, copied verbatim) as
the reference for the .h5 layout.

Not collected by pytest (file name does not start with test_).
"""

import h5py
import numpy as np
import pandas as pd


# --- notebook function: load_dict_data
def load_dict_data(filename, index_col_condition='num-1'):
    """
    Reads from a two-column file the hash and the file and
     stores the information of the csv file into a dictionary.
    Format file to be read:
     f00,(path)../newFY_1-26/resA_MOcore_AB_2.5A_1-26.csv
     f01,(path)../newFY_1-26/resA_MOcore_AB_2.6A_1-26.csv
     f02,(path)../newFY_1-26/resA_MOcore_AB_2.7A_1-26.csv
     f03,(path)../newFY_1-26/resA_MOcore_AB_2.8A_1-26.csv
      ...
     f61,(path)../newFY_1-26/resA_MOcore_AB_11.0A_1-26.csv 
    Args:
     filename (str): two-column file filename having
      a hash for each path file.
     index_col_condition (str): the name of the index 
      column to read the csv as pandas structure.
      Default as 'num-1'
    Output (dict): keys are the hashes and values of the dictionary
     are the pandas frame for each csv file.
    """
    # Initialize a dictionary
    dict_raw = {}
    # Open the list file
    with open(filename, 'r') as file:
        # Read each line in the file
        for line in file:
            line = line.strip()
    # {(key) hash = line.split(',')[0] : (value) file_n = line.split(',')[1]}
            dict_raw.update({
                line.split(',')[0]: # key
                pd.read_csv(line.split(',')[1],
                            delimiter=',',
                            index_col=index_col_condition) # value
            })
    return dict_raw


# --- notebook function: nonzero_mo_matrix
def nonzero_mo_matrix(df):
    """
    it returns MO matrix (df) having just non-zero MO population.
    """
    return df.loc[:, (df != 0).any(axis=0)] #removing zero columns


# --- notebook function: remove_noncontrb
def remove_noncontrb(dict_data_raw):
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


# --- notebook function: ts_psb_acore_bvirt
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


# --- notebook function: heatmap_ETDAC
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


# --- notebook formatting loops after heatmap_ETDAC, wrapped as a function
def format_heatmaps(heatmap_raw):
    for key in heatmap_raw.keys():
        heatmap_raw[key].index.names = ['core-atom']
        heatmap_raw[key].columns.names = ['virtual-atom']
    heatmap = {}
    for key in heatmap_raw.keys():
        heatmap.update({
            key:
            heatmap_raw[key].apply(pd.to_numeric).sort_index(ascending=True)
        })
    return heatmap


# --- notebook function: save_ETDAC_matrix
def save_ETDAC_matrix(data_dict, data_set_name="data_etdac_matrix.h5"):
    """
    Get the node/edge features for each molecule and save
    all the results in H5PY format.
    Args:
    data_dict (dict) contains a hash (key) and 
     the ETDAC matrix (value) of each molecule.
    data_set_name (str, optional) is the name of the H5PY file to be
     created. By default that file is called "data_etdac_matrix.h5".
    """
    
    with h5py.File(data_set_name, 'w') as f:

        # Get node/edge features for the list of molecules
        for hash in data_dict.keys():
#df.to_hdf('data.h5', key='df', mode='w', format='table')
            qm_group = f.create_group(f"sample_{hash}")
            qm_group.create_dataset("ETDAC_matrix", 
                                    data=data_dict[hash].to_records(index=True),  # Preserves index+columns
                                    compression="gzip")
            
            qm_group.attrs["hash"] = hash
            qm_group.attrs["column_name"] = data_dict[hash].columns.name # Save column name
            qm_group.attrs["index_name"] = data_dict[hash].index.name  # Save row name
