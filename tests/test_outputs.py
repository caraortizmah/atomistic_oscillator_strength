"""Output folder and rotation of existing results (step 5e, commit 1; ADR 0003).

A run writes a pair of files, `<stem>.h5` and `<stem>.log`, into the output folder. An
existing pair is never overwritten: it is renamed `<stem>_oldversionN<ext>` (N = highest
existing number + 1, the same N for both files) and a WARNING says so.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from qm_etdac_calculator.errors import OutputError
from qm_etdac_calculator.outputs import DEFAULT_STEM, OutputPaths, prepare_outputs

STEM = DEFAULT_STEM


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
