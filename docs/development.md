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
