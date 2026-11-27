"""Input validation (step 5d, ADR 0005): hashes (commit 1), CSV structure (commit 2), CSV values (commit 3).

Each rejected case is paired with an accepted one just inside the boundary. Non-ASCII test
values are written as escape sequences, so this file stays plain ASCII.
"""

from __future__ import annotations

import pytest

from qm_etdac_calculator.errors import InputError
import logging

from qm_etdac_calculator.validation import check_csv_structure, check_csv_values, check_hash, check_same_hashes

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


# --- CSV values (step 5d, commit 3a) --------------------------------------------------


def _population(value: str, sym: str = "C", lvl: str = "s") -> list[tuple[int, list[str]]]:
    return _rows(f"num-1,sym,lvl,7\n1,{sym},{lvl},{value}")


def _oscillator(value: str) -> list[tuple[int, list[str]]]:
    return _rows(f"virt\\core,7\n92,{value}")


@pytest.mark.parametrize("value", ["0", "0.0", "99.6", "1e-6", "8.73323e-06", "1E5", "2.5e+3", "-0.0", "-0"])
def test_numbers_in_the_parser_format_are_accepted(value: str) -> None:
    check_csv_values(_population(value), "population", WHERE)
    check_csv_values(_oscillator(value), "oscillator", WHERE)


@pytest.mark.parametrize(
    "value",
    [
        "nan", "NaN", "inf", "-inf", "Infinity", "", "abc",  # not numbers
        "=HYPERLINK(1)", "+1", "@SUM(A1)",  # formula injection
        "1_000", "0x1F", "1e", "e5", "1.2.3", "--1",  # float() accepts some of these
        "\u0661", "\uff11",  # Arabic-Indic and full-width digits: float() accepts them
    ],
)
def test_values_that_are_not_plain_numbers_are_rejected(value: str) -> None:
    with pytest.raises(InputError, match="CSV line 2, column 7: .* is not a number"):
        check_csv_values(_population(value), "population", WHERE)


def test_overflow_to_infinity_is_rejected() -> None:
    with pytest.raises(InputError, match="CSV line 2, column 7: .* is not a finite number"):
        check_csv_values(_population("1e999"), "population", WHERE)


def test_negative_population_is_rejected() -> None:
    with pytest.raises(InputError, match="CSV line 2, column 7: negative population '-0.1'"):
        check_csv_values(_population("-0.1"), "population", WHERE)


def test_negative_oscillator_strength_is_rejected() -> None:
    """The message uses the users' term (docs/input-format.md); in the code it is the oscillator strength."""
    with pytest.raises(InputError, match="CSV line 2, column 7: negative core-electron transition intensity '-1e-9'"):
        check_csv_values(_oscillator("-1e-9"), "oscillator", WHERE)


@pytest.mark.parametrize(("sym", "lvl"), [("C", "s"), ("atom", "lvlMO"), ("abcdefgh", "s")])
def test_letter_only_text_columns_are_accepted(sym: str, lvl: str) -> None:
    check_csv_values(_population("1.0", sym, lvl), "population", WHERE)


@pytest.mark.parametrize(
    ("sym", "lvl", "column"),
    [("<script>", "s", "sym"), ("C;", "s", "sym"), ("C1", "s", "sym"), ("abcdefghi", "s", "sym"), ("C", "", "lvl")],
)
def test_text_columns_must_be_letters_only(sym: str, lvl: str, column: str) -> None:
    with pytest.raises(InputError, match=f"CSV line 2, column {column}: invalid text"):
        check_csv_values(_population("1.0", sym, lvl), "population", WHERE)


def test_abbreviated_decimals_are_accepted_with_one_warning_per_file(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING, logger="qm_etdac_calculator")
    check_csv_values(_rows("num-1,sym,lvl,7,8\n1,C,s,.5,5.\n2,C,s,0.5,1.0"), "population", WHERE)
    warnings = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "2 value(s) written without a leading or trailing zero" in warnings[0]
    assert "first: CSV line 2, column 7: '.5' read as 0.5" in warnings[0]
    assert "write 0.5 and 5.0" in warnings[0]


def test_full_numbers_give_no_warning(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING, logger="qm_etdac_calculator")
    check_csv_values(_rows("num-1,sym,lvl,7\n1,C,s,0.5\n2,C,s,5.0"), "population", WHERE)
    assert [r for r in caplog.records if r.levelno == logging.WARNING] == []


def test_value_errors_show_the_value_safely() -> None:
    with pytest.raises(InputError) as excinfo:
        check_csv_values(_population("1\x1b[31m"), "population", WHERE)
    assert "\x1b" not in str(excinfo.value)
    assert str(excinfo.value).startswith(WHERE + ": ")


# --- population sums (step 5d, commit 3b) ---------------------------------------------


def _column(*values: str) -> list[tuple[int, list[str]]]:
    """One MO column (label 7) with one atom per value."""
    lines = [f"{atom},C,s,{value}" for atom, value in enumerate(values, start=1)]
    return _rows("num-1,sym,lvl,7\n" + "\n".join(lines))


def _warnings(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]


@pytest.mark.parametrize(
    "values",
    [
        ("60.0", "40.0"),  # exactly 100
        ("0.4", "32.2", "67.4"),  # 100 in decimal, 100.00000000000001 as floats: the tolerance absorbs it
        ("50.0", "46.1"),  # below 100: normal in the Phe-Tyr data (96.1 to 99.8)
        ("100.0", "0.0"),  # one atom holds the whole MO
    ],
)
def test_population_sums_up_to_100_give_no_warning(values: tuple[str, ...], caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING, logger="qm_etdac_calculator")
    check_csv_values(_column(*values), "population", WHERE)
    assert _warnings(caplog) == []


@pytest.mark.parametrize(
    "values",
    [
        ("60.0", "40.1"),  # 100.1: just above
        ("60.0", "41.0"),  # 101.0
        ("60.0", "42.5"),  # 102.5: the edge itself
        ("0.4", "32.2", "69.9"),  # 102.5 in decimal, 102.50000000000001 as floats: still at the edge
    ],
)
def test_population_sum_within_rounding_tolerance_warns_at_the_edge(
    values: tuple[str, ...], caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.WARNING, logger="qm_etdac_calculator")
    check_csv_values(_column(*values), "population", WHERE)
    warnings = _warnings(caplog)
    assert len(warnings) == 1
    assert warnings[0].startswith(WHERE + ": ")
    assert "1 MO column(s) add up to more than 100 % but within the rounding tolerance of 102.5 % (at the edge" in warnings[0]
    assert "beyond" not in warnings[0]


def test_population_sum_beyond_rounding_tolerance_warns(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING, logger="qm_etdac_calculator")
    check_csv_values(_column("60.0", "42.6"), "population", WHERE)
    warnings = _warnings(caplog)
    assert len(warnings) == 1
    assert "1 MO column(s) add up to more than 102.5 %, beyond the rounding tolerance (first: column 7, sum 102.60)" in warnings[0]
    assert "at the edge" not in warnings[0]


def test_single_population_above_100_warns(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING, logger="qm_etdac_calculator")
    check_csv_values(_column("100.1", "0.0"), "population", WHERE)
    warnings = _warnings(caplog)
    assert len(warnings) == 1
    assert "1 value(s) above 100 % (first: CSV line 2, column 7: '100.1')" in warnings[0]


def test_population_problems_in_one_file_give_one_warning_with_counts(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING, logger="qm_etdac_calculator")
    text = "num-1,sym,lvl,7,8,9,10\n1,C,s,60.0,60.0,101.0,50.0\n2,C,s,41.0,42.0,0.0,50.0\n3,C,s,0.0,1.0,0.0,0.0"
    check_csv_values(_rows(text), "population", WHERE)
    warnings = _warnings(caplog)
    assert len(warnings) == 1
    message = warnings[0]
    assert "1 value(s) above 100 % (first: CSV line 2, column 9: '101.0')" in message
    assert "2 MO column(s) add up to more than 100 % but within" in message  # columns 7 (101.0) and 9 (101.0)
    assert "(at the edge; first: column 7, sum 101.00)" in message
    assert "1 MO column(s) add up to more than 102.5 %" in message  # column 8 (103.0)
    assert "first: column 8, sum 103.00" in message
    assert "check the population output of this sample" in message


def test_oscillator_strengths_have_no_100_limit(caplog: pytest.LogCaptureFixture) -> None:
    """Oscillator strengths are not percentages; only populations add up to 100 %."""
    caplog.set_level(logging.WARNING, logger="qm_etdac_calculator")
    check_csv_values(_rows("virt\\core,7\n92,150.0\n93,80.0"), "oscillator", WHERE)
    assert _warnings(caplog) == []
