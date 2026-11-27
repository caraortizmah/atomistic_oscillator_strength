# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `docs/project-state.md`: status, decisions and plan.
- `docs/adr/`: architecture decision records 0001–0006.
- `requirements-dev.txt`: hashed lock file generated with pip-tools.
- `scripts/dev-setup.sh`: one-time developer setup (`.venv` + locked install).
- `scripts/clean.sh`: removes generated development artefacts (`--dry-run`, `--all`).
- `README.md`: license notice (GPL-3.0-or-later).
- Tests in three layers: hand-computed (`tests/test_handcomputed.py`), notebook
  equivalence (`tests/test_notebook_equivalence.py`) and golden (`tests/test_golden.py`);
  frozen notebook reference `tests/notebook_reference.py`.
- `tests/data/phe_tyr/`: public Phe–Tyr data set (52 geometries, 3.5–11.0 Å) with its
  reference ETDAC output, committed for the golden test.
- ADR 0005 (input validation: allowlist, fail closed; context-aware output encoding;
  CSV/formula injection) and ADR 0006 (provenance metadata in output files).
- `docs/development.md`: "Running tests" section.
- `logging_setup.py`: `configure_logging` (console INFO by default, DEBUG with
  `--verbose`/`--debug`; optional DEBUG log file opened in mode "x", never overwritten;
  safe to call twice), `untrusted()` (repr + truncation for untrusted values) and
  `SafeFormatter` (escapes newlines and terminal control codes: CWE-117 log injection).
  Tests in `tests/test_logging.py`.
- `Operations.etdac_batch` logs which non-contributing core MOs were removed per sample
  (DEBUG, only when any) and a summary line (INFO); replaces the old `report_trimmed`.
- `docs/development.md`: "Logging and debugging" section (levels, flags, `caplog`, `breakpoint()`,
  `pytest --pdb`, VS Code debug configuration).
- `errors.py`: `InputError`, raised on purpose for invalid input files (shared by the
  readers and the validation).
- `gate_controler.parse_list_file`: strict reading of list files (`hash,path` per line):
  UTF-8 only; BOM removed (INFO); `\r\n` / `\r` line endings accepted (INFO), mixed ones
  accepted with a WARNING; blank lines ignored with a WARNING; control and invisible
  characters rejected (including bidirectional overrides, "Trojan Source"); exactly two
  non-empty fields without leading/trailing spaces; spaces inside paths give a WARNING.
  Tests in `tests/test_controler.py`.
- `gate_controler.Controler` and `default_data_root` (path policy, ADR 0003/0004): reads
  only inside its data root (default: parent of the logs folder); list file must be inside;
  absolute paths rejected; relative paths resolve against the list file's folder; symlinks
  followed, so links escaping the root are rejected; whole-component check (`is_relative_to`,
  no string prefixes); target must be an existing regular file.

### Changed

- `etdac_operations.py` rewritten: `etdac_matrix` (single sample, formerly
  `ts_psb_acore_bvirt`) as an explicit loop over shared MO labels, without `try/except`;
  `Operations` (option `trim_core=True`) with `etdac_batch` (all samples, formerly
  `heatmap_ETDAC` plus formatting); inputs are never modified. `etdac_matrix(..., return_transition=True)`
  also returns the step-1 matrix (formerly the notebook option `atm_to_virtmo`). Other notebook
  helpers kept unchanged.
- `__init__.py`: imports only the working operations, so `import qm_etdac_calculator` works
  again; `ConfigMan`, `Scheme` and `cli` return as they are fixed (steps 5c-6).
- `pyproject.toml`: pytest `golden` marker, `--strict-markers`, `tests` on the import path.
- `.gitignore`: re-includes `tests/data/phe_tyr/` only.
- Package moved to `src/qm_etdac_calculator/` (src layout); `pyproject.toml` sets `package-dir`.
- `pyproject.toml`: runtime dependencies declared (numpy, pandas, h5py); Python >= 3.11;
  license as SPDX expression `GPL-3.0-or-later`; version read from `__version__` (single source);
  `dev` extra is now pip-tools, pytest, pytest-cov; `test` extra and `py.typed` declaration removed.
- Version is now `1.2.0.dev0`.
- `.gitignore` ignores virtual environments by pattern (`venv*/`, `.venv*/`).
- `docs/installation.md`: `pyproject.toml` is the single build file; pip >= 21.3 required for editable installs.

### Removed

- `gate_controler.py` notebook leftovers (`is_datawell`, `get_dict_data`, `save_ETDAC_matrix`,
  module-level notebook code); reading returns in step 5c, writing in step 5e.
- `setup.py`: duplicated package discovery from `pyproject.toml` with conflicting settings.
- `requirements.txt`: duplicated the dev extras, had a typo (`pytest-conv`) and listed unused packages.

## [1.1.0]

Tagged in git; no changelog was kept before this file.

## [0.5.2]

Tagged in git; no changelog was kept before this file.
