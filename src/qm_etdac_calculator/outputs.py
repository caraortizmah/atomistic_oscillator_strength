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

Step 5e, commit 2: write_etdac_h5() writes the results with the notebook's layout (one group
`sample_<hash>` per sample, dataset `ETDAC_matrix` from DataFrame.to_records(index=True),
gzip compression, attributes `hash`, `column_name`, `index_name`), so existing readers and
notebooks keep working. Unlike the notebook (h5py mode "w", which replaces an existing file),
it never overwrites and never leaves a half-written result:

1. the file is written under a hidden temporary name in the same folder
   (`.<name>.<random>.tmp`, created with mode "x"), then flushed to disk (fsync);
2. it is published with os.link(), which fails if the final name exists (a result that
   appeared meanwhile, e.g. from another run, survives and this run gets an OutputError);
3. the temporary name is removed in every case, also when writing fails.
The temporary file must be in the same folder because a hard link cannot cross filesystems.

Step 5e, commit 3: provenance (ADR 0006). The file gets four attributes: `program`,
`program_version`, `created_utc` (ISO 8601, UTC, to the second) and `input_files`, a JSON
list of {"path", "sha256"} from Controler.inputs_read. The JSON is built with json.dumps
(ASCII only: other characters are escaped), never by string concatenation, so a file name
with quotes or brackets cannot break or forge the record (ADR 0005, context-aware output).
"""

from __future__ import annotations

import json
import logging
import os
import re
import secrets
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

import h5py
import pandas as pd

from . import __version__
from .errors import OutputError
from .gate_controler import InputRecord
from .logging_setup import untrusted
from .validation import HASH_PATTERN

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


PROGRAM = "qm_etdac_calculator"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def provenance(inputs: Sequence[InputRecord]) -> dict[str, str]:
    """The file-level attributes of ADR 0006 for a result made from `inputs`."""
    return {
        "program": PROGRAM,
        "program_version": __version__,
        "created_utc": _utc_now(),
        "input_files": json.dumps([{"path": r.path, "sha256": r.sha256} for r in inputs], ensure_ascii=True),
    }


def _write_groups(results: Mapping[str, pd.DataFrame], temporary: Path, attrs: Mapping[str, str]) -> None:
    """Write every sample into a new file (mode "x": the temporary name must not exist)."""
    with h5py.File(temporary, "x") as file:
        for hash_, frame in results.items():
            group = file.create_group(f"sample_{hash_}")
            group.create_dataset("ETDAC_matrix", data=frame.to_records(index=True), compression="gzip")
            group.attrs["hash"] = hash_
            group.attrs["column_name"] = frame.columns.name
            group.attrs["index_name"] = frame.index.name


def write_etdac_h5(results: Mapping[str, pd.DataFrame], path: Path) -> None:
    """
    Write the ETDAC matrices to a new .h5 file at `path`, atomically and without overwriting.

    Args:
        results: {hash: ETDAC matrix}, e.g. from Operations.etdac_batch; written in this order.
        path: the file to create (from prepare_outputs); must not exist.
    Raises:
        OutputError: `path` exists, or appeared while the file was being written.
        ValueError: no results, or a key that is not a valid hash (a program error: the
            keys come from validated list files).
    """
    if not results:
        raise ValueError("no results to write")
    for hash_ in results:
        if HASH_PATTERN.fullmatch(hash_) is None:
            raise ValueError(f"invalid sample hash {untrusted(hash_)}")
    if path.exists() or path.is_symlink():
        raise OutputError(f"{untrusted(path.name)} already exists in {untrusted(str(path.parent))}; it is never overwritten")

    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    try:
        _write_groups(results, temporary)
        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())  # on disk before it gets its final name
        try:
            os.link(temporary, path)  # FileExistsError if the name appeared meanwhile: never overwrites
        except FileExistsError:
            raise OutputError(
                f"{untrusted(path.name)} appeared in {untrusted(str(path.parent))} while this run was writing it "
                f"(another run?); it already exists and is never overwritten"
            ) from None
    finally:
        temporary.unlink(missing_ok=True)
    logger.info("wrote %d sample(s) to %s", len(results), untrusted(str(path)))
