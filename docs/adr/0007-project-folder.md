# ADR 0007: Project folder: one folder authorized for reading, one derived folder for writing

- Status: accepted
- Date: 2026-11-28
- Revises: ADR 0003 (default output folder `./etdac_outputs/` and the `--output-dir` option); D32 in `docs/project-state.md` (`outputpath` setting); the step-6 decision to keep `--paths-inout LOGS [OUTPUT]` (now `--paths-inout LOGS`)

## Context

Until step 6.2 the output folder was a setting (`outputpath`, or the second value of `--paths-inout`), default `./etdac_outputs/` in the folder where the command runs. Reading was strict (data root, path policy, ADR 0003/0004), but writing had no root: any folder the user could write to was accepted and created, parents included. A typo, or a JSON file copied from another project, could send results somewhere unexpected.

The program is going to be installed from PyPI. Where it is installed (a virtual environment, a shared cluster installation) must not decide where data is read or written.

## Decision

- **Project folder.** The folder that contains the three list files (`logspath`) is the project folder. If no folder is given on the command line, it is the folder where the command runs (step 6.3).
- **Layout.** The CSV files are in `inputs/` inside the project folder. This is a documented convention, not a rule the program enforces; the path policy already decides what may be read.
- **Reading.** Unchanged: every path in a list file must resolve inside the data root (ADR 0003), today the parent of the project folder (ADR 0004, temporary).
- **Writing.** A run writes only to `etdac_outputs/` inside the project folder (`ConfigMan.output_dir()`). The output folder is derived, never chosen: there is no `outputpath` setting any more, and a JSON file that still has one is rejected as an unknown key.
- **Installation.** Data is never read from or written to the folder where the program is installed. `pip uninstall`, or deleting a virtual environment, never touches a project folder.
- **Authority.** Only the folder the user gives decides what may be read and written. The content of input files (list files) never extends it.

### Before the PyPI release (least privilege)

ADR 0004 widens the data root to the parent of the project folder, so that the repository's `popmatrices/Bigscale` list files can reach `../newFY_1-26/`. For an installed program run in, for example, `/home/user/project`, that parent is the whole home folder. Before the PyPI release (step 10a) this temporary rule ends: the data root becomes the project folder itself. `tests/data/phe_tyr/` already has the layout (list files and `inputs/` inside), so its golden tests check the strict rule on real data. Consequence: until `popmatrices/` is cleaned up (Future list), the command rejects the `popmatrices/Bigscale` list files; the notebooks are not affected, because they read their data with their own loader.

## Alternatives considered

- Output folder chosen freely (the state before step 6.2): rejected; writing needs no more privilege than one folder next to the inputs.
- `outputpath` as an optional override: postponed. Explicitly authorized folders outside the project belong to the HPC design (Future list), with their own ADR, so that read and write authority are designed together.
- Data next to the installation (e.g. in the virtual environment's folder): rejected; reinstalling or uninstalling would delete results, and on clusters the installation is often read-only or shared.

## Consequences

- One output folder per project folder: results of different systems no longer meet in one `./etdac_outputs/` (a Future item in `docs/project-state.md`, now partly addressed).
- The README example writes into `tests/data/phe_tyr/etdac_outputs/`; `.gitignore` ignores `etdac_outputs/` so results are never committed by mistake.
- Tests that run a calculation work on a copy of the Phe-Tyr folder, so tests never write into `tests/data/`.

## Required tests

- The output paths are in `etdac_outputs/` inside the logs folder (`tests/test_config.py`, `tests/test_scheme.py`).
- `outputpath` is rejected as an unknown key (`tests/test_config.py`).
- A run creates only its result in `etdac_outputs/` and changes nothing else in the data root (`tests/test_scheme.py`).
- Before the release: the golden tests pass with the data root equal to the project folder (step 10a).
