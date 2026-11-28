"""Orchestration of a run (step 5f-2): Scheme reads, calculates and writes, in that order.

Scheme is used in two steps (decision of step 5f): prepare_outputs() first, so the CLI can
open the run log before anything is read (step 6), then run(paths).
"""

from __future__ import annotations

import json
from pathlib import Path

import h5py
import pandas as pd
import pytest
from conftest import REFERENCE_H5, assert_etdac_equal, read_etdac_h5

from qm_etdac_calculator import ConfigMan, InputError, Operations, Scheme

LIST_FILES = {
    "corepop": "resA_MOcore_list.log",
    "virtpop": "resB_MOvirt_list.log",
    "etranscv": "corevirt_fosce_AB_list.log",
}


def _scheme(logs: Path, output: Path, **options: Operations) -> Scheme:
    return Scheme(ConfigMan(**LIST_FILES, logspath=str(logs), outputpath=str(output)), **options)


def test_prepare_outputs_uses_the_configured_folder_and_writes_nothing(phe_tyr_dir: Path, tmp_path: Path) -> None:
    output = tmp_path / "results"
    paths = _scheme(phe_tyr_dir, output).prepare_outputs()
    assert (paths.h5.parent, paths.log.parent) == (output.resolve(), output.resolve())
    assert list(output.iterdir()) == []


@pytest.mark.golden
def test_phe_tyr_run_reproduces_the_reference(phe_tyr_dir: Path, tmp_path: Path) -> None:
    """End to end through the package: settings, reading, calculation, writing."""
    scheme = _scheme(phe_tyr_dir, tmp_path / "etdac_outputs")
    paths = scheme.prepare_outputs()
    results = scheme.run(paths)

    expected = read_etdac_h5(REFERENCE_H5)
    assert_etdac_equal(results, expected)
    assert_etdac_equal(read_etdac_h5(paths.h5), expected)
    with h5py.File(paths.h5, "r") as f:
        recorded = json.loads(f.attrs["input_files"])
    assert len(recorded) == 3 + 3 * 52  # one reader records the three list files and every CSV
    assert [r["path"] for r in recorded if r["path"].endswith(".log")] == [
        "phe_tyr/resA_MOcore_list.log",
        "phe_tyr/resB_MOvirt_list.log",
        "phe_tyr/corevirt_fosce_AB_list.log",
    ]


def test_an_input_error_leaves_no_result(phe_tyr_dir: Path, tmp_path: Path) -> None:
    output = tmp_path / "etdac_outputs"
    scheme = Scheme(ConfigMan(**{**LIST_FILES, "virtpop": "missing_list.log"}, logspath=str(phe_tyr_dir), outputpath=str(output)))
    paths = scheme.prepare_outputs()
    with pytest.raises(InputError, match="list file not found"):
        scheme.run(paths)
    assert list(output.iterdir()) == []  # no .h5, no temporary file


class _RecordingOperations(Operations):
    """Operations that remember which inputs they received."""

    def etdac_batch(self, core, virt, etrans):  # type: ignore[no-untyped-def]
        object.__setattr__(self, "received", (list(core), list(virt), list(etrans)))
        return super().etdac_batch(core, virt, etrans)


def test_the_given_operations_are_used(phe_tyr_dir: Path, tmp_path: Path) -> None:
    operations = _RecordingOperations(trim_core=False)
    scheme = _scheme(phe_tyr_dir, tmp_path / "out", operations=operations)
    results = scheme.run(scheme.prepare_outputs())
    hashes = [f"f{i}" for i in range(10, 62)]
    assert operations.received == (hashes, hashes, hashes)  # type: ignore[attr-defined]
    assert all(isinstance(matrix, pd.DataFrame) for matrix in results.values())


def test_default_operations_trim_the_core_matrix(phe_tyr_dir: Path, tmp_path: Path) -> None:
    assert _scheme(phe_tyr_dir, tmp_path).operations == Operations(trim_core=True)
