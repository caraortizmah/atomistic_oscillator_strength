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
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping

from .errors import InputError
from .logging_setup import untrusted

HASH_PATTERN = re.compile(r"[A-Za-z0-9]{1,64}")
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
