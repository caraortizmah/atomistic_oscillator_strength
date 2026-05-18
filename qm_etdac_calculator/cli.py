"""
Command-line interface entry points for the ETDAC calculation.

These functions serve as entry points for installed console scripts.
"""

import sys
import os
import subprocess
from pathlib import Path


def _get_script_path(script_name: str, subdir: str = "bin") -> Path:
    """
    Get the absolute path to a shell script or Python script.
    
    Args:
        script_name: Name of the script (e.g., 'etdac_calculator.py', 'gate_controled.py')
        subdir: Subdirectory to search ('bin', 'tests')
        
    Returns:
        Path to the script
        
    Raises:
        FileNotFoundError: If script is not found
    """
    # Try installation location first
    package_dir = Path(__file__).parent.parent
    script_path = package_dir / subdir / script_name
    
    if script_path.exists():
        return script_path
    
    # Fallback to current directory
    cwd_path = Path.cwd() / subdir / script_name
    if cwd_path.exists():
        return cwd_path
    
    raise FileNotFoundError(f"Script not found: {subdir}/{script_name}")


def run_qm_etdac_calculator() -> int:
    """
    Entry point for 'qm-etdac-run' console script.
    Runs bin/manager_etdac.py with command-line arguments.
    Provides --help to display usage information.
    """
    try:
        # Check for --help flag
        if len(sys.argv) > 1 and sys.argv[1] in ('--help', '-h', 'help'):
            help_msg = """
qm-etdac-calculator: Core-electron transition decomposition in atomic contributions program

USAGE:
    qm-etdac-run [options]

This command calls bin/manager_etdac.py to run the program that calculates the 
electron transition density atomic contribution (ETDAC) matrix.

For detailed information on usage, examples, and configuration, please see:
    - README.md: Project overview and quick start
    - docs/howtorun.md: Step-by-step tutorial
    - docs/architecture.md: System design and data flow
    - docs/installation.md: Installation instructions

RELATED COMMANDS:
    qm-etdacx-test      Run automated tests

"""
            print(help_msg)
            return 0
        
        script = _get_script_path("mannager_etdac.py", "bin")
        result = subprocess.run([sys.executable, str(script)] + sys.argv[1:], check=False)
        return result.returncode
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

