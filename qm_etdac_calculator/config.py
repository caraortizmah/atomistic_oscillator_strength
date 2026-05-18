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
        'input_path': (str, None),
        'output_path': (str, None),
    }
    
    def __init__(self, input_path: str, output_path: str):
        """
        Initialize ConfigMan with input and output paths.
        
        Args:
            input_path: Path to the log files
            output_path: Path to the H5 output file
        """
        self.input_path = input_path
        self.output_path = output_path
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def checker_path(self) -> bool:
        """
        Check if paths already exists.
        input path MUST exists and output path is created if not exists
        
        Returns:
            bool: True if successful, False if errors occurred
        """
        if not os.path.isdir(self.input_path):
            self.errors.append(f"Input path not found: {self.input_path}")
            return False

        if not os.path.isdir(self.output_path):
            self.warnings.append(f"Output path not found: {self.output_path}, input path: {self.input_path}, will be used instead")
            self.output_path = self.input_path
        
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
    
