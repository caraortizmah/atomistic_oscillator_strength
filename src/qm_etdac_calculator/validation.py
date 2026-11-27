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

Temporary hash policy (1.2.0): the hash rules above, uniqueness within one list file
(gate_controler.Controler.load_dict_data) and the recommendation of at most 9 characters
(docs/input-format.md) assume that one run reads one set of three list files. They stay in
force until multi-file runs are designed: a large system can be split into many list files
(e.g. 1 000 000 samples in 100 files), and then a hash must be unique across all the list
files of that system, not only within one, and hashes will be longer. That change needs a
revision of ADR 0005 (see docs/project-state.md, Future).

Step 5d, commit 2: CSV structure (check_csv_structure), on the raw cells before pandas
interprets anything: no spaces around cells, exact header, unique non-negative integer
labels (MO labels in the header, atom / virtual-MO labels in the first column), and every
row as long as the header.

Step 5d, commit 3a: CSV values (check_csv_values), also on the raw cells. Numbers must match
an explicit pattern before conversion, because float() is far too permissive: it accepts
"nan", "inf", "1_000", spaces, and non-ASCII digits (Arabic-Indic, full-width), and "1e999"
becomes infinity. Accepted: 0, 0.0, 99.6, 8.73323e-06, 1E5; ".5" and "5." are read as 0.5
and 5.0 with one WARNING per file. Populations and oscillator strengths must be >= 0
(-0.0 is zero and accepted). The text columns sym / lvl hold 1 to 8 ASCII letters.

Step 5d, commit 3b: population sums (populations only). A population is a percentage of one
MO on one atom, so a value above 100 % and an MO column adding up to more than 100 % point to
a problem in the parser output. Values are rounded to one decimal, so with up to 47 atoms a
column can reach 100 + 47 x 0.05 = 102.35 % by rounding alone: sums up to 102.5 % are "at the
edge", above it "beyond the rounding tolerance". These are warnings, not errors (ADR 0005).
Columns are added with math.fsum (exact rounding, no error growing with the number of atoms),
and FLOAT_TOLERANCE absorbs the remaining binary representation error: 0.4 + 32.2 + 67.4 is
100.00000000000001 as floats. Sums below 100 % are normal (small contributions are not
written by the parser; the Phe-Tyr data has 96.1 to 99.8 %) and give no warning.
"""

from __future__ import annotations

import logging
import math
import re
from collections.abc import Iterable, Mapping

from .errors import FORMAT_HINT, InputError
from .logging_setup import untrusted

logger = logging.getLogger(__name__)

HASH_PATTERN = re.compile(r"[A-Za-z0-9]{1,64}")
LABEL_PATTERN = re.compile(r"[0-9]+")  # non-negative integer, ASCII digits only
HEADER_PREFIX = {"population": ["num-1", "sym", "lvl"], "oscillator": ["virt\\core"]}
NUMBER_PATTERN = re.compile(r"-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")
ABBREVIATED = re.compile(r"^-?\.|\.(?:[eE]|$)")  # ".5" (no leading zero) or "5." (no trailing zero)
TEXT_PATTERN = re.compile(r"[A-Za-z]{1,8}")
QUANTITY = {"population": "population", "oscillator": "oscillator strength"}
MAX_REPORTED = 10  # problems listed in one message; the rest are counted
POPULATION_TOTAL = 100.0  # percent: one MO over all atoms
ROUNDING_EDGE = 102.5  # percent: 47 atoms x 0.05 rounding = 102.35, plus margin
FLOAT_TOLERANCE = 1e-9  # absorbs binary representation error, far below the 0.1 resolution


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


def check_csv_values(rows: list[tuple[int, list[str]]], kind: str, where: str) -> None:
    """
    Check the values of a CSV file whose structure already passed check_csv_structure (ADR 0005).

    Args:
        rows: (line number in the file, cells) for every non-blank line; rows[0] is the header.
        kind: "population" or "oscillator".
        where: how to name the sample and file in messages.
    Raises:
        InputError: the first value that is not a plain finite number, is negative, or a
            sym / lvl cell that is not 1 to 8 ASCII letters.
    """
    header = rows[0][1]
    first_number = len(HEADER_PREFIX[kind])
    abbreviated: list[tuple[int, str, str]] = []
    columns: dict[str, list[float]] = {label: [] for label in header[first_number:]}
    above_total: list[tuple[int, str, str]] = []
    for number, cells in rows[1:]:
        if kind == "population":
            for column, cell in (("sym", cells[1]), ("lvl", cells[2])):
                if TEXT_PATTERN.fullmatch(cell) is None:
                    raise InputError(
                        f"{where}: CSV line {number}, column {column}: invalid text {untrusted(cell)}: "
                        f"expected 1 to 8 letters (A-Z, a-z), e.g. C, atom, s, lvlMO {FORMAT_HINT}"
                    )
        for label, cell in zip(header[first_number:], cells[first_number:], strict=True):
            position = f"CSV line {number}, column {label}"
            if NUMBER_PATTERN.fullmatch(cell) is None:
                raise InputError(
                    f"{where}: {position}: {untrusted(cell)} is not a number: expected digits such as 0.0, "
                    f"99.6 or 8.73323e-06 (no nan, inf, text, formulas or spaces) {FORMAT_HINT}"
                )
            value = float(cell)  # safe: the pattern admits only plain decimal numbers
            if not math.isfinite(value):
                raise InputError(f"{where}: {position}: {untrusted(cell)} is not a finite number {FORMAT_HINT}")
            if value < 0:
                raise InputError(f"{where}: {position}: negative {QUANTITY[kind]} {untrusted(cell)} {FORMAT_HINT}")
            if ABBREVIATED.search(cell):
                abbreviated.append((number, label, cell))
            columns[label].append(value)
            if kind == "population" and value > POPULATION_TOTAL + FLOAT_TOLERANCE:
                above_total.append((number, label, cell))
    if abbreviated:
        number, label, cell = abbreviated[0]
        logger.warning(
            "%s: %d value(s) written without a leading or trailing zero were read as full numbers "
            "(first: CSV line %d, column %s: %s read as %s); check the file and write 0.5 and 5.0 "
            "instead of .5 and 5. to avoid the assumption",
            where,
            len(abbreviated),
            number,
            label,
            untrusted(cell),
            float(cell),
        )
    if kind == "population":
        _warn_about_population_sums(columns, above_total, where)


def _warn_about_population_sums(
    columns: dict[str, list[float]], above_total: list[tuple[int, str, str]], where: str
) -> None:
    """Log one WARNING for the file if a population or an MO column sum exceeds 100 %."""
    at_edge: list[tuple[str, float]] = []
    beyond: list[tuple[str, float]] = []
    for label, values in columns.items():
        total = math.fsum(values)
        if total > ROUNDING_EDGE + FLOAT_TOLERANCE:
            beyond.append((label, total))
        elif total > POPULATION_TOTAL + FLOAT_TOLERANCE:
            at_edge.append((label, total))

    parts = []
    if above_total:
        number, label, cell = above_total[0]
        parts.append(
            f"{len(above_total)} value(s) above 100 % (first: CSV line {number}, column {label}: {untrusted(cell)})"
        )
    if at_edge:
        label, total = at_edge[0]
        parts.append(
            f"{len(at_edge)} MO column(s) add up to more than 100 % but within the rounding tolerance of "
            f"{ROUNDING_EDGE} % (at the edge; first: column {label}, sum {total:.2f})"
        )
    if beyond:
        label, total = beyond[0]
        parts.append(
            f"{len(beyond)} MO column(s) add up to more than {ROUNDING_EDGE} %, beyond the rounding tolerance "
            f"(first: column {label}, sum {total:.2f})"
        )
    if parts:
        logger.warning(
            "%s: populations above 100 %%: %s; check the population output of this sample: each MO column "
            "should add up to at most 100 %% (up to %s %% can come from rounding to one decimal)",
            where,
            "; ".join(parts),
            ROUNDING_EDGE,
        )
