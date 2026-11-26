"""Layer 1: tiny cases whose expected ETDAC matrix can be checked with pencil and paper.

The ETDAC matrix of one sample (ADR 0002):

    step 1:  T[a, v] = sum_c  core_pop[a, c] * osc[v, c] / 100   over core MOs c shared by both
    step 2:  E[a, b] = sum_v  T[a, v] * virt_pop[b, v]           over virtual MOs v shared by both

a = core atom, b = virtual atom. Populations are in percent; only step 1 is divided by 100.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from conftest import OSC_INDEX, POP_INDEX, frame_from_csv

from qm_etdac_calculator.etdac_operations import Operations, nonzero_mo_matrix, remove_noncontrb


def _batch(core: str, virt: str, osc: str, **options: bool) -> pd.DataFrame:
    result = Operations(**options).etdac_batch(
        {"s1": frame_from_csv(core, POP_INDEX)},
        {"s1": frame_from_csv(virt, POP_INDEX)},
        {"s1": frame_from_csv(osc, OSC_INDEX)},
    )
    assert list(result) == ["s1"]
    return result["s1"]


# Case A: one core MO, one virtual MO.
#   T = [60*0.5/100, 40*0.5/100] = [0.30, 0.20]
#   E = [[0.30*0.3, 0.30*0.7], [0.20*0.3, 0.20*0.7]]
CASE_A = dict(
    core="""
num-1,sym,lvl,7
1,C,s,60.0
2,C,s,40.0
""",
    osc="""
virt\\core,7
92,0.5
""",
    virt="""
num-1,sym,lvl,92
0,atom,lvlMO,0.3
1,atom,lvlMO,0.7
""",
)

# Case B: the quirks of real data.
#   core MO 8 is all zero          -> removed by the core trimming (no numeric effect)
#   core MO 9 has no transitions   -> not in osc, contributes nothing
#   virtual MO 95 is all zero      -> kept (virtual matrix is never trimmed), contributes 0
#   T(atom 1) = [60*0.5, 60*0.2, 60*0.4]/100 = [0.30, 0.12, 0.24]   for v = 92, 93, 95
#   T(atom 2) = [40*0.5, 40*0.2, 40*0.4]/100 = [0.20, 0.08, 0.16]
#   E[1,0] = 0.30*0.3 + 0.12*1.0 + 0.24*0 = 0.21     E[1,1] = 0.30*0.7 = 0.21
#   E[2,0] = 0.20*0.3 + 0.08*1.0 + 0.16*0 = 0.14     E[2,1] = 0.20*0.7 = 0.14
CASE_B = dict(
    core="""
num-1,sym,lvl,7,8,9
1,C,s,60.0,0.0,20.0
2,C,s,40.0,0.0,80.0
""",
    osc="""
virt\\core,7,8
92,0.5,0.9
93,0.2,0.0
95,0.4,0.0
""",
    virt="""
num-1,sym,lvl,92,93,95
0,atom,lvlMO,0.3,1.0,0.0
1,atom,lvlMO,0.7,0.0,0.0
""",
)


def test_case_a_single_transition() -> None:
    result = _batch(**CASE_A)
    assert result.index.name == "core-atom"
    assert result.columns.name == "virtual-atom"
    assert list(result.index) == [1, 2]
    assert [int(c) for c in result.columns] == [0, 1]
    np.testing.assert_allclose(result.to_numpy(dtype=float), [[0.09, 0.21], [0.06, 0.14]], rtol=1e-12)


def test_case_b_zero_columns_and_unshared_labels() -> None:
    result = _batch(**CASE_B)
    np.testing.assert_allclose(result.to_numpy(dtype=float), [[0.21, 0.21], [0.14, 0.14]], rtol=1e-12)


def test_rows_are_sorted_by_core_atom() -> None:
    """Case A with the core atoms listed in reverse order: output rows still come out 1, 2."""
    reversed_core = """
num-1,sym,lvl,7
2,C,s,40.0
1,C,s,60.0
"""
    result = _batch(core=reversed_core, virt=CASE_A["virt"], osc=CASE_A["osc"])
    assert list(result.index) == [1, 2]
    np.testing.assert_allclose(result.to_numpy(dtype=float), [[0.09, 0.21], [0.06, 0.14]], rtol=1e-12)


def test_core_trimming_is_a_safeguard_without_numeric_effect() -> None:
    """ADR 0002: trimming all-zero core MO columns must not change the result."""
    trimmed = _batch(**CASE_B)
    untrimmed = _batch(**CASE_B, trim_core=False)
    np.testing.assert_allclose(trimmed.to_numpy(dtype=float), untrimmed.to_numpy(dtype=float), rtol=0, atol=0)


def test_default_options_trim_core() -> None:
    assert Operations().trim_core is True


def test_nonzero_mo_matrix_removes_only_all_zero_columns() -> None:
    """Pins the documented limit (ADR 0002): an all-NaN column is NOT removed."""
    df = frame_from_csv(
        """
num-1,sym,lvl,7,8,9,10
1,C,s,0.0,,,50.0
2,C,s,0.0,,0.0,50.0
""",
        POP_INDEX,
    )
    assert list(nonzero_mo_matrix(df).columns) == ["sym", "lvl", "8", "9", "10"]


def test_remove_noncontrb_applies_to_every_sample() -> None:
    df = frame_from_csv(CASE_B["core"], POP_INDEX)
    trimmed = remove_noncontrb({"x": df, "y": df})
    assert list(trimmed) == ["x", "y"]
    assert all(list(t.columns) == ["sym", "lvl", "7", "9"] for t in trimmed.values())


def test_inputs_are_not_modified() -> None:
    """The notebook's ts_psb_acore_bvirt changes its input's index in place; the package must not."""
    core = {"s1": frame_from_csv(CASE_B["core"], POP_INDEX)}
    virt = {"s1": frame_from_csv(CASE_B["virt"], POP_INDEX)}
    osc = {"s1": frame_from_csv(CASE_B["osc"], OSC_INDEX)}
    before = {name: {k: v.copy(deep=True) for k, v in d.items()} for name, d in (("core", core), ("virt", virt), ("osc", osc))}
    Operations().etdac_batch(core, virt, osc)
    for name, d in (("core", core), ("virt", virt), ("osc", osc)):
        pd.testing.assert_frame_equal(d["s1"], before[name]["s1"], check_exact=True, obj=name)
