"""Reading list files: format (step 5c, bullet 1).

A list file has one `hash,path` entry per line. These tests pin how the reader treats
editing leftovers (UTF-8 BOM, line endings, blank lines) and malformed lines. Each rejected case
is paired with an accepted one just inside the boundary. Hash *content* (pattern,
duplicates, the same hashes in all three files) is validated later, in step 5d.
"""

from __future__ import annotations

import logging

import pytest

from qm_etdac_calculator.errors import InputError
from qm_etdac_calculator.gate_controler import ListEntry, parse_list_file

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


def test_mixed_line_endings_are_accepted_with_a_warning(caplog: pytest.LogCaptureFixture) -> None:
    assert [e.hash for e in _parse(b"f10,a.csv\r\nf11,b.csv\nf12,c.csv\r")] == ["f10", "f11", "f12"]
    assert _logged(caplog, logging.WARNING) == [
        "'resA_MOcore_list.log' has inconsistent line endings (\\r\\n: 1, \\n: 1, \\r: 1); "
        "each one is treated as a line break"
    ]


def test_lone_carriage_return_splits_the_line_and_never_edits_a_path() -> None:
    """A lone \\r is a line break: the two halves must each be a valid line."""
    # "f10,inputs/" is line 1 (2 fields, format OK); "a.csv" is line 2 and has 1 field
    with pytest.raises(InputError, match="line 2: expected 2 fields"):
        _parse(b"f10,inputs/\ra.csv\n")


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
        "'resA_MOcore_list.log' line 1: path contains spaces (works, but avoid it): 'file of molecule 30.csv'"
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


def test_error_messages_stay_on_one_line_and_show_values_safely() -> None:
    with pytest.raises(InputError) as excinfo:
        _parse(b"f10,a.csv,\x1b[31mINFO: forged\n")
    message = str(excinfo.value)
    assert "\n" not in message and "\x1b" not in message
    assert message.startswith("'resA_MOcore_list.log' line 1: ")
