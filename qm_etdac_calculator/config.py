"""
Configuration parameters for the electron transition decomposition atomic contribution
(ETDAC) calculation.
"""

import os
#import re
from typing import Dict, Optional, Tuple, List
#from pathlib import Path


class ConfigMan:
    """
    Manages the configuration parameters prior to load log files for the ETDAC calculation.
    
    This class is in an ongoing extension.
    Mandatory parameters: path_logs_files, path_etdac_h5_file
    Optional parameters: None
    """
    MANDATORY_FLAGS = {
        'Atom_number_range_A': str,
        'Atom_number_range_B': str,
        'core_MO_range': str,
        'exc_state_range': str,
        'soc_option': int,
        'orca_output': str,
    }
    
    OPTIONAL_FLAGS = {
        'spectra_option': (int, 0),
        'external_MO_file': (str, None),
        'atm_core': (str, 'C'),
        'wave_f_type': (str, 's'),
        'input_path': (str, None),
        'output_path': (str, None),
    }

    PATHS_PARAMS = {
        'output_path': (str, None),
    }
    
    def __init__(
        self, 
        corepop_files: str, 
        virtualpop_files: str, 
        etrans_files: str,
        output_path: str):
        """
        Initialize ConfigMan with transition and population files;
          output path is optional.
        
        Args:
            
            corepop_file: File of path lists having core MOs population files
            virtualpop_file: File of path lists having virtual MOs population files
            etrans_file: File of path lists having core-virtual e- transitions files
            output_path: Path to the H5 output file
        """
        self.core_files = corepop_files
        self.virtual_files = virtualpop_files
        self.etrans_files = etrans_files
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def checker_path(self) -> bool:
        """
        Check if path already exists.
        Output path is created if not exists
        
        Returns:
            bool: True if successful, False if errors occurred
        """
        if not os.path.isdir(self.output_path):
            self.warnings.append(f"Output path not found: {self.output_path}, however it was created.")
            return False
        
        return True

    def checker_files(self, name_log: str, type_log:str) -> bool:
        """
        Load csv files.
        
        Returns:
            bool: True if successful, False if errors occurred
        """
        self.name_log = name_log
        self.type_log = type_log

        self.path_log = os.path.join(self.input_path, self.name_log)

        if not os.path.isfile(self.path_log):
            self.errors.append(f"Log file {self.name_log} not found in path {self.path_log}")
            return False
        
        return True
    
