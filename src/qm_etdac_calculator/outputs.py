"""
Output folder and protection of existing results (ADR 0003).

Step 5e, commit 1. A run writes a pair of files into the output folder: `<stem>.h5` (the
results) and `<stem>.log` (the run log, opened by the CLI in step 6). prepare_outputs():

- creates the output folder with os.makedirs (never a shell); the folder must be a real
  folder, not a file and not a symbolic link (a planted link would send the results
  somewhere else: CWE-59);
- accepts only a simple output name (stem): ASCII letters, digits, '_' and '-', starting
  with a letter or digit, at most 64 characters, so no path or extension can be smuggled in;
- if `<stem>.h5` or `<stem>.log` already exists, renames it to `<stem>_oldversionN<ext>`,
  with N = the highest existing number + 1 (gaps stay, so a higher N is always newer) and
  the same N for both files of the pair; existing `_oldversion` files are never touched;
- logs one WARNING per rotation: the program cannot tell yet whether the old result belongs
  to the same system (see docs/project-state.md, Future), so it always says so;
- renames without overwriting: os.link() fails if the new name already exists (os.rename()
  would silently replace it on Linux), then the old name is removed. A second run racing for
  the same name gets an OutputError instead of destroying a result.

The returned paths do not exist yet; the results are written in step 5e, commit 2.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import NamedTuple

from .errors import OutputError
from .logging_setup import untrusted

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = "etdac_outputs"
DEFAULT_STEM = "data_etdac_matrix"
EXTENSIONS = (".h5", ".log")
STEM_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")


class OutputPaths(NamedTuple):
    h5: Path
    log: Path


def _next_number(folder: Path, stem: str) -> int:
    """Highest N of `<stem>_oldversionN<ext>` over all EXTENSIONS, plus one."""
    pattern = re.compile(re.escape(stem) + r"_oldversion([1-9][0-9]*)(?:" + "|".join(map(re.escape, EXTENSIONS)) + ")")
    numbers = [int(m.group(1)) for p in folder.iterdir() if (m := pattern.fullmatch(p.name))]
    return max(numbers, default=0) + 1


def _move_no_overwrite(source: Path, target: Path) -> None:
    """Rename `source` to `target`, failing instead of replacing an existing `target`."""
    try:
        os.link(source, target)  # FileExistsError if target exists: never overwrites
    except FileExistsError:
        raise OutputError(
            f"cannot keep {untrusted(source.name)}: {untrusted(target.name)} already exists "
            f"(another run may be writing into {untrusted(str(source.parent))} at the same time)"
        ) from None
    source.unlink()


def prepare_outputs(output_dir: Path | str = DEFAULT_OUTPUT_DIR, stem: str = DEFAULT_STEM) -> OutputPaths:
    """
    Create the output folder and move any existing result of the same name out of the way.

    Args:
        output_dir: the output folder; created if missing.
        stem: the file name without extension, shared by the .h5 and the .log file.
    Returns:
        The paths of the .h5 and .log files to write; neither exists.
    Raises:
        OutputError: invalid stem, output path is a file or a symbolic link, or a rotated
            name appeared meanwhile.
    """
    if STEM_PATTERN.fullmatch(stem) is None:
        raise OutputError(
            f"invalid output name {untrusted(stem)}: use letters, digits, '_' and '-' only, starting with a "
            f"letter or digit, at most 64 characters, without extension"
        )
    given = Path(output_dir)
    if given.is_symlink():
        raise OutputError(f"output folder {untrusted(str(given))} is a symbolic link; use a real folder")
    if given.exists() and not given.is_dir():
        raise OutputError(f"output folder {untrusted(str(given))} is not a folder")
    os.makedirs(given, exist_ok=True)
    folder = given.resolve(strict=True)

    existing = [folder / f"{stem}{ext}" for ext in EXTENSIONS if (folder / f"{stem}{ext}").exists()]
    if existing:
        number = _next_number(folder, stem)
        kept = [path.with_name(f"{stem}_oldversion{number}{path.suffix}") for path in existing]
        for source, target in zip(existing, kept, strict=True):
            _move_no_overwrite(source, target)
        logger.warning(
            "%s already %s in the output folder %s: kept as %s (never overwritten); it may come from another job "
            "or system: check that this is the right output folder",
            ", ".join(untrusted(p.name) for p in existing),
            "exists" if len(existing) == 1 else "exist",
            untrusted(str(folder)),
            ", ".join(untrusted(p.name) for p in kept),
        )
    return OutputPaths(h5=folder / f"{stem}.h5", log=folder / f"{stem}.log")
