"""Input validation (step 5d, ADR 0005): hash pattern and the same hashes in all three files.

Each rejected case is paired with an accepted one just inside the boundary. Non-ASCII test
values are written as escape sequences, so this file stays plain ASCII.
"""

from __future__ import annotations

import pytest

from qm_etdac_calculator.errors import InputError
from qm_etdac_calculator.validation import check_hash, check_same_hashes

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
