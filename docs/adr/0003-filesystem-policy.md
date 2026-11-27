# ADR 0003: Filesystem policy: least privilege, never overwrite

- Status: accepted; default data root amended by ADR 0004
- Date: 2026-11-26

## Context

The program reads list files (`hash,path` per line) that point at CSVs, and writes
H5 results. The old code created folders with `shell=True` from user input and wrote
next to wherever it was run. Existing results (for example, `data_etdac_matrix.h5`) must
never be lost.

## Decision

Reading:

- Every path is resolved with `Path.resolve()`, which follows symlinks.
- Paths inside a list file are resolved relative to that list file.
- Absolute paths inside list files are rejected.
- A resolved path outside the data root is rejected. By default the data root is the
  logs folder. A `--data-root` option is designed, but it is only exposed once
  `newFY_1-26` is renamed.
- The JSON config has a strict schema: unknown keys are rejected.

Writing:

- Results go only to the output folder: `--output-dir`, default `./etdac_outputs/`,
  created with `os.makedirs` (never a shell).
- If a target file exists, it is first renamed to `<name>_oldversionN<ext>`, where N is
  the next free number. Existing `_oldversion` files are never renamed.
- New files are written under a temporary name, then atomically renamed into place.

Uninstalling (`pip uninstall`) removes only the installed package. The output folder
and its contents are user data and are never touched.

## Alternatives considered

- Free paths anywhere: rejected (least privilege).
- Overwrite with a `--overwrite` flag: rejected. It is too easy to lose a result.

## Consequences

- The existing Bigscale list files (`../newFY_1-26/...`) need the data root widened
  until the folder is renamed.
- More checks, all covered by tests.
- Implementation: the reading part is implemented in step 5c (`gate_controler.Controler`, `read_list_file`, `load_dict_data`; tests in `tests/test_controler.py`, "Path policy" section). The writing part (output folder, `_oldversionN`, atomic write) follows in step 5e.
