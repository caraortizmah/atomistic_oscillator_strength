"""
Excited-State Charge Transfer Calculator Program for X-ray Absorption Spectroscopy

A package for calculating the Electron Transition Density Atomic Contribution (ETDAC)
Matrix using the parsed data of the quantum-charge-transfer-calculator package.
"""

__version__ = "1.0.0"
__author__ = "Carlos Ortiz-Mahecha"

from .config import ConfigMan
from . import cli
from .etdac_calculator import Scheme

__all__ = ["ConfigMan", "cli"]
