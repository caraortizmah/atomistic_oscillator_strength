"""Layer 3: golden test on the real Phe-Tyr data set of the cited paper (3.5-11.0 A, 52 samples).

Inputs are read with the notebook's own loader (frozen copy), so this test isolates the
calculation. The end-to-end path through the package's loader is tested in step 5.
Reference: tests/data/phe_tyr/reference/data_etdac_matrix_3.5-11.0A.h5, cut from the
notebook's output (see tests/data/phe_tyr/README.md).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import OSC_INDEX, POP_INDEX, REFERENCE_H5, assert_etdac_equal, read_etdac_h5

import notebook_reference as nb
from qm_etdac_calculator.etdac_operations import Operations

EXPECTED_HASHES = [f"f{i}" for i in range(10, 62)]


@pytest.mark.golden
def test_phe_tyr_reproduces_reference(phe_tyr_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(phe_tyr_dir)  # list files hold paths relative to their own folder
    core = nb.load_dict_data("resA_MOcore_list.log", POP_INDEX)
    virt = nb.load_dict_data("resB_MOvirt_list.log", POP_INDEX)
    osc = nb.load_dict_data("corevirt_fosce_AB_list.log", OSC_INDEX)
    assert list(core) == EXPECTED_HASHES

    actual = Operations().etdac_batch(core, virt, osc)
    expected = read_etdac_h5(REFERENCE_H5)
    assert list(expected) == EXPECTED_HASHES
    assert_etdac_equal(actual, expected)
