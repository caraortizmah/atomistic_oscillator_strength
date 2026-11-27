"""Reading list files: format (step 5c, bullet 1), path policy (bullet 2), loading CSVs (bullet 3).

A list file has one `hash,path` entry per line. These tests pin how the reader treats
editing leftovers (UTF-8 BOM, line endings, blank lines) and malformed lines. Each rejected case
is paired with an accepted one just inside the boundary. Hash *content* (pattern,
duplicates, the same hashes in all three files) is validated later, in step 5d.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import pytest

from qm_etdac_calculator.errors import InputError
from qm_etdac_calculator.gate_controler import (
    Controler,
    ListEntry,
    ResolvedEntry,
    default_data_root,
    parse_list_file,
)

NAME = "resA_MOcore_list.log"


def _parse(data: bytes) -> list[ListEntry]:
    return parse_list_file(data, NAME)


def _logged(caplog: pytest.LogCaptureFixture, level: int) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.levelno == level]


@pytest.fixture(autouse=True)
def _capture_package_logs(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger="qm_etdac_calculator")


# --- accepted ------------------------------------------------------------------------


def test_plain_file_is_read_in_order() -> None:
    entries = _parse(b"f10,inputs/a.csv\nf11,inputs/b.csv\n")
    assert entries == [ListEntry(1, "f10", "inputs/a.csv"), ListEntry(2, "f11", "inputs/b.csv")]


def test_final_newline_is_normal_and_silent(caplog: pytest.LogCaptureFixture) -> None:
    assert _parse(b"f10,inputs/a.csv\n") == _parse(b"f10,inputs/a.csv")
    assert _logged(caplog, logging.WARNING) == []


def test_windows_line_endings_are_accepted_and_logged(caplog: pytest.LogCaptureFixture) -> None:
    assert [e.hash for e in _parse(b"f10,a.csv\r\nf11,b.csv\r\n")] == ["f10", "f11"]
    assert _logged(caplog, logging.INFO) == ["'resA_MOcore_list.log' uses Windows line endings (\\r\\n)"]
    assert _logged(caplog, logging.WARNING) == []


def test_classic_mac_line_endings_are_accepted_and_logged(caplog: pytest.LogCaptureFixture) -> None:
    assert [e.hash for e in _parse(b"f10,a.csv\rf11,b.csv\r")] == ["f10", "f11"]
    assert _logged(caplog, logging.INFO) == ["'resA_MOcore_list.log' uses classic Mac line endings (\\r)"]


def test_mixed_windows_and_unix_line_endings_are_accepted_with_a_warning(caplog: pytest.LogCaptureFixture) -> None:
    """\\r\\n mixed with \\n: the \\r before \\n is a removable Windows leftover."""
    assert [e.hash for e in _parse(b"f10,a.csv\r\nf11,b.csv\n")] == ["f10", "f11"]
    assert _logged(caplog, logging.WARNING) == [
        "'resA_MOcore_list.log' has inconsistent line endings (\\r\\n: 1, \\n: 1); "
        "each one is treated as a line break"
    ]


def test_lone_carriage_return_in_a_unix_file_is_rejected() -> None:
    """A lone \\r among \\n line endings is not interpreted: it is an error, never an edit."""
    with pytest.raises(InputError, match="line 1: lone carriage return"):
        _parse(b"f10,inputs/\ra.csv\n")


def test_lone_carriage_return_in_a_windows_file_is_rejected() -> None:
    with pytest.raises(InputError, match="line 2: lone carriage return"):
        _parse(b"f10,a.csv\r\nf11,b\r.csv\r\n")


def test_utf8_bom_is_removed_and_logged(caplog: pytest.LogCaptureFixture) -> None:
    assert _parse(b"\xef\xbb\xbff10,a.csv\n")[0].hash == "f10"
    assert _logged(caplog, logging.INFO) == ["'resA_MOcore_list.log' starts with a UTF-8 BOM; removed"]


@pytest.mark.parametrize("blank", [b"", b"   ", b"\t", b" \t "])
def test_blank_lines_are_ignored_with_a_warning(blank: bytes, caplog: pytest.LogCaptureFixture) -> None:
    entries = _parse(b"f10,a.csv\n" + blank + b"\nf11,b.csv\n")
    assert [(e.line, e.hash) for e in entries] == [(1, "f10"), (3, "f11")]  # line numbers stay true
    assert _logged(caplog, logging.WARNING) == ["'resA_MOcore_list.log' line 2: blank line ignored"]


def test_trailing_blank_lines_are_ignored_with_a_warning(caplog: pytest.LogCaptureFixture) -> None:
    assert len(_parse(b"f10,a.csv\n\n\n")) == 1
    assert _logged(caplog, logging.WARNING) == [
        "'resA_MOcore_list.log' line 2: blank line ignored",
        "'resA_MOcore_list.log' line 3: blank line ignored",
    ]


def test_spaces_inside_a_path_are_accepted_with_a_warning(caplog: pytest.LogCaptureFixture) -> None:
    assert _parse(b"f30,file of molecule 30.csv\n")[0].path == "file of molecule 30.csv"
    assert _logged(caplog, logging.WARNING) == [
        "'resA_MOcore_list.log' line 1: path contains spaces: works in this program, but may break "
        "shell commands or other tools that do not quote paths; rename the file: 'file of molecule 30.csv'"
    ]


# --- rejected (InputError) -----------------------------------------------------------


def test_invalid_utf8_is_rejected() -> None:
    with pytest.raises(InputError, match="not valid UTF-8"):
        _parse(b"f10,caf\xe9.csv\n")  # Latin-1 byte


@pytest.mark.parametrize(
    "line",
    [b"f10", b"f10,a.csv,extra", b",a.csv", b"f10,", b","],
)
def test_lines_that_are_not_exactly_hash_and_path_are_rejected(line: bytes) -> None:
    with pytest.raises(InputError, match="line 1: "):
        _parse(line + b"\n")


@pytest.mark.parametrize("line", [b" f10,a.csv", b"f10 ,a.csv", b"f10, a.csv", b"f10,a.csv "])
def test_leading_or_trailing_spaces_in_a_field_are_rejected(line: bytes) -> None:
    with pytest.raises(InputError, match="leading or trailing spaces"):
        _parse(line + b"\n")


@pytest.mark.parametrize(
    "hostile",
    [
        b"f10,a.csv\x1b[31m",  # ANSI escape code
        b"f10\t,a.csv",  # tab inside a non-blank line
        b"f10,a\x0c.csv",  # form feed
        b"f10,a\x00.csv",  # NUL
        "f10,a\u2028.csv".encode(),  # Unicode line separator
        "f10,a\u200b.csv".encode(),  # zero-width space: not blank, not visible
        "f10,a\u202e.csv".encode(),  # right-to-left override ("Trojan Source", CVE-2021-42574)
        "f10,a\u2066.csv".encode(),  # left-to-right isolate (same family)
    ],
)
def test_control_and_invisible_characters_are_rejected(hostile: bytes) -> None:
    with pytest.raises(InputError, match="line 1: forbidden character"):
        _parse(hostile + b"\n")


def test_file_without_entries_is_rejected() -> None:
    with pytest.raises(InputError, match="no entries"):
        _parse(b"\n  \n")


@pytest.mark.parametrize(
    "data",
    [b"f10\n", b"f10,a.csv\x1b\n", b" f10,a.csv\n", b"f10,\n", b"f10,a\rb.csv\n", b"f10,caf\xe9.csv\n"],
)
def test_format_errors_point_to_the_format_documentation(data: bytes) -> None:
    with pytest.raises(InputError) as excinfo:
        _parse(data)
    assert str(excinfo.value).endswith("(see docs/input-format.md)")


def test_error_messages_stay_on_one_line_and_show_values_safely() -> None:
    with pytest.raises(InputError) as excinfo:
        _parse(b"f10,a.csv,\x1b[31mINFO: forged\n")
    message = str(excinfo.value)
    assert "\n" not in message and "\x1b" not in message
    assert message.startswith("'resA_MOcore_list.log' line 1: ")


# =====================================================================================
# Path policy (step 5c, bullet 2; ADR 0003 and ADR 0004)
# =====================================================================================

@pytest.fixture
def tree(tmp_path: Path) -> dict[str, Path]:
    """
    tmp/
      root/                      <- data root
        logs/  list files, inputs/a.csv
        data/  b.csv
        link_in   -> data/b.csv          (symlink staying inside the root)
        link_out  -> ../outside/c.csv    (symlink escaping the root)
        folder/
      root2/x.csv                <- sibling whose name starts with "root"
      outside/c.csv
    """
    root = tmp_path / "root"
    for folder in (root / "logs" / "inputs", root / "data", root / "folder", tmp_path / "root2", tmp_path / "outside"):
        folder.mkdir(parents=True)
    for file in (root / "logs" / "inputs" / "a.csv", root / "data" / "b.csv", tmp_path / "root2" / "x.csv", tmp_path / "outside" / "c.csv"):
        file.write_text("x\n")
    (root / "link_in").symlink_to(root / "data" / "b.csv")
    (root / "link_out").symlink_to(tmp_path / "outside" / "c.csv")
    return {"tmp": tmp_path, "root": root, "logs": root / "logs"}


def _list(folder: Path, *lines: str, name: str = "list.log") -> Path:
    path = folder / name
    path.write_text("".join(line + "\n" for line in lines), encoding="utf-8")
    return path


def _read(tree: dict[str, Path], *lines: str) -> list[ResolvedEntry]:
    return Controler(tree["root"]).read_list_file(_list(tree["logs"], *lines))


# --- accepted ------------------------------------------------------------------------


def test_default_data_root_is_the_parent_of_the_logs_folder(tree: dict[str, Path]) -> None:
    """ADR 0004, until newFY_1-26 is renamed."""
    assert default_data_root(tree["logs"]) == tree["root"].resolve()


def test_relative_path_inside_the_logs_folder(tree: dict[str, Path]) -> None:
    assert _read(tree, "f10,inputs/a.csv") == [
        ResolvedEntry(1, "f10", (tree["logs"] / "inputs" / "a.csv").resolve())
    ]


def test_parent_folder_inside_the_data_root(tree: dict[str, Path]) -> None:
    """The Bigscale case: ../newFY_1-26/... stays inside the data root."""
    assert _read(tree, "f10,../data/b.csv")[0].path == (tree["root"] / "data" / "b.csv").resolve()


def test_symlink_pointing_inside_is_followed(tree: dict[str, Path]) -> None:
    assert _read(tree, "f10,../link_in")[0].path == (tree["root"] / "data" / "b.csv").resolve()


def test_paths_resolve_against_the_list_file_not_the_working_folder(
    tree: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tree["tmp"])  # running from elsewhere changes nothing
    assert _read(tree, "f10,inputs/a.csv")[0].path == (tree["logs"] / "inputs" / "a.csv").resolve()


def test_order_and_line_numbers_are_kept(tree: dict[str, Path]) -> None:
    entries = _read(tree, "f11,../data/b.csv", "", "f10,inputs/a.csv")
    assert [(e.line, e.hash) for e in entries] == [(1, "f11"), (3, "f10")]


# --- rejected (InputError) -----------------------------------------------------------


def test_absolute_path_is_rejected_even_inside_the_root(tree: dict[str, Path]) -> None:
    inside = (tree["logs"] / "inputs" / "a.csv").resolve()
    with pytest.raises(InputError, match="absolute paths are not allowed") as excinfo:
        _read(tree, f"f10,{inside}")
    assert str(excinfo.value).endswith("(see docs/input-format.md)")


def test_path_escaping_the_data_root_is_rejected(tree: dict[str, Path]) -> None:
    with pytest.raises(InputError, match="outside the data root"):
        _read(tree, "f10,../../outside/c.csv")


def test_sibling_folder_with_the_same_name_prefix_is_rejected(tree: dict[str, Path]) -> None:
    """root2/ starts with "root": a string-prefix check would wrongly accept it."""
    with pytest.raises(InputError, match="outside the data root"):
        _read(tree, "f10,../../root2/x.csv")


def test_symlink_pointing_outside_is_rejected(tree: dict[str, Path]) -> None:
    with pytest.raises(InputError, match="outside the data root"):
        _read(tree, "f10,../link_out")


def test_symlink_loop_is_rejected(tree: dict[str, Path]) -> None:
    (tree["root"] / "loop").symlink_to(tree["root"] / "loop")
    with pytest.raises(InputError, match="cannot resolve"):
        _read(tree, "f10,../loop")


def test_missing_file_is_rejected(tree: dict[str, Path]) -> None:
    with pytest.raises(InputError, match="line 1: file not found"):
        _read(tree, "f10,inputs/missing.csv")


def test_folder_instead_of_file_is_rejected(tree: dict[str, Path]) -> None:
    with pytest.raises(InputError, match="not a regular file"):
        _read(tree, "f10,../folder")


def test_list_file_outside_the_data_root_is_rejected(tree: dict[str, Path]) -> None:
    outside_list = _list(tree["tmp"] / "outside", "f10,c.csv")
    with pytest.raises(InputError, match="list file is outside the data root"):
        Controler(tree["root"]).read_list_file(outside_list)


def test_missing_list_file_is_rejected(tree: dict[str, Path]) -> None:
    with pytest.raises(InputError, match="list file not found"):
        Controler(tree["root"]).read_list_file(tree["logs"] / "missing.log")


def test_missing_data_root_is_rejected(tree: dict[str, Path]) -> None:
    with pytest.raises(InputError, match="data root not found"):
        Controler(tree["tmp"] / "nowhere")


# =====================================================================================
# Loading the CSV files (step 5c, bullet 3)
# =====================================================================================

PHE_TYR = Path(__file__).parent / "data" / "phe_tyr"
PHE_TYR_LISTS = {
    "resA_MOcore_list.log": "num-1",
    "resB_MOvirt_list.log": "num-1",
    "corevirt_fosce_AB_list.log": "virt\\core",
}


@pytest.mark.parametrize(("list_name", "index_col"), PHE_TYR_LISTS.items())
def test_load_dict_data_reproduces_the_notebook_loader(
    list_name: str, index_col: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """All 52 Phe-Tyr samples: same hashes, same order, identical DataFrames."""
    import notebook_reference as nb

    controler = Controler(default_data_root(PHE_TYR))
    loaded = controler.load_dict_data(PHE_TYR / list_name, index_col)

    monkeypatch.chdir(PHE_TYR)  # the notebook loader resolves paths against the working folder
    expected = nb.load_dict_data(list_name, index_col)

    assert list(loaded) == list(expected) == [f"f{i}" for i in range(10, 62)]
    for key in expected:
        pd.testing.assert_frame_equal(loaded[key], expected[key], check_exact=True, obj=key)


def test_load_dict_data_reports_what_it_loaded(caplog: pytest.LogCaptureFixture) -> None:
    Controler(default_data_root(PHE_TYR)).load_dict_data(PHE_TYR / "resA_MOcore_list.log", "num-1")
    assert "loaded 52 entries from 'resA_MOcore_list.log'" in _logged(caplog, logging.INFO)


def test_load_dict_data_applies_the_path_policy(tree: dict[str, Path]) -> None:
    with pytest.raises(InputError, match="outside the data root"):
        Controler(tree["root"]).load_dict_data(_list(tree["logs"], "f10,../../outside/c.csv"), "num-1")


def test_duplicate_hash_is_rejected_instead_of_overwritten(tree: dict[str, Path]) -> None:
    """A dict keyed by hash would silently keep only the last duplicate."""
    list_file = _list(tree["logs"], "f10,inputs/a.csv", "f10,../data/b.csv")
    with pytest.raises(InputError, match="line 2: duplicate hash 'f10' \\(first on line 1\\)"):
        Controler(tree["root"]).load_dict_data(list_file, "num-1")


def test_distinct_hashes_pointing_to_the_same_file_are_accepted(tree: dict[str, Path]) -> None:
    """Boundary: only hashes must be unique; two samples may share a file."""
    (tree["logs"] / "inputs" / "a.csv").write_text("num-1,sym,lvl,7\n1,C,s,60.0\n")
    list_file = _list(tree["logs"], "f10,inputs/a.csv", "f11,inputs/a.csv")
    assert list(Controler(tree["root"]).load_dict_data(list_file, "num-1")) == ["f10", "f11"]
