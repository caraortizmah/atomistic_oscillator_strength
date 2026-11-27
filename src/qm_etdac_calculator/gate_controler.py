"""
Input and output of the ETDAC calculation (the program's "gate").

Step 5c, bullet 1: reading the format of a list file. A list file has one entry per line:

    hash,path

e.g. `f10,inputs/resA_MOcore_AB_3.5A_1-26.csv`. The reader is strict about structure and
tolerant only about harmless editing leftovers, which it reports:

- UTF-8 only; a UTF-8 BOM at the start is removed (INFO).
- Line endings \\n, \\r\\n or \\r are all line breaks; \\r\\n or \\r alone is reported at INFO,
  a mix of them at WARNING. A lone \\r therefore splits a line; it never edits a path.
- Blank or whitespace-only lines are ignored (WARNING with file and line).
- Any other control or invisible character is an error, including tab, ANSI escape,
  NUL, Unicode line separators, zero-width and bidirectional-override characters
  (the latter are the "Trojan Source" trick, CVE-2021-42574).
- Exactly two non-empty fields; leading or trailing spaces in a field are an error;
  spaces inside a path work in Python (no shell is involved) but give a WARNING.

Hash content (pattern, duplicates, the same hashes in all three files) is validated in
step 5d; the path policy (ADR 0003/0004) is bullet 2 of step 5c.
"""

from __future__ import annotations

import logging
import re
from typing import NamedTuple

from .errors import InputError
from .logging_setup import untrusted

logger = logging.getLogger(__name__)

_BOM = b"\xef\xbb\xbf"
_LINE_BREAK = re.compile(r"\r\n|\r|\n")
_BLANK = re.compile(r"[ \t]*")
# C0 controls (tab included), DEL, C1 controls, line/paragraph separators,
# zero-width characters and BOM, bidirectional overrides and isolates
_FORBIDDEN = re.compile(
    "[\x00-\x1f\x7f-\x9f\u2028\u2029\u200b-\u200f\u2060\ufeff\u202a-\u202e\u2066-\u2069]"
)


class ListEntry(NamedTuple):
    """One entry of a list file: its line number (1-based), hash and path as written."""

    line: int
    hash: str
    path: str


def _report_line_endings(text: str, where: str) -> None:
    crlf = text.count("\r\n")
    counts = {"\\r\\n": crlf, "\\n": text.count("\n") - crlf, "\\r": text.count("\r") - crlf}
    used = {kind: n for kind, n in counts.items() if n}
    if len(used) > 1:
        detail = ", ".join(f"{kind}: {n}" for kind, n in used.items())
        logger.warning("%s has inconsistent line endings (%s); each one is treated as a line break", where, detail)
    elif "\\r\\n" in used:
        logger.info("%s uses Windows line endings (\\r\\n)", where)
    elif "\\r" in used:
        logger.info("%s uses classic Mac line endings (\\r)", where)


def parse_list_file(data: bytes, name: str) -> list[ListEntry]:
    """
    Parse the raw bytes of a list file into entries, in file order.

    Args:
        data: the file content as bytes.
        name: the file name, used in messages.
    Returns:
        One ListEntry per non-blank line.
    Raises:
        InputError: the file is not valid UTF-8, has a malformed line, or has no entries.
    """
    where = untrusted(name)
    if data.startswith(_BOM):
        data = data[len(_BOM) :]
        logger.info("%s starts with a UTF-8 BOM; removed", where)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise InputError(f"{where} is not valid UTF-8 (byte {error.start})") from None

    _report_line_endings(text, where)
    lines = _LINE_BREAK.split(text)
    if lines and lines[-1] == "":
        lines.pop()  # the final line break is normal, not a blank line

    entries: list[ListEntry] = []
    for number, line in enumerate(lines, start=1):
        prefix = f"{where} line {number}"
        if _BLANK.fullmatch(line):
            logger.warning("%s: blank line ignored", prefix)
            continue
        forbidden = _FORBIDDEN.search(line)
        if forbidden:
            raise InputError(
                f"{prefix}: forbidden character {untrusted(forbidden.group())} at position {forbidden.start() + 1}"
            )
        fields = line.split(",")
        if len(fields) != 2:
            raise InputError(f"{prefix}: expected 2 fields 'hash,path', found {len(fields)}: {untrusted(line)}")
        hash_, path = fields
        for label, value in (("hash", hash_), ("path", path)):
            if value == "":
                raise InputError(f"{prefix}: empty {label}")
            if value != value.strip(" "):
                raise InputError(f"{prefix}: {label} has leading or trailing spaces: {untrusted(value)}")
        if " " in path:
            logger.warning("%s: path contains spaces (works, but avoid it): %s", prefix, untrusted(path))
        entries.append(ListEntry(number, hash_, path))

    if not entries:
        raise InputError(f"{where} has no entries")
    return entries
