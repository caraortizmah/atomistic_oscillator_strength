"""
Configuration parameters for the electron transition decomposition atomic contribution
(ETDAC) calculation.
"""

import os
import re
from typing import Dict, Optional, Tuple, List
from pathlib import Path


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
        corepop_log_file: str, 
        virtualpop_log_file: str, 
        etrans_log_file: str,
        logs_path: str,
        output_path: str):
        """
        Initialize ConfigMan with population files (core and virtual), 
          electron transition file (core-virtual oscillator strength),
          execution path and output path (same as execution path as defult).
        
        Args:
            
            corepop_log_file: File of path lists having core MOs population files
            virtualpop_log_file: File of path lists having virtual MOs population files
            etrans_log_file: File of path lists having core-virtual e- transitions files
            logs_path: Path to the log files (execution path by defult)
            output_path: Path to the H5 output file
        """
        self.corelog_file = corepop_log_file
        self.virtualog_file = virtualpop_log_file
        self.etranslog_file = etrans_log_file
        self.logs_path = logs_path
        self.output_path = output_path
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def checker_outpath(self) -> bool:
        """
        Check if a path already exists.
        Output path is created if not exists
        
        Returns:
            bool: True if successful, False if errors occurred
        """
        if not os.path.isdir(self.output_path):
            self.warnings.append(f"Output path not found: {self.output_path}")
            return False
        
        return True

    def checker_log_file(self, path) -> bool:
        """
        Check if a mandatory log file exists
        
        Returns:
            bool: True if successful, False if errors occurred
        """
        if not os.path.isfile(path):
            self.errors.append(f"Log file {path} not found")
            return False
        
        try:
            with open(path, 'r') as f:
                f.read()
            return True
        except Exception as e:
            self.errors.append(f"Failed to read log file: {str(e)}")
            return False
    
    def checker_logs(self) -> bool:
        """
        Check if all log files exist and cand be read in the execution directory
        
        Returns:
            bool: True if successful, False if errors occurred
        """
        
        errors = 0

        if not self.checker_log_file(os.path.join(self.logs_path, self.corelog_file)): errors += 1
        
        if not self.checker_log_file(os.path.join(self.logs_path, self.virtualog_file)): errors += 1
        
        if not self.checker_log_file(os.path.join(self.logs_path, self.etranslog_file)): errors += 1
    
        return errors == 0
    
    def load(self) -> bool:
        """
        Load the three log files.
        
        Returns:
            bool: True if successful, False if errors occurred
        """
        if self.checker_logs():
            print("Working")
        else:
            return self.checker_logs()
        
        return True

    
