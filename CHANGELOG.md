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
- `docs/input-format.md`: the simple, robust input format (list files and CSV headers),
  what is tolerated, and common mistakes. Every format error ends with a pointer to it.
- `Controler.load_dict_data` (formerly the notebook's `load_dict_data`): reads every CSV of a
  list file through the path policy; checks the whole list (duplicate hashes are an error,
  never silently overwritten) before opening any CSV; logs `loaded N entries` (INFO).
  Reproduces the notebook loader exactly on all 52 Phe-Tyr samples. `Controler`,
  `default_data_root` and `InputError` exported from the package.
- `validation.py` (ADR 0005, step 5d): `check_hash` (1 to 64 ASCII letters or digits, explicit
  pattern with `fullmatch`; `isalnum()`/`\w` would accept non-ASCII) applied in the first pass of
  `load_dict_data`; `check_same_hashes` (every sample in all three inputs, any order).
  Tests in `tests/test_validation.py`.
- CSV files are read in three stages (ADR 0005): bytes read once (a test simulates a file swapped
  between check and parse), raw text checked before pandas interprets anything
  (`gate_controler.read_text_lines`, shared with list files, and `validation.check_csv_structure`:
  no spaces around cells, no quotes, exact header, unique non-negative integer labels, rows as long
  as the header), then parsed exactly as the notebook did. Broken CSV files are an `InputError`
  naming list file, line, hash and CSV file instead of raw pandas errors.
- `validation.check_csv_values` (ADR 0005, stage 2 of the CSV reader): numbers must match an explicit
  pattern before conversion (`float()` accepts `nan`, `inf`, `1_000`, non-ASCII digits) and be finite;
  populations and oscillator strengths >= 0 (`-0.0` accepted); `sym`/`lvl` 1 to 8 ASCII letters;
  `.5` / `5.` read as 0.5 / 5.0 with one warning per file. `nan` in a CSV no longer spreads silently.
- Population warnings (ADR 0005): a value above 100 %, or an MO column adding up to more than 100 % ("at the edge" up to 102.5 %, "beyond the rounding tolerance" above), gives one warning per CSV file with counts, first occurrences and what to check. Sums use `math.fsum` plus a 1e-9 tolerance, so float noise (`0.4 + 32.2 + 67.4`) never warns; sums below 100 % are normal and give no warning.
- Size limits (ADR 0005) against resource exhaustion: list files up to 10 000 entries, 10 001 to 10 100 with a warning to split the samples, more is an error; list files at most 3 MB and CSV files at most 50 MB, read with `gate_controler.read_limited()`, which never reads more than limit + 1 bytes. The errors say they come from the size policy, not from a program error.
- `docs/input-format.md`: size limits section; hashes of at most 9 characters recommended.
- `outputs.prepare_outputs` (ADR 0003): creates the output folder (default `etdac_outputs/`; not a file, not a symbolic link), checks the output name, and keeps an existing `<stem>.h5` / `<stem>.log` pair as `<stem>_oldversionN` (highest N + 1, same N for both) with a warning that it may come from another job or system; renames never overwrite (`os.link`). New `errors.OutputError`.
- `outputs.write_etdac_h5` (ADR 0003): writes the results with the notebook's `.h5` layout (unchanged for existing readers), to a hidden temporary file that is fsynced and then published with `os.link`: never overwrites, never leaves a half-written result. `tests/notebook_reference.py` gains the notebook's `save_ETDAC_matrix` (verbatim) as the layout reference; the golden test now also runs end to end through the package's loader and writer.
- Provenance in every `.h5` result (ADR 0006): file attributes `program`, `program_version`, `created_utc` and `input_files` (JSON, paths relative to the data root, SHA-256 of each list file and CSV). `Controler.inputs_read` records every file whose content passed the checks, hashing the bytes that were checked (never a second read). `write_etdac_h5` now takes the inputs as a required argument.
- Hash policy marked temporary in code comments, ADR 0005 and `docs/input-format.md`: hashes will have to be unique across all list files of one system once multi-file runs exist.
- ADR 0005: list-file format details decided in step 5c; ADR 0003/0004: implementation notes.
- `docs/input-format.md` and ADR 0005: the 2.5 rounding tolerance covers systems of up to 47 atoms with one decimal; larger systems need more precise values (user's responsibility).

### Changed

- Paths in messages are shown complete (`logging_setup.untrusted_path`, up to 4096 characters) instead of being cut after 80 characters, still escaped with `repr()`; 15 messages in `gate_controler.py` and `outputs.py`. Values from file contents keep the short limit of `untrusted()`.
- `qm-etdac noauto` works again, inside the package (step 6.3): `cli.main` replaces the call of `bin/manager_etdac.py`; `--list-input F1 F2 F3 [--paths-inout LOGS]`, with the current folder as default; `--verbose`, `--debug`; results and run log in `LOGS/etdac_outputs/`; input and output problems are one `ERROR:` line with exit code 1 (`--debug` adds the traceback). A second `--paths-inout` value (the old output folder) is rejected with an explanation. `docs/examplesrun.md`: noauto section rewritten, dead `examples` link removed.
- Project folder (ADR 0007, step 6.2): a run writes only to `etdac_outputs/` inside the logs folder (`ConfigMan.output_dir()`); the output folder is no longer a setting, and `outputpath` is rejected as an unknown key. Before, the default was `./etdac_outputs/` in the folder where the program ran, and any folder could be chosen. `docs/input-format.md`: "Project folder" section. `.gitignore` ignores `etdac_outputs/`.
- `default_data_root`: a logs folder that does not exist gives an `InputError` ("logs folder not found") instead of a bare `FileNotFoundError` traceback (step 6.1).
- `etdac_calculator.py` rewritten (step 5f): `Scheme(config)` runs one calculation in two steps, `prepare_outputs()` (output folder, earlier result kept) and `run(paths)` (one `Controler` reads the three inputs, `Operations.etdac_batch` calculates, `write_etdac_h5` writes with provenance); the notebook leftovers are removed. `Scheme` is exported from the package again; the README example uses it. End-to-end golden test in `tests/test_scheme.py`.
- `config.py` rewritten (step 5f): `ConfigMan` holds the run settings under the documented keys (`corepop`, `virtpop`, `etranscv`, `logspath`, `outputpath`, default `etdac_outputs`), frozen; `list_files()` gives the three list files inside the logs folder. A missing or unknown key is an error. `ConfigMan` is exported from the package again.
- `Operations.etdac_batch` checks that the three inputs contain the same samples: a sample missing
  from the virtual input was silently dropped before, one missing from the core input raised a bare
  `KeyError`; both are now an `InputError`.
- List-file reader: a lone `\r` in a file that also uses `\n` or `\r\n` line endings is now an
  error (not interpreted); `\n` mixed with `\r\n` stays a warning. The warning for spaces in
  paths names the risk (shell commands and tools that do not quote paths).
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

- `ConfigMan.checker_outpath`, `checker_log_file`, `checker_logs` and `load`: they repeated the checks of `Controler` and read whole files outside the path policy and the size limits (ADR 0003, ADR 0005).
- `gate_controler.py` notebook leftovers (`is_datawell`, `get_dict_data`, `save_ETDAC_matrix`,
  module-level notebook code); reading returns in step 5c, writing in step 5e.
- `setup.py`: duplicated package discovery from `pyproject.toml` with conflicting settings.
- `requirements.txt`: duplicated the dev extras, had a typo (`pytest-conv`) and listed unused packages.

### Security

- `bin/manager_etdac.py`: removed the `mkdir -p` run through a shell (`shell=True`) with a path typed by the user (command injection, CWE-78); the output folder is created by `outputs.prepare_outputs` with `os.makedirs` (ADR 0003). The ruff security rules (`S`, step 8) will check the whole code for shell calls.

## [1.1.0]

Tagged in git; no changelog was kept before this file.

## [0.5.2]

Tagged in git; no changelog was kept before this file.
