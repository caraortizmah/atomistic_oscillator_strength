"""Shared test helpers and fixtures.

Inputs are built from CSV text with pandas.read_csv, so their dtypes are exactly
what the loader produces from real parser files (string MO labels in the header,
integer atom / virtual-MO labels in the index column).
"""

from __future__ import annotations

import io
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
import pytest

DATA_DIR = Path(__file__).parent / "data" / "phe_tyr"
REFERENCE_H5 = DATA_DIR / "reference" / "data_etdac_matrix_3.5-11.0A.h5"

POP_INDEX = "num-1"  # index column of population files (atom number)
OSC_INDEX = "virt\\core"  # index column of oscillator-strength files (virtual MO)


def frame_from_csv(text: str, index_col: str) -> pd.DataFrame:
    """Parse CSV text exactly like the loader parses a parser output file."""
    return pd.read_csv(io.StringIO(text.strip() + "\n"), delimiter=",", index_col=index_col)


def read_etdac_h5(path: Path) -> dict[str, pd.DataFrame]:
    """Read an ETDAC .h5 file (one group sample_<hash> per sample) into DataFrames."""
    out: dict[str, pd.DataFrame] = {}
    with h5py.File(path, "r") as f:
        for group_name in f:
            group = f[group_name]
            records = group["ETDAC_matrix"][()]
            index_field, *value_fields = records.dtype.names
            frame = pd.DataFrame(
                np.column_stack([records[name] for name in value_fields]),
                index=pd.Index(records[index_field], name=group.attrs["index_name"]),
                columns=pd.Index([int(name) for name in value_fields], name=group.attrs["column_name"]),
            )
            out[str(group.attrs["hash"])] = frame
    return out


def assert_etdac_equal(
    actual: dict[str, pd.DataFrame],
    expected: dict[str, pd.DataFrame],
    rtol: float = 1e-12,
    atol: float = 1e-15,
) -> None:
    """Same samples, same atom labels (rows and columns), same numbers within tolerance."""
    assert list(actual) == list(expected), "sample hashes differ (or their order)"
    for key in expected:
        a, e = actual[key], expected[key]
        assert a.index.name == "core-atom" and a.columns.name == "virtual-atom", key
        np.testing.assert_array_equal(a.index.to_numpy(), e.index.to_numpy(), err_msg=f"{key}: core atoms")
        np.testing.assert_array_equal(
            np.asarray(a.columns, dtype=np.int64),
            np.asarray(e.columns, dtype=np.int64),
            err_msg=f"{key}: virtual atoms",
        )
        np.testing.assert_allclose(a.to_numpy(dtype=float), e.to_numpy(dtype=float), rtol=rtol, atol=atol, err_msg=key)


@pytest.fixture
def phe_tyr_dir() -> Path:
    """Folder with the committed Phe-Tyr golden data set (see its README.md)."""
    return DATA_DIR
