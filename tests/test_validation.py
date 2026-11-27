"""Input validation (step 5d, ADR 0005): hashes (commit 1) and CSV structure (commit 2).

Each rejected case is paired with an accepted one just inside the boundary. Non-ASCII test
values are written as escape sequences, so this file stays plain ASCII.
"""

from __future__ import annotations

import pytest

from qm_etdac_calculator.errors import InputError
from qm_etdac_calculator.validation import check_csv_structure, check_hash, check_same_hashes

# --- hash pattern: ^[A-Za-z0-9]{1,64}$, ASCII only ----------------------------------


@pytest.mark.parametrize("value", ["f10", "F10", "10", "f", "a" * 64, "AbC123xyz"])
def test_valid_hashes_are_accepted(value: str) -> None:
    check_hash(value, "list.log line 1")


@pytest.mark.parametrize(
    "value",
    [
        "f 10",  # space inside
        "f10;rm",  # shell metacharacter
        "<b>",  # markup
        "f-10",  # punctuation
        "f_10",  # underscore (\w would accept it)
        "f\u00e910",  # e with acute accent: str.isalnum() would accept it
        "\u0661\u0662",  # Arabic-Indic digits: str.isalnum() would accept them
        "\uff46\uff11\uff10",  # full-width "f10": looks like ASCII, is not
        "a" * 65,  # too long
        "f10\n",  # trailing newline: re.match with $ would accept it
    ],
)
def test_invalid_hashes_are_rejected(value: str) -> None:
    with pytest.raises(InputError, match="list.log line 1: invalid hash"):
        check_hash(value, "list.log line 1")


def test_hash_error_shows_the_value_safely() -> None:
    with pytest.raises(InputError) as excinfo:
        check_hash("f10\x1b[31m", "list.log line 1")
    assert "\x1b" not in str(excinfo.value)
    assert "letters and digits only" in str(excinfo.value)


# --- the same hashes in all three files --------------------------------------------


def test_same_hashes_in_any_order_are_accepted() -> None:
    check_same_hashes({"core": ["f10", "f11"], "virtual": ["f11", "f10"], "osc": ["f10", "f11"]})


def test_hash_missing_from_one_set_is_rejected() -> None:
    with pytest.raises(InputError, match="hash 'f11' is missing from: virtual"):
        check_same_hashes({"core": ["f10", "f11"], "virtual": ["f10"], "osc": ["f10", "f11"]})


def test_hash_missing_from_two_sets_names_both() -> None:
    with pytest.raises(InputError, match="hash 'f11' is missing from: virtual, osc"):
        check_same_hashes({"core": ["f10", "f11"], "virtual": ["f10"], "osc": ["f10"]})


def test_extra_hash_in_one_set_is_rejected() -> None:
    """An extra hash is a hash missing from the other two sets."""
    with pytest.raises(InputError, match="hash 'f99' is missing from: core, virtual"):
        check_same_hashes({"core": ["f10"], "virtual": ["f10"], "osc": ["f10", "f99"]})


def test_long_lists_of_problems_are_truncated() -> None:
    core = [f"f{i}" for i in range(15)]
    with pytest.raises(InputError) as excinfo:
        check_same_hashes({"core": core, "virtual": [], "osc": core})
    message = str(excinfo.value)
    assert message.count("is missing from") == 10
    assert message.endswith("and 5 more")


# --- CSV structure (step 5d, commit 2) ------------------------------------------------

WHERE = "list.log line 1 ('f10', 'x.csv')"


def _rows(text: str) -> list[tuple[int, list[str]]]:
    """Rows as the reader gives them: (line number, cells split on commas)."""
    return [(n, line.split(",")) for n, line in enumerate(text.strip("\n").split("\n"), start=1)]


POPULATION_OK = "num-1,sym,lvl,7,8\n1,C,s,60.0,0.0\n2,C,s,40.0,0.0\n"
OSCILLATOR_OK = "virt\\core,7,8\n92,0.5,0.0\n93,0.2,0.1\n"


def test_valid_population_and_oscillator_files_are_accepted() -> None:
    check_csv_structure(_rows(POPULATION_OK), "population", WHERE)
    check_csv_structure(_rows(OSCILLATOR_OK), "oscillator", WHERE)


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("x", "header must be 'num-1,sym,lvl,<MO labels>'"),
        ("atom,sym,lvl,7\n1,C,s,60.0", "header must be 'num-1,sym,lvl,<MO labels>'"),
        ("num-1,lvl,sym,7\n1,s,C,60.0", "header must be 'num-1,sym,lvl,<MO labels>'"),
        ("num-1;sym;lvl;7\n1;C;s;60.0", "header must be 'num-1,sym,lvl,<MO labels>'"),
        ('"num-1",sym,lvl,7\n1,C,s,60.0', "header must be 'num-1,sym,lvl,<MO labels>'"),
        ("num-1,sym,lvl\n1,C,s", "no MO columns"),
        ("num-1,sym,lvl,7", "no data rows"),
    ],
)
def test_population_structure_errors(text: str, message: str) -> None:
    with pytest.raises(InputError, match=message):
        check_csv_structure(_rows(text), "population", WHERE)


@pytest.mark.parametrize(
    "text",
    ["virt/core,7\n92,0.5", "num-1,7\n92,0.5", "virt\\core\n92"],
)
def test_oscillator_structure_errors(text: str) -> None:
    with pytest.raises(InputError, match=r"header must be 'virt\\core,<MO labels>'|no MO columns"):
        check_csv_structure(_rows(text), "oscillator", WHERE)


@pytest.mark.parametrize(
    "label",
    ["7a", "-7", "7.0", "", "+7", "0x7", " 7", "\u0667", "\uff17"],  # last two: Arabic-Indic and full-width 7 (\d would accept them)
)
def test_mo_labels_must_be_non_negative_integers(label: str) -> None:
    with pytest.raises(InputError, match="CSV line 1: "):
        check_csv_structure(_rows(f"num-1,sym,lvl,{label}\n1,C,s,60.0"), "population", WHERE)


def test_duplicate_mo_label_is_rejected_before_pandas_could_rename_it() -> None:
    """pandas would silently rename the second '7' to '7.1'."""
    with pytest.raises(InputError, match="CSV line 1: duplicate MO label '7'"):
        check_csv_structure(_rows("num-1,sym,lvl,7,7\n1,C,s,60.0,1.0"), "population", WHERE)


@pytest.mark.parametrize("label", ["1a", "", "-1", "1.0"])
def test_row_labels_must_be_non_negative_integers(label: str) -> None:
    with pytest.raises(InputError, match="CSV line 2: invalid row label"):
        check_csv_structure(_rows(f"num-1,sym,lvl,7\n{label},C,s,60.0"), "population", WHERE)


def test_duplicate_row_label_is_rejected() -> None:
    with pytest.raises(InputError, match="CSV line 3: duplicate row label '1' \\(first on CSV line 2\\)"):
        check_csv_structure(_rows("num-1,sym,lvl,7\n1,C,s,60.0\n1,C,s,40.0"), "population", WHERE)


@pytest.mark.parametrize(("row", "found"), [("1,C,s,60.0,9.9", 5), ("1,C,s", 3)])
def test_rows_must_have_as_many_fields_as_the_header(row: str, found: int) -> None:
    with pytest.raises(InputError, match=f"CSV line 2: expected 4 fields .*found {found}"):
        check_csv_structure(_rows(f"num-1,sym,lvl,7\n{row}"), "population", WHERE)


@pytest.mark.parametrize("text", ["num-1, sym,lvl,7\n1,C,s,60.0", "num-1,sym,lvl,7\n1,C ,s,60.0", "num-1,sym,lvl,7\n1,C,s, 60.0"])
def test_spaces_around_cells_are_rejected_with_an_explanation(text: str) -> None:
    with pytest.raises(InputError) as excinfo:
        check_csv_structure(_rows(text), "population", WHERE)
    message = str(excinfo.value)
    assert "leading or trailing spaces" in message
    assert "expected values without spaces" in message
    assert message.endswith("(see docs/input-format.md)")


def test_structure_errors_name_the_sample_and_file() -> None:
    with pytest.raises(InputError) as excinfo:
        check_csv_structure(_rows("x"), "population", WHERE)
    assert str(excinfo.value).startswith(WHERE + ": ")
