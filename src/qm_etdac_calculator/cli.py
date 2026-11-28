"""
The `qm-etdac` command: runs the ETDAC calculation from the command line.

    qm-etdac noauto --list-input F1 F2 F3 [--paths-inout LOGS] [--verbose | --debug]

F1, F2 and F3 are the three list files (core-MO populations, virtual-MO populations,
core-electron transition intensities) inside the project folder LOGS, by default the folder
where the command runs. The results go to LOGS/etdac_outputs (ADR 0007).

Order of a run: console logging, settings (ConfigMan), output folder (Scheme.prepare_outputs),
run log next to the results, then Scheme.run. Only this module configures logging (D19).
InputError and OutputError are expected problems: one line on stderr, exit code 1 (with
--debug also the traceback). Usage errors exit with 2 (argparse). Anything else is a program
bug and keeps its traceback.

The `auto` and `check` modes follow in steps 6.4 and 6.5; `qm-etdac-test` in step 6.6.
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from .config import ConfigMan
from .errors import InputError, OutputError
from .etdac_calculator import Scheme
from .logging_setup import configure_logging

logger = logging.getLogger(__name__)

_NO_OUTPUT_FOLDER = (
    "the output folder is no longer chosen: results go to LOGS/etdac_outputs (ADR 0007); "
    "give only the folder with the three list files"
)


def _parser() -> tuple[argparse.ArgumentParser, argparse.ArgumentParser]:
    """The command's parser and its noauto subparser (for noauto-specific errors)."""
    common = argparse.ArgumentParser(add_help=False)
    verbosity = common.add_mutually_exclusive_group()
    verbosity.add_argument("--verbose", action="store_true", help="show DEBUG messages on the console")
    verbosity.add_argument("--debug", action="store_true", help="like --verbose, and show tracebacks of errors")

    parser = argparse.ArgumentParser(
        prog="qm-etdac",
        description="Calculate the electron transition density atomic contribution (ETDAC) matrix "
        "of every sample from XAS inputs (https://doi.org/10.1039/D4CP04615C). "
        "Input format and project folder: docs/input-format.md.",
    )
    modes = parser.add_subparsers(dest="mode", required=True, metavar="MODE")
    noauto = modes.add_parser(
        "noauto",
        parents=[common],
        help="run with the list files given on the command line",
        usage="qm-etdac noauto --list-input F1 F2 F3 [--paths-inout LOGS] [--verbose | --debug]",
        description="Run the calculation; results go to LOGS/etdac_outputs.",
    )
    noauto.add_argument(
        "--list-input",
        nargs=3,
        required=True,
        metavar=("F1", "F2", "F3"),
        help="list files of the core-MO populations, virtual-MO populations and "
        "core-electron transition intensities, inside LOGS",
    )
    noauto.add_argument(
        "--paths-inout",
        nargs="+",  # one folder; a second value (the old output folder) is rejected with an explanation
        default=["."],
        metavar="LOGS",
        help="project folder with the three list files (default: the current folder)",
    )
    return parser, noauto


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command; returns the exit code (0 success, 1 input or output problem)."""
    parser, noauto = _parser()
    args = parser.parse_args(argv)
    if len(args.paths_inout) > 1:
        noauto.error(_NO_OUTPUT_FOLDER)  # exits with 2

    configure_logging(verbose=args.verbose, debug=args.debug)
    try:
        corepop, virtpop, etranscv = args.list_input
        scheme = Scheme(ConfigMan(corepop=corepop, virtpop=virtpop, etranscv=etranscv, logspath=args.paths_inout[0]))
        paths = scheme.prepare_outputs()
        configure_logging(verbose=args.verbose, debug=args.debug, log_file=paths.log)
        scheme.run(paths)
    except (InputError, OutputError) as error:
        logger.error("%s", error, exc_info=args.debug)
        return 1
    logger.info("results: %s (run log: %s)", paths.h5, paths.log.name)
    return 0


def run_qm_etdac_calculator() -> int:
    """Entry point of the `qm-etdac` console script (pyproject.toml)."""
    return main()


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
            return result1.returncode
        else:
            print("Some tests failed. Please review the output above.")
        print("=" * 60)
        
        # Return non-zero if any test failed
        return max(result1.returncode)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    if sys.argv[1:2] == ["test"]:
        sys.exit(run_qm_etdac_test())  # until step 6.6
    sys.exit(main())
