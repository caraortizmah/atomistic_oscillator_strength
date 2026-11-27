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

Step 5c, bullet 2: the path policy (ADR 0003, ADR 0004). A Controler may read only inside
its data root:

- the list file itself must resolve inside the data root;
- absolute paths in a list file are rejected, even if they point inside the root;
- relative paths resolve against the list file's own folder, never the working folder;
- resolving follows symlinks, so a link that points outside the root is rejected;
- "inside" compares whole path components (Path.is_relative_to), never string prefixes
  (a sibling "root2" must not pass as being inside "root");
- the target must be an existing regular file.

Known limit: a file could be swapped between this check and the read (TOCTOU). For a
local single-user tool this is accepted; the reader opens the resolved path, not the
original string.

Hash content (pattern, duplicates, the same hashes in all three files) is validated in
step 5d.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
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


class ResolvedEntry(NamedTuple):
    """One list-file entry whose path passed the path policy: an absolute, resolved Path."""

    line: int
    hash: str
    path: Path


def default_data_root(logs_path: Path | str) -> Path:
    """
    The default data root: the parent of the logs folder (ADR 0004).

    Temporary rule until newFY_1-26 is renamed; then a new ADR returns the default to the
    logs folder itself and exposes --data-root. Kept in one function so the change is one line.
    """
    return Path(logs_path).resolve(strict=True).parent


class Controler:
    """
    Reads input files, only from inside its data root (ADR 0003, ADR 0004).

    Attributes:
        data_root: absolute, resolved folder; nothing outside it is ever read.
    """

    def __init__(self, data_root: Path | str) -> None:
        try:
            root = Path(data_root).resolve(strict=True)
        except (OSError, RuntimeError):
            raise InputError(f"data root not found: {untrusted(str(data_root))}") from None
        if not root.is_dir():
            raise InputError(f"data root is not a folder: {untrusted(str(root))}")
        self.data_root = root

    def _is_inside(self, path: Path) -> bool:
        return path.is_relative_to(self.data_root)  # whole components, not string prefixes

    def read_list_file(self, list_file: Path | str) -> list[ResolvedEntry]:
        """
        Read a list file and apply the path policy to every entry.

        Returns:
            The entries in file order, each with its resolved, checked path.
        Raises:
            InputError: list file missing or outside the data root, malformed line
                (see parse_list_file), or an entry that breaks the path policy.
        """
        try:
            list_path = Path(list_file).resolve(strict=True)
        except (OSError, RuntimeError):
            raise InputError(f"list file not found: {untrusted(str(list_file))}") from None
        if not self._is_inside(list_path):
            raise InputError(
                f"list file is outside the data root {untrusted(str(self.data_root))}: {untrusted(str(list_path))}"
            )
        if not list_path.is_file():
            raise InputError(f"list file is not a regular file: {untrusted(str(list_path))}")

        base = list_path.parent
        resolved_entries: list[ResolvedEntry] = []
        for entry in parse_list_file(list_path.read_bytes(), list_path.name):
            prefix = f"{untrusted(list_path.name)} line {entry.line}"
            written = Path(entry.path)
            if written.is_absolute():
                raise InputError(f"{prefix}: absolute paths are not allowed: {untrusted(entry.path)}")
            try:
                resolved = (base / written).resolve(strict=True)  # follows symlinks
            except FileNotFoundError:
                raise InputError(f"{prefix}: file not found: {untrusted(entry.path)}") from None
            except (OSError, RuntimeError):
                raise InputError(f"{prefix}: cannot resolve path (symlink loop?): {untrusted(entry.path)}") from None
            if not self._is_inside(resolved):
                raise InputError(
                    f"{prefix}: path is outside the data root {untrusted(str(self.data_root))}: {untrusted(entry.path)}"
                )
            if not resolved.is_file():
                raise InputError(f"{prefix}: not a regular file: {untrusted(entry.path)}")
            resolved_entries.append(ResolvedEntry(entry.line, entry.hash, resolved))
        logger.debug("%s: %d entries passed the path policy", untrusted(list_path.name), len(resolved_entries))
        return resolved_entries
