"""
Run settings of an ETDAC calculation: which three list files to read, and where they are.

ConfigMan holds the four settings of a run under the documented keys (the keys of
`qm-etdac auto` JSON files), so `ConfigMan(**settings)` builds it from such a dict:

- corepop: list file of the core-MO population files
- virtpop: list file of the virtual-MO population files
- etranscv: list file of the core-electron transition intensity files
  (oscillator strengths, core to virtual MOs)
- logspath: folder that contains the three list files (the project folder)

The results always go to `etdac_outputs` inside the logs folder (output_dir()); the output
folder is not a setting, so a run cannot write anywhere else (least privilege, ADR 0007).
`outputpath`, a setting until step 6.2, is now an unknown key.

ConfigMan only holds settings; it opens no file. The list files and every file they name
are checked when Controler reads them (path policy, ADR 0003/0004), so there is one place
that decides what may be read. A missing or unknown key is a TypeError from the constructor
(a programming error).

read_config() reads the settings from the JSON file of `qm-etdac auto` with a strict schema
(ADR 0003): a JSON object with exactly the four keys, each a non-empty string; duplicate keys
are rejected, because Python's json would keep the last one silently. Every problem is an
InputError naming the file. Paths in the file are relative to the folder where the command
runs, like command-line arguments.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, NamedTuple

from .errors import InputError
from .logging_setup import untrusted, untrusted_path
from .outputs import DEFAULT_OUTPUT_DIR

_CONFIG_HINT = "(see docs/examplesrun.md, auto mode)"


class ListFiles(NamedTuple):
    """The three list files of a run, in the order the calculation uses them."""

    core: Path
    virt: Path
    etrans: Path


@dataclass(frozen=True)
class ConfigMan:
    """The settings of one run; frozen, so they cannot change while the run uses them."""

    corepop: str
    virtpop: str
    etranscv: str
    logspath: str

    def list_files(self) -> ListFiles:
        """The three list files, as paths inside the logs folder (not checked here)."""
        logs = Path(self.logspath)
        return ListFiles(core=logs / self.corepop, virt=logs / self.virtpop, etrans=logs / self.etranscv)

    def output_dir(self) -> Path:
        """The only folder a run writes to: `etdac_outputs` inside the logs folder (ADR 0007)."""
        return Path(self.logspath) / DEFAULT_OUTPUT_DIR


_KEYS = tuple(field.name for field in fields(ConfigMan))


def _keys(names: list[str]) -> str:
    return ", ".join(untrusted(name) for name in names)


def read_config(path: Path | str) -> ConfigMan:
    """
    Read the settings of a run from a JSON file (`qm-etdac auto`).

    Raises:
        InputError: the file is missing, not UTF-8 or not JSON; it is not a JSON object;
            a key is unknown, missing or duplicated; a value is not a non-empty string.
    """
    where = untrusted_path(path)
    try:
        data = Path(path).read_bytes()
    except FileNotFoundError:
        raise InputError(f"config file not found: {where}") from None
    except OSError as error:
        raise InputError(f"cannot read config file {where}: {error.strerror}") from None
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise InputError(f"{where} is not valid UTF-8 (byte {error.start}) {_CONFIG_HINT}") from None

    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        seen: set[str] = set()
        for key, _ in pairs:
            if key in seen:
                raise InputError(f"{where}: duplicate key {untrusted(key)} {_CONFIG_HINT}")
            seen.add(key)
        return dict(pairs)

    try:
        settings = json.loads(text, object_pairs_hook=no_duplicates)
    except json.JSONDecodeError as error:
        raise InputError(
            f"{where} is not valid JSON: {error.msg} (line {error.lineno}, column {error.colno}) {_CONFIG_HINT}"
        ) from None
    if not isinstance(settings, dict):
        raise InputError(f"{where} must be a JSON object with the keys {_keys(list(_KEYS))} {_CONFIG_HINT}")

    if "outputpath" in settings:
        raise InputError(
            f"{where}: 'outputpath' is no longer a setting: results go to <logspath>/{DEFAULT_OUTPUT_DIR} "
            f"(ADR 0007); remove the key"
        )
    unknown = sorted(set(settings) - set(_KEYS))
    if unknown:
        raise InputError(
            f"{where}: unknown key{'s' if len(unknown) > 1 else ''} {_keys(unknown)}; "
            f"expected {_keys(list(_KEYS))} {_CONFIG_HINT}"
        )
    missing = sorted(set(_KEYS) - set(settings))
    if missing:
        raise InputError(f"{where}: missing key{'s' if len(missing) > 1 else ''} {_keys(missing)} {_CONFIG_HINT}")
    for key in _KEYS:
        value = settings[key]
        if not isinstance(value, str) or value == "":
            raise InputError(f"{where}: {key!r} must be a non-empty string, found {untrusted(value)} {_CONFIG_HINT}")
    return ConfigMan(**settings)
