#!/usr/bin/env python3
"""
X-ray Spectroscopy Pipeline: Configuration Helper

This script reads configuration from config.info and executes the pipeline
with proper validation, logging, and error handling.

Usage:
    ./manager_etdac.py [--list-inputs [LIST_INPUTS... ]] [--path-output PATH_OUTPUT]
"""

import os
import sys
import subprocess
import argparse
import json
from pathlib import Path

# Add package to path - handle both direct execution and via symlink
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from qm_etdac_calculator import ConfigMan

def get_kwargs(dict, key, value):
    return dict.update({key:value})

def set_args_askwargs(dict={}, *args):
    """
    List information transformed in a dictionary.
    Information in the list SHOULD come in order:
    1: core population log file
    2: virtual population log file
    3: electron transition (core to virtual) log file
    4: path of the three previous log files
    5: path of the output
    """
    get_kwargs(dict, 'corepop',args[0])
    get_kwargs(dict, 'virtpop',args[1])
    get_kwargs(dict, 'etranscv',args[2])
    get_kwargs(dict, 'logspath',args[3])
    get_kwargs(dict, 'outputpath',args[4])
    return dict

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Excited State Charge Transfer Calculator Program - Options Helper"
    )

    parser.add_argument('mode', choices=['noauto', 'auto'])
    # Mode 1: Using --list-run and --path-output
    parser.add_argument('--list-input', 
    nargs=3, 
    default=[],
    help="Use three log files containing list of path files with core and virtual population and electron transition"
    )
    parser.add_argument('--paths-inout',
    nargs='+',
    default=[],
    help="Provide the path of the log files and (optional) path of the ETDAC results."
    )
    
    #Mode 2: By reading JSON file
    parser.add_argument('auto', nargs='?')

    args = parser.parse_args()

    if args.mode == 'noauto':
        if not args.list_input:
            args.list_input = ["", "", ""]
    
        if len(args.paths_inout) == 1:
            cwd = os.getcwd()
            missing_path = os.path.join(cwd, "etdac_results")
            args.paths_inout.append(missing_path)
            print(f"Output folder will be called etdac_results/ in: {missing_path}\n")

        args_list = [*args.list_input, *args.paths_inout]        
        dict_args = set_args_askwargs({}, *args_list)
        print(f"Arguments that will be used were configured as: {dict_args}\n")
    else:
        # Read JSON (which becomes a dictionary)
        with open(args.auto, 'r') as jsonf:
            dict_args = json.load(jsonf)  # Returns a dict
        print(f"Arguments that will be used were configured from file {args.auto} as: {dict_args}\n ")

    # Load configuration
    config = ConfigMan(**dict_args)

    if not config.load():
        #logger.error("Failed to load configuration")
        #logger.error(f"Errors: {', '.join(config.errors)}")
        print("Failed to load necessary files or there is a missing file:")
        print(f"Errors: {', '.join(config.errors)}")
        return 1

    if not config.checker_outpath():
        path_cmd = f"mkdir -p {args.path_output}"
        print(f"New path will be created: {args.path_output}\n")

    try:
        subprocess.run(path_cmd, shell=True, check=False)
            
    except Exception as e:
        #logger.error(f"Error executing ETDAC program: {str(e)}\n")
        print(f"Error creating path for the results: {str(e)}\n")
        return 1
    
    from qm_etdac_calculator import Scheme

    if config.load():
        #logger.info("="*70)
        #logger.info("ETDAC execution started")
        #logger.info("="*70)
        print("ETDAC program will be executed")

        #logger.error(f"Error executing ETDAC program: {str(e)}\n")
        #return 1
        

if __name__ == "__main__":
    sys.exit(main())