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
import h5py

# %%
"""
Electron transition density atomic contribution matrix
$$
\huge \tilde{\gamma}^{[l,m]}_{AA^{\prime}}
$$
"""

# %% [markdown]
# ____________________________

# %% [markdown]
# #### General case of the post analysis for a list of molecules

# %% [markdown]
# The required data are the standard csv files obtained from the https://github.com/caraortizmah/x-ray_scripting_out pipeline which encodes the required information for the calculation of the electronic transition density atomic contribution matrix.

# %% [markdown]
# #### Before starting, create a list file (for the csv files) with two columns (hash, file) listing all the csv files by property/component.
# For instance the case of *resA core MO*:
# 
# 
# Create a file named `resA_MOcore_list.log` where the first column is a list with a hash, e.g., f01, f02, ...f99 and
# the second is the name of the csv file to explore (in this case only the resA MO core csv files).
# 
# The file should look like:
# >  f00,(path)../newFY_1-26/resA_MOcore_AB_2.5A_1-26.csv <br>
# >  f01,(path)../newFY_1-26/resA_MOcore_AB_2.6A_1-26.csv <br>
# >  f02,(path)../newFY_1-26/resA_MOcore_AB_2.7A_1-26.csv <br>
# >  f03,(path)../newFY_1-26/resA_MOcore_AB_2.8A_1-26.csv <br>
# >  ... <br>
# >  f61,(path)../newFY_1-26/resA_MOcore_AB_11.0A_1-26.csv <br>

class Controler:
    def __init__(self):
        return 0
    
    def is_datawell(self, log_file: str) -> bool:
        try:
            with open(log_file, 'r') as file:
                for line in file:
                    line = line.strip()
                    if (len(line.split(',')) !=2 ):
                        return False
                    check_tmp = line.split(',')[0]
                    #check patterns in hash 
                    if not bool(check_tmp and check_tmp.strip()):
                        return False #if blank spaces or empty
                    if (' ' in check_tmp.strip()):
                        return False # if spaces between words
                    if not check_tmp.replace(' ', '').isalnum():
                        return False # if not alphanumeric
                    check_tmp = line.split(',')[1]
                    if not os.path.isfile(check_tmp):
                        return False
                    try:
                        with open(check_tmp, 'r') as f:
                            f.read()
                    except Exception as e:
                        return False
        except Exception as e:
            self.errors.append(f"Failed to open {log_file} file: {str(e)}\n")    
            return False
        #condition
        return True
        
    def get_dict_data(self, filename: str =log_file, index_col_condition='num-1') -> Dict:
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
        
        try:
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
            print(f"Calculated ETDAC was saved in H5 format\n")
            return True
        except Exception as e:
            self.errors.append(f"Failed to save calculated ETDAC in a H5 file: {str(e)}\n")    
            return False 
