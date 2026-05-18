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
        script_name: Name of the script (e.g., 'etdac_calculator.py', 'gate_controler.py')
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
    Entry point for 'qm-etdac' console script.
    Runs bin/manager_etdac.py with command-line arguments.
    Provides --help to display usage information.
    """
    try:
        # Check for --help flag
        if len(sys.argv) > 1 and sys.argv[1] in ('--help', '-h', 'help'):
            help_msg = """
qm-etdac-calculator: Core-electron transition decomposition in atomic contributions program

USAGE:
    qm-etdac [options]

This command calls bin/manager_etdac.py to run the program that calculates the 
electron transition density atomic contribution (ETDAC) matrix.

For detailed information on usage, examples, and configuration, please see:
    - README.md: Project overview and quick start
    - docs/howtorun.md: Step-by-step tutorial
    - docs/architecture.md: System design and data flow
    - docs/installation.md: Installation instructions

RELATED COMMANDS:
    qm-etdac-test      Run automated tests

"""
            print(help_msg)
            return 0
        
        script = _get_script_path("manager_etdac.py", "bin")
        result = subprocess.run([sys.executable, str(script)] + sys.argv[1:], check=False)
        return result.returncode
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def run_qm_etdac_test() -> int:
    """
    Entry point for 'qm-etdac-test' console script.
    Runs automated tests using tester.sh 
    """
    try:
        print("=" * 60)
        print("Running qm-etdac-calculator test ...")
        print("=" * 60)
        
        tester_script = _get_script_path("tester.sh", "tests")
        
        # ongoing
        print("\n[1/n] Testing test model...")
        cmd1 = ["bash", str(tester_script)]
        result1 = subprocess.run(cmd1, check=False)
        
        print("\n" + "=" * 60)
        if result1.returncode == 0:
            print("All tests passed!")
        else:
            print("Some tests failed. Please review the output above.")
        print("=" * 60)
        
        # Return non-zero if any test failed
        return max(result1.returncode)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    # For testing CLI entry points
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "test":
            sys.exit(run_qm_etdac_test())
        # TODO:
        #elif command == "setup":
        #    sys.exit(run_qm_etdac_setup())
    
    print("Usage: qm-etdac|qm-etdac-test [args]")
    sys.exit(1)