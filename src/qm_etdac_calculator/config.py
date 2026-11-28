"""
Run settings of an ETDAC calculation: which three list files to read and where to write.

ConfigMan holds the five settings of a run under the documented keys (the keys of
`qm-etdac auto` JSON files), so `ConfigMan(**settings)` builds it from such a dict:

- corepop: list file of the core-MO population files
- virtpop: list file of the virtual-MO population files
- etranscv: list file of the core-electron transition intensity files
  (oscillator strengths, core to virtual MOs)
- logspath: folder that contains the three list files
- outputpath: output folder for the results (default `etdac_outputs`, ADR 0003)

ConfigMan only holds settings; it opens no file. The list files and every file they name
are checked when Controler reads them (path policy, ADR 0003/0004), so there is one place
that decides what may be read. A missing or unknown key is a TypeError from the constructor;
reading a JSON file and reporting its mistakes to users is step 6 (CLI).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

from .outputs import DEFAULT_OUTPUT_DIR


class ListFiles(NamedTuple):
    """The three list files of a run, in the order the calculation uses them."""

    core: Path
    virt: Path
    etrans: Path


@dataclass(frozen=True)
class ConfigMan:
    """The settings of one run; frozen, so they cannot change while the run uses them."""

    corepop: str
    virtpop: str
    etranscv: str
    logspath: str
    outputpath: str = DEFAULT_OUTPUT_DIR

    def list_files(self) -> ListFiles:
        """The three list files, as paths inside the logs folder (not checked here)."""
        logs = Path(self.logspath)
        return ListFiles(core=logs / self.corepop, virt=logs / self.virtpop, etrans=logs / self.etranscv)
