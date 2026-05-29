#!/usr/bin/env python3
"""
X-ray Spectroscopy Pipeline: Configuration Helper

This script reads configuration from config.info and executes the pipeline
with proper validation, logging, and error handling.

Usage:
    ./manager_etdac.py [--single-run] [--list-run]
"""

import os
import sys
import subprocess
import argparse
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
    parser.add_argument('--list-run',
    nargs='*',
    default=[],
    help="Run program for a list of n molecules: n sets of excited-state files")
    parser.add_argument('--path-output',
    help="Save the ETDAC results in the output path.")

    args = parser.parse_args()
    cwd = os.getcwd()
    
    if not args.list_run:
        args.list_run = [
            "",
            "",
            ""
            ]

    if not args.path_output:
        args.path_output = os.path.join(cwd, "etdac_results")
        print(f"Output folder will be called etdac_results/ in: {args.path_output}\n")
    
    args.list_run.append(cwd)
    args.list_run.append(args.path_output)
    dict_args = set_args_askwargs({}, *args.list_run)
    print(f"Arguments that will be used were configured as: {dict_args}\n")

    # Load configuration
    config = ConfigMan(**dict_args)

    if not config.checker_outpath():
        path_cmd = f"mkdir -p {args.path_output}"
        print(f"Path will be created: {args.path_output}")

    if not config.load():
        #logger.error("Failed to load configuration")
        #logger.error(f"Errors: {', '.join(config.errors)}")
        print("Failed to load necessary files or there is a missing file")
        print(f"Errors: {', '.join(config.errors)}")
        return 1
    

    try:
        subprocess.run(path_cmd, shell=True, check=False)
        #logger.info("="*70)
        #logger.info("ETDAC execution started")
        #logger.info("="*70)
  
        if config.load():
            print("ETDAC program will be executed")
            
    except Exception as e:
        logger.error(f"Error executing ETDAC program: {str(e)}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())