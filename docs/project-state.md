# Project state: qm_etdac_calculator

_Last updated: 2026-11-27 - Checkpoint 5d (input validation)_

## How to resume

<!--
Paste the original working prompt plus this file into a new conversation.
 If you have it locally, also paste `.notes/restart.md` (private, not in git).
-->
In case of assistance, this file serves as context for a prompt into a conversation.

## Where we are

- The packaging plan is agreed. Steps 0–4 are committed; step 5 is split into 5a–5f; 5a (calculation), 5b (logging), 5c (reading inputs with the path policy) and 5d (input validation) are done: `pytest` gives 241 passed, including the golden test. Next: 5e (writing outputs).
- `import qm_etdac_calculator` works and exports the operations and the input reader (`Controler`). `config.py`, `etdac_calculator.py`, `cli.py` and the `qm-etdac` command are still broken (notebook leftovers); nothing imports them until 5f and step 6.
- The notebook `popmatrices/Bigscale/ETDAC_matrix_calculator.ipynb` reproduces
  `popmatrices/Bigscale/data_etdac_matrix.h5` exactly (checked on samples f00 and f13).
  This is the golden reference.

## Target for 1.2.0

The repo installs cleanly, tests are green and lint is clean, and a stranger can run it from the README.
That means: PEP 621 `pyproject.toml`, `src/` layout, hashed lock file, ruff + mypy + pytest +
pre-commit, GitHub Actions CI gating on them, a README under one page, and a CHANGELOG.

## Decisions

| ID  | Decision | Record |
|-----|----------|--------|
| D1  | Lock dependencies with pip-tools (hashed). Revisit uv for Docker/n8n. | ADR 0001 |
| D2  | The notebook is the numerical source of truth. Core matrix trimmed (technical safeguard against 0/0 = NaN, no effect on results); virtual matrix untrimmed; ÷100 on the first product only. | ADR 0002 |
| D3  | Filesystem policy: strict data root, outputs only in `etdac_outputs/`, nothing overwritten. | ADR 0003 |
| D3a | Default data root temporarily widened to the parent of the logs folder (rule stays strict) until `newFY_1-26` is renamed. | ADR 0004 |
| D4  | CLI keeps the documented names: `qm-etdac noauto`, `qm-etdac auto`, `qm-etdac check`, `qm-etdac --help`, `qm-etdac-test` (built-in self-check). | here |
| D5  | Python >= 3.11. Next release 1.2.0. | here |
| D6  | `src/` layout. Nothing in `plot/` or `popmatrices/` is moved, renamed or deleted. | here |
| D7  | Tests in three layers: hand-computed synthetic, notebook equivalence, golden (local only for now). `*.csv` stays ignored; synthetic data is generated at test time. | here |
| D8  | Logging with stdlib `logging`; `--verbose` and `--debug` flags. Debugging guide in `docs/development.md`. | here |
| D9  | `etdac_editprinter` becomes tested functions in 1.2.0. Atom ranges come from a config file, not code. | here |
| D10 | I implement the vectorised `ts_psb_acore_bvirt`, keeping the loop version as an explanatory comment. | here |
| D11 | Private notes live in `.notes/`, excluded via `.git/info/exclude`. Public notes: this file and `docs/adr/`. | here |
| D12 | License: GPL v3 or any later version (SPDX `GPL-3.0-or-later`), stated in `pyproject.toml` and `README.md`. | here |
| D13 | Single-source version: `__version__` in `__init__.py`, read statically by setuptools. | here |
| D14 | Developer setup via `scripts/dev-setup.sh` (create `.venv`, install from the lock file - requirements-dev.txt). The lock file is regenerated only on purpose, when dependencies change. `scripts/clean.sh` removes generated artefacts (`--all` also `.venv`). | here |
| D15 | Classes where there is state to protect, functions where there is none: `Operations` (calculation options, e.g. `trim_core=True`), `Controler` (data root, output folder), `Scheme` (orchestration), `ConfigMan` (run settings). Single-sample kernel `etdac_matrix` (was `ts_psb_acore_bvirt`); all samples `Operations.etdac_batch` (was `heatmap_ETDAC` + formatting), returning a dict `{hash: matrix}`. | here |
| D16 | Golden data set: Phe–Tyr, 52 geometries 3.5–11.0 Å (`f10`–`f61`, the paper's range), committed in `tests/data/phe_tyr/` with its reference output (cut from the notebook's `.h5`). Hashes keep their original IDs; `f<number>` is only a convention. | here |
| D17 | Input validation: allowlist, fail closed; warnings for populations > 100 % and for MO sums > 100 % (two levels: "at the edge" up to 102.5 %, "beyond rounding tolerance" above). Size limits fixed for now. Required tests (negative + boundary pairs) listed in the ADR. Context-aware output encoding and CSV/formula injection documented as security examples. | ADR 0005 |
| D18 | Output `.h5` files carry provenance: program, version, UTC time, SHA-256 of every input. | ADR 0006 |
| D19 | Logging: console INFO by default, DEBUG with `--verbose`/`--debug`; a DEBUG log file next to every run's results (never overwritten); no `NullHandler`, so warnings stay visible when the package is used without configuration; `SafeFormatter` + `untrusted()` against log injection. | here |
| D20 | List-file reading: strict structure, tolerated editing leftovers always reported (BOM, `\r\n`/`\r`, mixed `\n`+`\r\n`, blank lines, spaces inside paths); lone `\r` mixed with other endings, control/invisible characters and duplicate hashes are errors; the whole list is checked before any CSV is opened; format errors point to `docs/input-format.md`. | ADR 0005 |
| D21 | CSV reading in three stages: the bytes are read once (no gap between check and parse: TOCTOU), the raw text is checked (same line rules as list files, plain split on commas, no quoting, no spaces around cells, exact header, unique integer labels, rows as long as the header), and only then pandas parses the checked text exactly as the notebook did. Every problem is an `InputError` naming list file, line, hash and CSV file. | ADR 0005 |
| D22 | Values: numbers must match an explicit pattern before conversion and be finite (no `nan`, `inf`, text, formulas, `1_000`, non-ASCII digits); populations and oscillator strengths >= 0 (`-0.0` accepted); `sym`/`lvl` 1 to 8 ASCII letters; `.5` and `5.` read as 0.5 and 5.0 with one warning per file. | ADR 0005 |
| D23 | Samples are paired by hash, not by position: the three inputs must contain the same set of hashes; a hash is 1 to 64 ASCII letters or digits, unique within a list file. This hash policy is temporary (marked "Temporary hash policy") until multi-file runs are designed. | ADR 0005 |
| D24 | Population warnings: one warning per CSV file combining values above 100 % and MO column sums above 100 % ("at the edge" up to 102.5 %, "beyond the rounding tolerance" above); sums with `math.fsum` plus a 1e-9 tolerance; sums below 100 % are normal and give no warning; oscillator strengths have no 100 limit. | ADR 0005 |
| D25 | Size limits: list files up to 10 000 entries (10 001 to 10 100: warning to split the samples; more: error) and at most 3 MB; CSV files at most 50 MB; files read with at most limit + 1 bytes; errors name the size policy, not a program error. Fixed in 1.2.0, configurable later. | ADR 0005 |
| D26 | Scope rule (80:20): the non-critical remainder of a change goes to the Future list instead of being built now, unless it is urgent or critical for security or code structure. | here |

## Plan

- [x] 0. Docs scaffolding: project-state, ADRs, CHANGELOG, private notes
- [x] 0b. ADR 0004: temporary parent-folder data root
- [x] 1. Hygiene: `.gitignore` venv patterns; delete `setup.py` and `requirements.txt`
- [x] 2. `pyproject.toml`: runtime deps, Python >= 3.11, single-source version; pip-tools lock; dev environment walkthrough; fix the "This installs" list in `docs/installation.md`
- [x] 3. `git mv` package into `src/` (pure move)
- [x] 4. Tests (red): hand-computed, notebook-equivalence, golden (Phe–Tyr data committed in `tests/data/phe_tyr/`)
- [ ] 5. Core, in small diffs (one commit per bullet):
  - [x] 5a. Calculation: `etdac_operations.py` rewritten (`etdac_matrix`, `Operations.etdac_batch`, `return_transition`); `__init__.py` imports only working modules; 20 tests green
  - [x] 5b. Logging foundation (`logging_setup.py`: levels, log file, `untrusted()`, `SafeFormatter`); "non-contributing core MOs removed" report and run summary in `etdac_batch`; "Logging and debugging" in `docs/development.md`
  - [x] 5c. Reading inputs: `errors.InputError`; `parse_list_file` (strict format, tolerated leftovers reported); `Controler` + `default_data_root` (path policy, ADR 0003/0004); `load_dict_data` (whole list checked, duplicates rejected, then CSVs read; reproduces the notebook loader on 52 samples); `docs/input-format.md`
  - [x] 5d. Input validation (ADR 0005): hash pattern and the same hashes in all three inputs; CSV read in three stages (bytes once, raw text checked, then parsed) with structure and value rules; population warnings; size limits; the hash policy marked temporary; 241 tests green
  - [ ] 5e. Writing outputs: `_oldversionN` rotation, atomic write, provenance (ADR 0003/0006)
  - [ ] 5f. `Scheme` orchestration; remove notebook leftovers from `etdac_calculator.py`, `gate_controler.py`, `config.py`; end-to-end test through the package loader
- [ ] 6. CLI as documented, inside the package
- [ ] 6b. `etdac_editprinter` as functions; atom-range config
- [ ] 7. Vectorised `etdac_matrix` (was `ts_psb_acore_bvirt`; spec + failing test provided)
- [ ] 8. ruff (incl. `S` security rules), then mypy, then pre-commit
- [ ] 9. GitHub Actions CI: least-privilege token, SHA-pinned actions, hashed install, build + `twine check`; recompile the lock and fail on diff; `pip-audit` (proposed); test on the oldest and newest supported Python (3.11 and 3.14): a 3.12+-only f-string slipped in during 5c and was caught by hand
- [ ] 10. README, docs cleanup (incl. resA/resB naming note, uninstall note, empty "Run Pipeline" section in `docs/installation.md`), release 1.2.0

## Open questions

- Add `pip-audit` (vulnerability scan of the lock file) to CI at step 9? Proposed, not yet decided.
- At step 6b JSON format could be used for the atom-range config, based on
  `popmatrices/Bigscale/conditions_ETDAC.txt`.

## Future (not in 1.2.0)

- **Priority 1 for the next release: HPC / cluster architecture.** Allow explicitly
  authorized data roots outside the program's folders (e.g. a project or scratch space on a
  cluster), configured by the user, never guessed. Work stays inside the authorized paths:
  if code or temporary files must move, they go to a temporary working area *inside* the
  same authorized path, never elsewhere. Same philosophy as ADR 0003/0004: least privilege,
  no lateral movement between folders. Needs its own ADR (supersedes the data-root default
  of ADR 0004 together with the `newFY_1-26` rename).
- Retire the notebook reference (`tests/notebook_reference.py`, `tests/test_notebook_equivalence.py`) once a validated release becomes the reference and the method changes; new ADR superseding ADR 0002 (criteria in `docs/development.md`).
- Size limits (10 000 list entries, 50 MB per CSV) configurable; fixed values become defaults (ADR 0005). A warning zone for CSV sizes, like the one for list entries (10 001 to 10 100), can be added at the same time.
- Hashes unique across all list files of one system (replaces the temporary hash policy of 1.2.0, ADR 0005). A large system can be split into many list files (e.g. 1 000 000 samples in 100 files); a hash must then be unique across all of them, not only within one list file, and hashes will be longer than the 9 characters recommended now. Needs a revision of ADR 0005 together with the design of multi-file runs.
- Better sample IDs than `f<number>` (e.g. derived from the geometry or a UUID).
- Unique output names or IDs instead of the fixed default `data_etdac_matrix` (to discuss).
- Outputs from other jobs or systems in the same output folder: today the program warns and keeps the old result as `_oldversionN`, because it cannot tell whether the result belongs to the same system. A real solution is to discuss, together with unique output IDs: e.g. one output folder per system or job, comparing the provenance of the existing file (ADR 0006 input hashes) with the current run, or refusing to write into a folder that belongs to another system.
- CI must handle one lock file per Python version (the lock is compiled for one interpreter); decide at step 9.
- pandas lower bound (>= 2.1) is untested; the golden check passed on pandas 3.0. Test minimum versions in CI at step 9.
- Rename the `resA_MOcore` / `resB_MOvirt` files. A and B label fragments and are not tied to
  core or virtual; for now this is documented only.
- Rename `newFY_1-26`, then expose `--data-root`.
- Delete the `workshop_tester` branch (not need it anymore).
- Reduced real dataset, committed, so CI runs the golden test.
- Migrate from pip-tools to uv; Docker image; n8n integration.
- `etdac_viz.py` (heatmaps / GUI).
