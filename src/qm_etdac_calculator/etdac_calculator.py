"""
One ETDAC calculation from start to end: read the three inputs, calculate, write the results.

Read https://doi.org/10.1039/D4CP04615C :
"X-ray absorption spectroscopy reveals charge transfer in pi-stacked aromatic amino acids"
for the method. The calculation itself is in etdac_operations.py; this module only puts the
parts together, in this order:

1. prepare_outputs(): the output folder, always `etdac_outputs` inside the logs folder
   (ADR 0007), and the paths of the .h5 and .log files; an earlier result is kept as
   `_oldversionN` (outputs.py, ADR 0003);
2. run(paths): one Controler reads the three list files and their CSV files (path policy and
   input rules, ADR 0003/0005), Operations.etdac_batch calculates every sample, and
   write_etdac_h5 writes the results with the provenance of every file read (ADR 0006).

The two steps are separate so the program entry point can open the run log at paths.log
before anything is read: modules only log, the entry point configures logging (D19). A run
that fails on its inputs writes no .h5 file.

check() (step 6.5, `qm-etdac check`) reads and validates the inputs exactly as run() does,
including the rule that the three inputs contain the same samples, but calculates nothing and
writes nothing. It cannot find problems of the output folder, which only a run meets.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .config import ConfigMan
from .etdac_operations import Operations
from .gate_controler import Controler, default_data_root
from .outputs import OutputPaths, prepare_outputs, write_etdac_h5
from .validation import check_same_hashes

POP_INDEX = "num-1"  # index column of the population files (atom number)
OSC_INDEX = "virt\\core"  # index column of the oscillator-strength files (virtual MO)


@dataclass(frozen=True)
class Scheme:
    """
    Runs the ETDAC calculation for the settings of one run.

    Attributes:
        config: which list files to read, and where they are (ConfigMan).
        operations: calculation options (default: Operations(), core matrix trimmed, ADR 0002).
    """

    config: ConfigMan
    operations: Operations = field(default_factory=Operations)

    def prepare_outputs(self) -> OutputPaths:
        """Create `etdac_outputs` in the logs folder and keep any earlier result; returns the paths to write."""
        return prepare_outputs(self.config.output_dir())

    def run(self, paths: OutputPaths) -> dict[str, pd.DataFrame]:
        """
        Read the inputs, calculate every sample and write the results to paths.h5.

        Args:
            paths: from prepare_outputs().
        Returns:
            {hash: ETDAC matrix}, as written to the file.
        Raises:
            InputError: the inputs break the input rules; nothing is written.
            OutputError: the result cannot be written without overwriting.
        """
        reader, core, virt, etrans = self._read()
        results = self.operations.etdac_batch(core, virt, etrans)
        write_etdac_h5(results, paths.h5, reader.inputs_read)
        return results

    def check(self) -> int:
        """
        Read and validate the inputs as run() does; calculate and write nothing.

        Returns:
            The number of samples, present in all three inputs.
        Raises:
            InputError: the inputs break the input rules.
        """
        _, core, virt, etrans = self._read()
        check_same_hashes({"core populations": core, "virtual populations": virt, "oscillator strengths": etrans})
        return len(virt)

    def _read(self) -> tuple[Controler, dict[str, pd.DataFrame], dict[str, pd.DataFrame], dict[str, pd.DataFrame]]:
        """One Controler reads the three list files and their CSV files (path policy and input rules)."""
        reader = Controler(default_data_root(self.config.logspath))
        files = self.config.list_files()
        core = reader.load_dict_data(files.core, POP_INDEX)
        virt = reader.load_dict_data(files.virt, POP_INDEX)
        etrans = reader.load_dict_data(files.etrans, OSC_INDEX)
        return reader, core, virt, etrans
