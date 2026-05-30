"""
Scheme of running the electron transition decomposition atomic contribution
(ETDAC) calculation.

Data presented here comes from the xas-qmol-parser
Read  https://doi.org/10.1039/D4CP04615C : 
"X-ray absorption spectroscopy reveals charge transfer in π-stacked aromatic amino acids"
for further information
"""

import numpy as np
import pandas as pd
import csv as csv
import h5py

from .gate_controler import Controler

class Scheme:
    """
    Take the accepted arguments from ConfigMan class and load the log files,
    enables the ETDAC calculation and saves the results.
    
    This class acts as an overall scheme that calls other routines to perform
    the calculation of the ETDAC analysis. 
    
    Mandatory parameters: log_files_name (3), paths (3)
    Optional parameters: None
    """
    
    def __init__(self, **kwargs: str):
        """
        After ConfigMan "approves" the existence of the provided arguments, the same 
        received arguments pass to this class. Of course, if the files have an inner
        problem that is responsibility of the user.
        
        kwargs:
            
            'corepop': corepop_log_file =  File of path lists having core MOs population files
            'virtpop': virtualpop_log_file = File of path lists having virtual MOs population files
            'etranscv': etrans_log_file = File of path lists having core-virtual e- transitions files
            'logspath': logs_path = Path to the log files (execution path by defult)
            'outputpath': output_path = Path to the H5 output file
        """
        self.corelog_file = kwargs['corepop']
        self.virtualog_file = kwargs['virtpop']
        self.etranslog_file = kwargs['etranscv']
        self.logs_path = kwargs['logspath']
        self.output_path = kwargs['outputpath']
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.data: Dict[str, Dict] = {}
        self.etdac: Dict = {}

        # Initialize classes
        open_data = Controler()

    def get_info(self, log_file: str) -> {}:
        if open_data.is_datawell(log_file):
            return open_data.get_dict_data(log_file, 'num-1')
        else:
            self.errors.append(f"One or more problems with file {log_file} were detected. Do a diagnosis.\n")
            return {}

    def opendata(self) -> Bool:
        self.data['corepop'] = self.get_info(self.corelog_file)
        self.data['virtualpop'] = self.get_info(self.virtualog_file)
        self.data['etrans'] =self.get_info(self.etranslog_file)
        # if any of them is empty is because get_info found something wrong
        if not (self.data['corepop'] or self.data['virtualpop'] or self.data['etrans']):
            return False
        return True


#resa_mocore_raw = load_dict_data('resA_MOcore_list.log', 'num-1')
#resb_movirt_raw = load_dict_data('resB_MOvirt_list.log', 'num-1')
#corevirtMO_fosce_raw = load_dict_data('corevirt_fosce_AB_list.log', 'virt\core')

# Reducing Löwdin Population MO matrices by removing non-contributing MO

#  Case for core MO in the resA 
resa_mocore = remove_noncontrb(resa_mocore_raw)

# Case for virtual MO in the resB
resb_movirt = remove_noncontrb(resb_movirt_raw)

# ### Results

"""
Final calculation: $$ \huge \tilde{\gamma}^{[l,m]}_{AA^{\prime}} $$
"""

# WSM case, it is the official representation by the domain-knowledge
heatmap_raw = heatmap_ETDAC(resa_mocore, resb_movirt_raw, corevirtMO_fosce_raw)


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
