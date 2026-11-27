"""Output folder and rotation of existing results (step 5e, commit 1; ADR 0003).

A run writes a pair of files, `<stem>.h5` and `<stem>.log`, into the output folder. An
existing pair is never overwritten: it is renamed `<stem>_oldversionN<ext>` (N = highest
existing number + 1, the same N for both files) and a WARNING says so.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
import pytest
from conftest import POP_INDEX, OSC_INDEX, REFERENCE_H5

import notebook_reference as nb
from qm_etdac_calculator.errors import OutputError
from qm_etdac_calculator.etdac_operations import Operations
from qm_etdac_calculator.gate_controler import Controler, InputRecord, default_data_root
from qm_etdac_calculator import __version__
from qm_etdac_calculator.outputs import DEFAULT_STEM, OutputPaths, prepare_outputs, write_etdac_h5

STEM = DEFAULT_STEM
INPUTS = (InputRecord("logs/list.log", "a" * 64), InputRecord("logs/inputs/a.csv", "b" * 64))


@pytest.fixture(autouse=True)
def _capture_package_logs(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger="qm_etdac_calculator")


def _warnings(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]


def _touch(folder: Path, *names: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for name in names:
        (folder / name).write_text(name)  # content = original name, to follow renames


def _names(folder: Path) -> set[str]:
    return {p.name for p in folder.iterdir()}


# --- folder ----------------------------------------------------------------------------


def test_default_stem_is_the_documented_name() -> None:
    assert DEFAULT_STEM == "data_etdac_matrix"


def test_missing_output_folder_is_created_with_parents(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    out = tmp_path / "a" / "etdac_outputs"
    paths = prepare_outputs(out)
    assert out.is_dir()
    assert paths == OutputPaths(h5=out.resolve() / f"{STEM}.h5", log=out.resolve() / f"{STEM}.log")
    assert not paths.h5.exists() and not paths.log.exists()  # prepared, not written
    assert _warnings(caplog) == []


def test_empty_existing_folder_gives_no_warning(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    prepare_outputs(tmp_path)
    assert _names(tmp_path) == set()
    assert _warnings(caplog) == []


def test_output_path_that_is_a_file_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "etdac_outputs"
    target.write_text("not a folder")
    with pytest.raises(OutputError, match="is not a folder"):
        prepare_outputs(target)


def test_output_folder_that_is_a_symlink_is_rejected(tmp_path: Path) -> None:
    """A planted link would send the results somewhere else (CWE-59)."""
    (tmp_path / "elsewhere").mkdir()
    (tmp_path / "etdac_outputs").symlink_to(tmp_path / "elsewhere")
    with pytest.raises(OutputError, match="is a symbolic link"):
        prepare_outputs(tmp_path / "etdac_outputs")
    assert _names(tmp_path / "elsewhere") == set()


@pytest.mark.parametrize("stem", ["", "a/b", "../x", "x.h5", " x", "x y", "-x", "\u00e9", "a" * 65])
def test_invalid_stem_is_rejected(tmp_path: Path, stem: str) -> None:
    with pytest.raises(OutputError, match="invalid output name"):
        prepare_outputs(tmp_path, stem)
    assert _names(tmp_path) == set()


@pytest.mark.parametrize("stem", ["x", "run_01", "Phe-Tyr", "a" * 64])
def test_valid_stems_are_accepted(tmp_path: Path, stem: str) -> None:
    assert prepare_outputs(tmp_path, stem).h5.name == f"{stem}.h5"


# --- rotation ----------------------------------------------------------------------------


def test_existing_result_is_kept_as_oldversion1_with_one_warning(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    _touch(tmp_path, f"{STEM}.h5")
    prepare_outputs(tmp_path)
    assert _names(tmp_path) == {f"{STEM}_oldversion1.h5"}
    assert (tmp_path / f"{STEM}_oldversion1.h5").read_text() == f"{STEM}.h5"
    warnings = _warnings(caplog)
    assert len(warnings) == 1
    assert f"'{STEM}.h5' already exists" in warnings[0]
    assert f"kept as '{STEM}_oldversion1.h5'" in warnings[0]
    assert "may come from another job or system" in warnings[0]
    assert "check that this is the right output folder" in warnings[0]


def test_result_and_log_are_rotated_as_a_pair_with_one_warning(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    _touch(tmp_path, f"{STEM}.h5", f"{STEM}.log")
    prepare_outputs(tmp_path)
    assert _names(tmp_path) == {f"{STEM}_oldversion1.h5", f"{STEM}_oldversion1.log"}
    warnings = _warnings(caplog)
    assert len(warnings) == 1
    assert f"'{STEM}.h5', '{STEM}.log' already exist" in warnings[0]


def test_log_alone_is_rotated_too(tmp_path: Path) -> None:
    """A run that failed before writing results still leaves its log; it is kept, not overwritten."""
    _touch(tmp_path, f"{STEM}.log")
    prepare_outputs(tmp_path)
    assert _names(tmp_path) == {f"{STEM}_oldversion1.log"}


def test_next_number_is_highest_plus_one_and_gaps_stay(tmp_path: Path) -> None:
    _touch(tmp_path, f"{STEM}.h5", f"{STEM}_oldversion1.h5", f"{STEM}_oldversion3.h5")
    prepare_outputs(tmp_path)
    assert f"{STEM}_oldversion4.h5" in _names(tmp_path)
    assert f"{STEM}_oldversion2.h5" not in _names(tmp_path)


def test_pair_shares_one_number_counted_over_both_extensions(tmp_path: Path) -> None:
    _touch(tmp_path, f"{STEM}.h5", f"{STEM}.log", f"{STEM}_oldversion1.h5", f"{STEM}_oldversion2.log")
    prepare_outputs(tmp_path)
    assert {f"{STEM}_oldversion3.h5", f"{STEM}_oldversion3.log"} <= _names(tmp_path)


def test_existing_oldversions_are_never_touched(tmp_path: Path) -> None:
    _touch(tmp_path, f"{STEM}.h5", f"{STEM}_oldversion1.h5", f"{STEM}_oldversion1.log")
    before = {name: (tmp_path / name).stat().st_mtime_ns for name in (f"{STEM}_oldversion1.h5", f"{STEM}_oldversion1.log")}
    prepare_outputs(tmp_path)
    for name, mtime in before.items():
        assert (tmp_path / name).read_text() == name
        assert (tmp_path / name).stat().st_mtime_ns == mtime


@pytest.mark.parametrize(
    "name",
    [
        "other_oldversion9.h5",  # another stem
        f"{STEM}_oldversion02.h5",  # leading zero: not written by this program
        f"{STEM}_oldversion9.txt",  # other extension
        f"{STEM}_oldversion9.h5.bak",
        f"x{STEM}_oldversion9.h5",
    ],
)
def test_unrelated_files_do_not_change_the_number(tmp_path: Path, name: str) -> None:
    _touch(tmp_path, f"{STEM}.h5", name)
    prepare_outputs(tmp_path)
    assert _names(tmp_path) == {f"{STEM}_oldversion1.h5", name}


def test_other_stems_are_independent(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    _touch(tmp_path, f"{STEM}.h5")
    prepare_outputs(tmp_path, "other")
    assert _names(tmp_path) == {f"{STEM}.h5"}
    assert _warnings(caplog) == []


def test_rotation_never_overwrites_even_in_a_race(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """If the target name appears between choosing N and renaming, the rename fails instead of overwriting."""
    import qm_etdac_calculator.outputs as outputs

    _touch(tmp_path, f"{STEM}.h5")
    real = outputs._next_number

    def racing(folder: Path, stem: str) -> int:
        number = real(folder, stem)
        (folder / f"{stem}_oldversion{number}.h5").write_text("other run")  # another process wins the race
        return number

    monkeypatch.setattr(outputs, "_next_number", racing)
    with pytest.raises(OutputError, match="already exists"):
        prepare_outputs(tmp_path)
    assert (tmp_path / f"{STEM}_oldversion1.h5").read_text() == "other run"
    assert (tmp_path / f"{STEM}.h5").read_text() == f"{STEM}.h5"  # the original is still there



# --- writing the .h5 file (step 5e, commit 2) ----------------------------------------------


def _h5_content(path: Path) -> dict[str, Any]:
    """Everything a reader can see in an ETDAC file: groups, dataset dtype, values, compression, attributes."""
    with h5py.File(path, "r") as f:
        return {
            name: {
                "dtype": f[name]["ETDAC_matrix"].dtype,
                "records": f[name]["ETDAC_matrix"][()],
                "compression": f[name]["ETDAC_matrix"].compression,
                "attrs": dict(f[name].attrs),
            }
            for name in f
        }


def _assert_same_content(actual: Path, expected: Path) -> None:
    got, want = _h5_content(actual), _h5_content(expected)
    assert list(got) == list(want)
    for name in want:
        assert got[name]["dtype"] == want[name]["dtype"], name
        assert np.array_equal(got[name]["records"], want[name]["records"]), name
        assert got[name]["compression"] == want[name]["compression"] == "gzip", name
        assert got[name]["attrs"] == want[name]["attrs"], name


def _small_results() -> dict[str, pd.DataFrame]:
    def frame(values: list[list[float]]) -> pd.DataFrame:
        return pd.DataFrame(
            values,
            index=pd.Index([0, 1], name="core-atom"),
            columns=pd.Index([0, 1], name="virtual-atom"),
        )

    return {"f10": frame([[0.09, 0.21], [0.06, 0.14]]), "f11": frame([[0.0, 1e-6], [2.5, 0.0]])}


def test_written_file_has_the_notebook_layout(tmp_path: Path) -> None:
    """Differential test: same groups, dtypes, values, compression and attributes as the notebook's save."""
    results = _small_results()
    nb.save_ETDAC_matrix(results, data_set_name=str(tmp_path / "notebook.h5"))
    paths = prepare_outputs(tmp_path / "out")
    write_etdac_h5(results, paths.h5, INPUTS)
    _assert_same_content(paths.h5, tmp_path / "notebook.h5")


@pytest.mark.golden
def test_phe_tyr_written_through_the_package_equals_the_reference(phe_tyr_dir: Path, tmp_path: Path) -> None:
    """End to end except orchestration: package loader, calculation, writer; byte-level content of the reference."""
    controler = Controler(default_data_root(phe_tyr_dir))
    core = controler.load_dict_data(phe_tyr_dir / "resA_MOcore_list.log", POP_INDEX)
    virt = controler.load_dict_data(phe_tyr_dir / "resB_MOvirt_list.log", POP_INDEX)
    osc = controler.load_dict_data(phe_tyr_dir / "corevirt_fosce_AB_list.log", OSC_INDEX)
    paths = prepare_outputs(tmp_path / "etdac_outputs")
    write_etdac_h5(Operations().etdac_batch(core, virt, osc), paths.h5, controler.inputs_read)
    _assert_same_content(paths.h5, REFERENCE_H5)  # groups only: the reference has no file-level attributes
    with h5py.File(paths.h5, "r") as f:
        recorded = json.loads(f.attrs["input_files"])
    assert len(recorded) == 3 + 3 * 52  # three list files, one CSV per sample in each
    assert recorded[0]["path"] == "phe_tyr/resA_MOcore_list.log"
    first_csv = next(r for r in recorded if r["path"].endswith(".csv"))
    assert first_csv["sha256"] == hashlib.sha256((phe_tyr_dir.parent / first_csv["path"]).read_bytes()).hexdigest()


def test_successful_write_leaves_only_the_result(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    paths = prepare_outputs(tmp_path)
    write_etdac_h5(_small_results(), paths.h5, INPUTS)
    assert _names(tmp_path) == {f"{STEM}.h5"}
    assert any("wrote 2 sample(s) to" in r.getMessage() for r in caplog.records if r.levelno == logging.INFO)


def test_existing_target_is_never_overwritten(tmp_path: Path) -> None:
    target = tmp_path / f"{STEM}.h5"
    target.write_text("previous result")
    with pytest.raises(OutputError, match="already exists"):
        write_etdac_h5(_small_results(), target, INPUTS)
    assert target.read_text() == "previous result"
    assert _names(tmp_path) == {f"{STEM}.h5"}  # no temporary file left behind


def test_existing_target_fails_before_anything_is_written(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail fast: no time spent writing a large file that can never be published."""
    import qm_etdac_calculator.outputs as outputs

    (tmp_path / f"{STEM}.h5").write_text("previous result")
    monkeypatch.setattr(outputs, "_write_groups", lambda *a: pytest.fail("wrote despite an existing target"))
    with pytest.raises(OutputError, match="never overwritten"):
        write_etdac_h5(_small_results(), tmp_path / f"{STEM}.h5", INPUTS)


def test_target_appearing_during_the_write_is_not_overwritten(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Another run publishes the same name while this one is writing: this run fails, the other result survives."""
    import qm_etdac_calculator.outputs as outputs

    target = tmp_path / f"{STEM}.h5"
    real = outputs._write_groups

    def racing(results: Any, temporary: Path, attrs: Any) -> None:
        real(results, temporary, attrs)
        target.write_text("other run")

    monkeypatch.setattr(outputs, "_write_groups", racing)
    with pytest.raises(OutputError, match="already exists"):
        write_etdac_h5(_small_results(), target, INPUTS)
    assert target.read_text() == "other run"
    assert _names(tmp_path) == {f"{STEM}.h5"}


def test_failed_write_leaves_nothing_behind(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A crash while writing must not leave a half-written result or a temporary file."""
    import qm_etdac_calculator.outputs as outputs

    def crash(results: Any, temporary: Path, attrs: Any) -> None:
        temporary.write_bytes(b"half")
        raise RuntimeError("disk full")

    monkeypatch.setattr(outputs, "_write_groups", crash)
    with pytest.raises(RuntimeError, match="disk full"):
        write_etdac_h5(_small_results(), tmp_path / f"{STEM}.h5", INPUTS)
    assert _names(tmp_path) == set()


def test_temporary_file_is_hidden_and_in_the_same_folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Same folder: os.link cannot cross filesystems. Hidden name: never mistaken for a result."""
    import qm_etdac_calculator.outputs as outputs

    seen: list[Path] = []
    real = outputs._write_groups

    def spy(results: Any, temporary: Path, attrs: Any) -> None:
        seen.append(temporary)
        real(results, temporary, attrs)

    monkeypatch.setattr(outputs, "_write_groups", spy)
    write_etdac_h5(_small_results(), tmp_path / f"{STEM}.h5", INPUTS)
    assert seen[0].parent == tmp_path
    assert seen[0].name.startswith(f".{STEM}.h5.") and seen[0].name.endswith(".tmp")


def test_empty_results_are_a_program_error(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no results to write"):
        write_etdac_h5({}, tmp_path / f"{STEM}.h5", INPUTS)
    assert _names(tmp_path) == set()


@pytest.mark.parametrize("key", ["a/b", "", "f 10", "../x"])
def test_sample_keys_must_be_valid_hashes(tmp_path: Path, key: str) -> None:
    """A '/' in a key would create nested groups; keys come from validated hashes, so this is a program error."""
    results = _small_results()
    results[key] = results.pop("f10")
    with pytest.raises(ValueError, match="invalid sample hash"):
        write_etdac_h5(results, tmp_path / f"{STEM}.h5", INPUTS)
    assert _names(tmp_path) == set()


# --- provenance attributes (step 5e, commit 3; ADR 0006) -----------------------------------


def _file_attrs(path: Path) -> dict[str, Any]:
    with h5py.File(path, "r") as f:
        return dict(f.attrs)


def test_written_file_carries_provenance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import qm_etdac_calculator.outputs as outputs

    monkeypatch.setattr(outputs, "_utc_now", lambda: "2026-11-27T19:30:00Z")
    paths = prepare_outputs(tmp_path)
    write_etdac_h5(_small_results(), paths.h5, INPUTS)
    attrs = _file_attrs(paths.h5)
    assert set(attrs) == {"program", "program_version", "created_utc", "input_files"}
    assert attrs["program"] == "qm_etdac_calculator"
    assert attrs["program_version"] == __version__
    assert attrs["created_utc"] == "2026-11-27T19:30:00Z"
    assert json.loads(attrs["input_files"]) == [
        {"path": "logs/list.log", "sha256": "a" * 64},
        {"path": "logs/inputs/a.csv", "sha256": "b" * 64},
    ]


def test_creation_time_is_utc_iso8601_to_the_second(tmp_path: Path) -> None:
    paths = prepare_outputs(tmp_path)
    write_etdac_h5(_small_results(), paths.h5, INPUTS)
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", _file_attrs(paths.h5)["created_utc"])


def test_input_files_is_real_json_whatever_the_file_names(tmp_path: Path) -> None:
    """Built with a JSON serialiser, never by concatenation (ADR 0005, context-aware output)."""
    tricky = (InputRecord('in/a"b\\c,d\u00e9.csv', "c" * 64), InputRecord("in/x\"]}, {\"path\": \"evil", "d" * 64))
    paths = prepare_outputs(tmp_path)
    write_etdac_h5(_small_results(), paths.h5, tricky)
    text = _file_attrs(paths.h5)["input_files"]
    assert text.isascii()  # non-ASCII names are escaped (\uXXXX): safe for any later reader
    assert [tuple(r.values()) for r in json.loads(text)] == [tuple(r) for r in tricky]


def test_writing_without_inputs_is_a_program_error(tmp_path: Path) -> None:
    """A result without provenance cannot be traced; every run reads at least its list files."""
    with pytest.raises(ValueError, match="no input files recorded"):
        write_etdac_h5(_small_results(), tmp_path / f"{STEM}.h5", ())
    assert _names(tmp_path) == set()
