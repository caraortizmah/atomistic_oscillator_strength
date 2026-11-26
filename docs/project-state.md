# Project state: qm_etdac_calculator

_Last updated: 2026-11-26 · Checkpoint 0b (data-root amendment)_

## How to resume

<!--
Paste the original working prompt plus this file into a new conversation.
 If you have it locally, also paste `.notes/restart.md` (private, not in git).
-->
In case of assistance, this file serves as context for a prompt into a conversation.

## Where we are

- The packaging plan is agreed. Step 0 is committed; amendment 0b (ADR 0004) is in review.
- Code is unchanged since `0d75b23`. The package installs, but `import qm_etdac_calculator`
  fails: notebook leftovers run at import time and there are 59 undefined names.
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
| D2  | The notebook is the numerical source of truth. Virtual matrix untrimmed; ÷100 on the first product only. | ADR 0002 |
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

## Plan

- [x] 0. Docs scaffolding: project-state, ADRs, CHANGELOG, private notes
- [ ] 0b. ADR 0004: temporary parent-folder data root *(in review)*
- [ ] 1. Hygiene: `.gitignore` venv patterns; delete `setup.py` and `requirements.txt`
- [ ] 2. `pyproject.toml`: runtime deps, Python >= 3.11, single-source version; pip-tools lock; dev environment walkthrough
- [ ] 3. `git mv` package into `src/` (pure move)
- [ ] 4. Tests (red): synthetic, notebook-equivalence, golden (skipped without data)
- [ ] 5. Core: logging, I/O with path and output policy, operations matching the notebook, `Scheme` orchestration (green)
- [ ] 6. CLI as documented, inside the package
- [ ] 6b. `etdac_editprinter` as functions; atom-range config
- [ ] 7. Vectorised `ts_psb_acore_bvirt` (spec + failing test provided)
- [ ] 8. ruff (incl. `S` security rules), then mypy, then pre-commit
- [ ] 9. GitHub Actions CI: least-privilege token, SHA-pinned actions, hashed install, build + `twine check`
- [ ] 10. README, docs cleanup (incl. resA/resB naming note, uninstall note), release 1.2.0

## Open questions

- None blocking.
- At step 6b JSON format could be used for the atom-range config, based on
  `popmatrices/Bigscale/conditions_ETDCA.txt`.

## Future (not in 1.2.0)

- Rename the `resA_MOcore` / `resB_MOvirt` files. A and B label fragments and are not tied to
  core or virtual; for now this is documented only.
- Rename `newFY_1-26`, then expose `--data-root`.
- Delete the `workshop_tester` branch (not need it anymore).
- Reduced real dataset, committed, so CI runs the golden test.
- Migrate from pip-tools to uv; Docker image; n8n integration.
- `etdac_viz.py` (heatmaps / GUI).
