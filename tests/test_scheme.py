"""Orchestration of a run (step 5f-2): Scheme reads, calculates and writes, in that order.

Scheme is used in two steps (decision of step 5f): prepare_outputs() first, so the CLI can
open the run log before anything is read (step 6), then run(paths). Since step 6.2 the
results go to `etdac_outputs` inside the logs folder (ADR 0007), so every test works on a
copy of the Phe-Tyr folder and never writes into tests/data/.
"""

from __future__ import annotations

import hashlib
import json
import shutil
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


@pytest.fixture
def project(phe_tyr_dir: Path, tmp_path: Path) -> Path:
    """A copy of the Phe-Tyr folder: list files and inputs/ (the reference/ folder is not needed)."""
    copy = tmp_path / "phe_tyr"
    shutil.copytree(phe_tyr_dir, copy, ignore=shutil.ignore_patterns("reference"))
    return copy


def _scheme(logs: Path, **options: Operations) -> Scheme:
    return Scheme(ConfigMan(**LIST_FILES, logspath=str(logs)), **options)


def _files(root: Path) -> dict[str, str]:
    """Every file below root, with the SHA-256 of its content."""
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob("*") if p.is_file()}


def test_prepare_outputs_uses_etdac_outputs_in_the_logs_folder_and_writes_nothing(project: Path) -> None:
    paths = _scheme(project).prepare_outputs()
    output = (project / "etdac_outputs").resolve()
    assert (paths.h5.parent, paths.log.parent) == (output, output)
    assert list(output.iterdir()) == []


@pytest.mark.golden
def test_phe_tyr_run_reproduces_the_reference(project: Path) -> None:
    """End to end through the package: settings, reading, calculation, writing."""
    scheme = _scheme(project)
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


def test_a_run_writes_only_its_result_into_etdac_outputs(project: Path) -> None:
    """Least privilege for writing (ADR 0007): nothing else in the data root is created or changed."""
    data_root = project.parent
    before = _files(data_root)
    scheme = _scheme(project)
    scheme.run(scheme.prepare_outputs())
    after = _files(data_root)
    assert set(after) - set(before) == {"phe_tyr/etdac_outputs/data_etdac_matrix.h5"}
    assert {name: after[name] for name in before} == before


def test_an_input_error_leaves_no_result(project: Path) -> None:
    scheme = Scheme(ConfigMan(**{**LIST_FILES, "virtpop": "missing_list.log"}, logspath=str(project)))
    paths = scheme.prepare_outputs()
    with pytest.raises(InputError, match="list file not found"):
        scheme.run(paths)
    assert list((project / "etdac_outputs").iterdir()) == []  # no .h5, no temporary file


class _RecordingOperations(Operations):
    """Operations that remember which inputs they received."""

    def etdac_batch(self, core, virt, etrans):  # type: ignore[no-untyped-def]
        object.__setattr__(self, "received", (list(core), list(virt), list(etrans)))
        return super().etdac_batch(core, virt, etrans)


def test_the_given_operations_are_used(project: Path) -> None:
    operations = _RecordingOperations(trim_core=False)
    scheme = _scheme(project, operations=operations)
    results = scheme.run(scheme.prepare_outputs())
    hashes = [f"f{i}" for i in range(10, 62)]
    assert operations.received == (hashes, hashes, hashes)  # type: ignore[attr-defined]
    assert all(isinstance(matrix, pd.DataFrame) for matrix in results.values())


def test_default_operations_trim_the_core_matrix(project: Path) -> None:
    assert _scheme(project).operations == Operations(trim_core=True)
