"""Layer 2: the package computes exactly what the notebook computes.

Inputs are random but shaped like real parser output (deterministic: fixed seeds).
This checks the arithmetic, not the chemistry; chemistry is covered by the golden
test on the real Phe-Tyr data set. Random inputs include the awkward cases real data
can contain: all-zero MO columns, and MO labels present in one matrix but not the other.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from conftest import OSC_INDEX, POP_INDEX, assert_etdac_equal

import notebook_reference as nb
from qm_etdac_calculator.etdac_operations import Operations, etdac_matrix

SEEDS = range(5)
SAMPLES_PER_SEED = 4


def _population(rng: np.random.Generator, atoms: np.ndarray, mos: list[int], sym: str, lvl: str) -> pd.DataFrame:
    """Percent populations: each MO column sums to <= 100, rounded to 0.1 like the parser output."""
    values = rng.dirichlet(np.full(len(atoms), 0.3), size=len(mos)).T * rng.uniform(95, 100, size=len(mos))
    values = np.round(values, 1)
    values[:, rng.integers(len(mos))] = 0.0  # one all-zero MO column
    frame = pd.DataFrame(values, index=pd.Index(atoms, name=POP_INDEX), columns=[str(m) for m in mos])
    frame.insert(0, "lvl", lvl)
    frame.insert(0, "sym", sym)
    return frame


def _oscillator(rng: np.random.Generator, core_mos: list[int], virt_mos: list[int]) -> pd.DataFrame:
    """Sparse, small, non-negative strengths; labels overlap the population files only partly."""
    cols = sorted(rng.choice(core_mos, size=len(core_mos) - 3, replace=False).tolist()) + [max(core_mos) + 1]
    rows = sorted(rng.choice(virt_mos, size=len(virt_mos) - 2, replace=False).tolist()) + [max(virt_mos) + 1]
    values = rng.exponential(0.01, size=(len(rows), len(cols))) * (rng.random((len(rows), len(cols))) < 0.6)
    return pd.DataFrame(values, index=pd.Index(rows, name=OSC_INDEX), columns=[str(c) for c in cols])


def _random_batch(seed: int) -> tuple[dict, dict, dict]:
    rng = np.random.default_rng(seed)
    core, virt, osc = {}, {}, {}
    for i in range(SAMPLES_PER_SEED):
        core_atoms = np.sort(rng.choice(np.arange(1, 24), size=18, replace=False))
        core_mos = list(range(7, 25))
        virt_mos = sorted(rng.choice(np.arange(90, 125), size=int(rng.integers(14, 21)), replace=False).tolist())
        key = f"f{i:02d}"
        core[key] = _population(rng, core_atoms, core_mos, "C", "s")
        virt[key] = _population(rng, np.arange(47), virt_mos, "atom", "lvlMO")
        osc[key] = _oscillator(rng, core_mos, virt_mos)
    return core, virt, osc


def _notebook_pipeline(core: dict, virt: dict, osc: dict) -> dict:
    """The notebook's sequence: trim core, heatmap_ETDAC, then the two formatting loops."""
    osc_copy = {k: v.copy() for k, v in osc.items()}  # the notebook mutates this input
    return nb.format_heatmaps(nb.heatmap_ETDAC(nb.remove_noncontrb(core), virt, osc_copy))


@pytest.mark.parametrize("seed", SEEDS)
def test_etdac_batch_matches_notebook(seed: int) -> None:
    core, virt, osc = _random_batch(seed)
    expected = _notebook_pipeline(core, virt, osc)
    actual = Operations().etdac_batch(core, virt, osc)
    assert_etdac_equal(actual, expected)


@pytest.mark.parametrize("seed", SEEDS)
def test_etdac_matrix_matches_notebook_kernel(seed: int) -> None:
    """Single-sample kernel against ts_psb_acore_bvirt (the function to vectorise in step 7)."""
    core, virt, osc = _random_batch(seed)
    for key in core:
        acore = nb.remove_noncontrb({key: core[key]})[key].T[2:].T
        bvirt = virt[key].T[2:].T
        expected = nb.ts_psb_acore_bvirt(acore, bvirt, osc[key].copy())
        actual = etdac_matrix(acore, bvirt, osc[key])
        np.testing.assert_array_equal(actual.index.to_numpy(), expected.index.to_numpy())
        np.testing.assert_array_equal(np.asarray(actual.columns), np.asarray(expected.columns))
        np.testing.assert_allclose(actual.to_numpy(dtype=float), expected.to_numpy(dtype=float), rtol=1e-12, atol=1e-15)
