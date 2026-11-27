# Development Guide for qm-etdc-calculator

Additional information about the program work

### Direct Execution (without installation or Python)

Read [../README.md](README.md) to understand how the program works.

Go to the repository, you should see folders such as `docs/`, `bin/`, `tests` and `src/qm_etdac_calculator`

> Note: the package now lives in `src/` (src layout). Direct execution of `cli.py` is
> broken in 1.1.0 and will be replaced in step 6; until then, use an editable install.

Then, to run `qm-etdac` type:

```bash
python src/qm_etdac_calculator/cli.py 
```

and ro tun `qm-etdac-test` type:

```bash
python src/qm_etdac_calculator/cli.py test
```



## Running tests

With the development environment active (`source .venv/bin/activate`):

```bash
pytest                      # all tests
pytest -m "not golden"      # skip the golden test on real data
pytest -m golden            # only the golden test
pytest tests/test_handcomputed.py -k case_a   # one file, one test
```

The tests come in three layers:

| File | Layer | What it proves |
|------|-------|----------------|
| `tests/test_handcomputed.py` | hand-computed | tiny cases you can check with pencil and paper (see the comments in the file) |
| `tests/test_notebook_equivalence.py` | notebook equivalence | the package computes exactly what the reference notebook computes, on random inputs shaped like real data |
| `tests/test_golden.py` | golden | the package reproduces the published Phe–Tyr results (52 geometries, 3.5–11.0 Å) |

- The golden data set is the π-stacked phenylalanine–tyrosine pair of the paper cited in the README; its origin and format are described in `tests/data/phe_tyr/README.md`.
- `tests/notebook_reference.py` is a frozen, verbatim copy of the notebook's functions. It is the reference the package is compared against and must not be edited (ADR 0002).
- "Random" inputs use fixed seeds, so every run is identical. They test the arithmetic,
  not the chemistry; the chemistry is covered by the golden test.

### Why the tests compare against the notebook

The reference notebook (`popmatrices/Bigscale/ETDAC_matrix_calculator.ipynb`) produced the
published results, so it is the only trusted definition of a correct ETDAC matrix. The
package is a rewrite of it: new structure, new names, a vectorised kernel. Rewrites can
change behaviour silently (a label mismatch handled differently, the ÷100 moved).

- **Test oracle.** `tests/notebook_reference.py` is a frozen copy of the notebook's
  functions: a trusted source of correct answers the package is checked against.
- **Differential testing.** The 52 real samples happen to have no all-zero columns and
  sorted atoms. With the notebook's code in the tests, both implementations can be given
  *any* input (random matrices, partial label overlaps, zero columns) and must agree. This
  explores cases the real data never contains.
- **Verbatim, never edited.** If the copy were "fixed", it would stop being a reference, and
  a test could pass while both versions are wrong in the same way. It keeps the notebook's
  style (including bare `except:`) because it is evidence, not code to maintain.
- **Characterization test** (M. Feathers): before refactoring legacy code, capture what it
  does as tests, then refactor under their protection. A failure points at the package,
  because the reference never changes.

### When to retire the notebook reference

The notebook reference is a transition tool, not a permanent part of the test suite. Retire
it deliberately, with a new ADR superseding ADR 0002, when both are true:

1. A release of the package has been validated against the notebook (all three test layers
   green), so the package's own outputs can become the reference.
2. The method is intentionally changed or extended (a new weighting, a new normalisation),
   so "same numbers as the notebook" is no longer the goal and the equivalence test would
   block legitimate changes.

Then: delete `tests/notebook_reference.py` and `tests/test_notebook_equivalence.py`, keep
the hand-computed and golden tests, and regenerate the golden reference with the released
package (recording its version and provenance, ADR 0006). Until then, keep it.

## Logging and debugging

### Logging

- Every module logs through its own logger: `logger = logging.getLogger(__name__)`. Modules
  never configure logging; only the program entry point calls
  `qm_etdac_calculator.logging_setup.configure_logging()`.
- Console (stderr): INFO and above by default; DEBUG with `--verbose` or `--debug`.
  `--debug` also shows full tracebacks (CLI, step 6).
- Log file: every run writes a DEBUG log next to its results in the output folder, under
  the never-overwrite rule (ADR 0003); together with the provenance attributes (ADR 0006)
  it records how each result was produced.
- No `NullHandler` on purpose: when the package is used without configuration (e.g. from a
  notebook), Python still prints WARNING and above, so validation warnings are never lost.
- Security (ADR 0005, CWE-117): untrusted values go into messages through `untrusted()`
  (repr, truncated), and `SafeFormatter` escapes control characters, so one record is
  always one line and cannot inject terminal codes.
- Write log calls as `logger.debug("%s: …", value)`, not with f-strings: the text is only
  built if the message is actually emitted.

In tests, the `caplog` fixture captures log records:

```python
def test_something(caplog):
    caplog.set_level(logging.DEBUG, logger="qm_etdac_calculator")
    ...  # run the code
    assert "expected text" in caplog.text
```

### Debugging

- `breakpoint()` anywhere in the code stops there and opens the Python debugger (pdb).
  Useful commands: `n` next line, `s` step into, `c` continue, `p expr` print, `l` list
  code, `q` quit. Remove it before committing.
- `pytest --pdb` opens the debugger at the point where a test fails; `pytest -x --pdb`
  stops at the first failure.
- `python -m pdb script.py` runs a script under the debugger from the first line.
- If results look stale after editing code, clear the bytecode cache: `scripts/clean.sh`.

VS Code: create `.vscode/launch.json` (ignored by git) with, for example:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "pytest: current file",
      "type": "debugpy",
      "request": "launch",
      "module": "pytest",
      "args": ["${file}", "-x", "-q"],
      "justMyCode": false
    }
  ]
}
```

Set breakpoints by clicking left of a line number, then run this configuration (F5).
