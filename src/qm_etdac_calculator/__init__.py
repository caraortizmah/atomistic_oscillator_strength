"""
Excited-State Charge Transfer Calculator Program for X-ray Absorption Spectroscopy

A package for calculating the Electron Transition Density Atomic Contribution (ETDAC)
Matrix using the parsed data of the xas-qmol-parser package.
"""

__version__ = "1.2.0.dev0"
__author__ = "Carlos Ortiz-Mahecha"

from .config import ConfigMan
from .errors import InputError
from .etdac_calculator import Scheme
from .etdac_operations import Operations, etdac_matrix, nonzero_mo_matrix, remove_noncontrb
from .gate_controler import Controler, default_data_root

# cli is exported again once it is fixed (step 6).
__all__ = [
    "ConfigMan",
    "Controler",
    "InputError",
    "Operations",
    "Scheme",
    "default_data_root",
    "etdac_matrix",
    "nonzero_mo_matrix",
    "remove_noncontrb",
]
