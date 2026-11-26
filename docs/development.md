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


