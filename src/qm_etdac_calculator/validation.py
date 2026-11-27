"""
Input validation rules (ADR 0005). Each rule raises InputError, naming where the problem is
and showing untrusted values only through untrusted().

Step 5d, commit 1: hashes.
- check_hash: a hash is 1 to 64 ASCII letters or digits, nothing else. An explicit
  character class with fullmatch is used on purpose: str.isalnum() and the regex \\w also
  accept non-ASCII letters and digits (accented letters, Arabic-Indic or full-width digits),
  and re.match with $ would accept a trailing newline.
- check_same_hashes: every sample (hash) must be present in all inputs; samples are paired
  by hash, not by position, so different orders are fine.

Step 5d, commit 2: CSV structure (check_csv_structure), on the raw cells before pandas
interprets anything: no spaces around cells, exact header, unique non-negative integer
labels (MO labels in the header, atom / virtual-MO labels in the first column), and every
row as long as the header.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping

from .errors import FORMAT_HINT, InputError
from .logging_setup import untrusted

HASH_PATTERN = re.compile(r"[A-Za-z0-9]{1,64}")
LABEL_PATTERN = re.compile(r"[0-9]+")  # non-negative integer, ASCII digits only
HEADER_PREFIX = {"population": ["num-1", "sym", "lvl"], "oscillator": ["virt\\core"]}
MAX_REPORTED = 10  # problems listed in one message; the rest are counted


def check_hash(value: str, where: str) -> None:
    """Raise InputError unless `value` is 1 to 64 ASCII letters or digits."""
    if HASH_PATTERN.fullmatch(value) is None:
        raise InputError(
            f"{where}: invalid hash {untrusted(value)}: use letters and digits only "
            f"(A-Z, a-z, 0-9), 1 to 64 characters"
        )


def check_same_hashes(hashes_by_input: Mapping[str, Iterable[str]]) -> None:
    """
    Raise InputError unless every hash appears in every input.

    Args:
        hashes_by_input: {label of the input: its hashes}, e.g.
            {"core populations": [...], "virtual populations": [...], ...}.
    """
    sets = {label: set(hashes) for label, hashes in hashes_by_input.items()}
    every_hash: list[str] = []
    for hashes in hashes_by_input.values():
        every_hash.extend(h for h in hashes if h not in every_hash)  # keep first-seen order

    problems = []
    for hash_ in every_hash:
        missing = [label for label, found in sets.items() if hash_ not in found]
        if missing:
            problems.append(f"hash {untrusted(hash_)} is missing from: {', '.join(missing)}")
    if problems:
        shown = problems[:MAX_REPORTED]
        extra = len(problems) - len(shown)
        message = "samples differ between inputs: " + "; ".join(shown)
        if extra:
            message += f"; and {extra} more"
        raise InputError(message)


def check_csv_structure(rows: list[tuple[int, list[str]]], kind: str, where: str) -> None:
    """
    Check the structure of a CSV file given as raw cells (ADR 0005), before pandas parses it.

    Args:
        rows: (line number in the file, cells split on commas) for every non-blank line.
        kind: "population" (header num-1,sym,lvl,<MO labels>) or "oscillator"
            (header virt\\core,<MO labels>).
        where: how to name the sample and file in messages.
    Raises:
        InputError: the first structural problem found.
    """
    for number, cells in rows:
        for cell in cells:
            if cell != cell.strip(" "):
                raise InputError(
                    f"{where}: CSV line {number}: cell {untrusted(cell)} has leading or trailing spaces; "
                    f"expected values without spaces, e.g. '1,C,s,60.0' (with spaces, '1' and ' 1' would be "
                    f"different labels and errors could hide) {FORMAT_HINT}"
                )
    if not rows:
        raise InputError(f"{where}: CSV file is empty {FORMAT_HINT}")

    prefix = HEADER_PREFIX[kind]
    expected = ",".join(prefix) + ",<MO labels>"
    header_line, header = rows[0]
    if header[: len(prefix)] != prefix:
        raise InputError(
            f"{where}: CSV line {header_line}: header must be '{expected}', found {untrusted(','.join(header))} "
            f"{FORMAT_HINT}"
        )
    mo_labels = header[len(prefix) :]
    if not mo_labels:
        raise InputError(f"{where}: CSV line {header_line}: header has no MO columns {FORMAT_HINT}")
    seen_mo: set[str] = set()
    for label in mo_labels:
        if LABEL_PATTERN.fullmatch(label) is None:
            raise InputError(
                f"{where}: CSV line {header_line}: invalid MO label {untrusted(label)}: expected a "
                f"non-negative integer {FORMAT_HINT}"
            )
        if label in seen_mo:
            raise InputError(f"{where}: CSV line {header_line}: duplicate MO label {untrusted(label)} {FORMAT_HINT}")
        seen_mo.add(label)

    if len(rows) == 1:
        raise InputError(f"{where}: CSV file has a header but no data rows {FORMAT_HINT}")
    first_seen: dict[str, int] = {}
    for number, cells in rows[1:]:
        if len(cells) != len(header):
            raise InputError(
                f"{where}: CSV line {number}: expected {len(header)} fields (as in the header), found {len(cells)} "
                f"{FORMAT_HINT}"
            )
        label = cells[0]
        if LABEL_PATTERN.fullmatch(label) is None:
            raise InputError(
                f"{where}: CSV line {number}: invalid row label {untrusted(label)}: expected a non-negative "
                f"integer {FORMAT_HINT}"
            )
        if label in first_seen:
            raise InputError(
                f"{where}: CSV line {number}: duplicate row label {untrusted(label)} "
                f"(first on CSV line {first_seen[label]}) {FORMAT_HINT}"
            )
        first_seen[label] = number
