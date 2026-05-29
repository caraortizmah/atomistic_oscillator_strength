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
    
    def __init__(self, **kwargs: str):
        """
        Initialize ConfigMan with population files (core and virtual), 
          electron transition file (core-virtual oscillator strength),
          execution path and output path (same as execution path as defult).
        
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
    
    def checker_outpath(self) -> bool:
        """
        Check if a path already exists.
        Output path is created if not exists
        
        Returns:
            bool: True if successful, False if errors occurred
        """
        if not os.path.isdir(self.output_path):
            self.warnings.append(f"Output path not found: {self.output_path}. ")
            return False
        
        return True

    def checker_log_file(self, path) -> bool:
        """
        Check if a mandatory log file exists
        
        Returns:
            bool: True if successful, False if errors occurred
        """
        if not os.path.isfile(path):
            self.errors.append(f"Log file {path} not found.\n")
            return False
        
        try:
            with open(path, 'r') as f:
                f.read()
            return True
        except Exception as e:
            self.errors.append(f"Failed to read log file: {str(e)}\n")
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
            #call gate_controler.py
            return True
        else:
            return self.checker_logs()
