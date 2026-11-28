# Guide to run qm-etdac-calculator

## Available commands

The installed program provides two commands: `qm-etdac` runs the calculation, `qm-etdac-test` is a built-in self-check (being completed, step 6.6). Without the installed console scripts, for example while developing, the same command runs as a Python module:

```bash
python -m qm_etdac_calculator.cli noauto --list-input F1 F2 F3
```

There are two ways to run the calculation: with the settings on the command line (`noauto`) or in a JSON file (`auto`).

### 1. noauto mode

```bash
qm-etdac noauto --list-input F1 F2 F3 [--paths-inout LOGS] [--verbose | --debug]
```

- `F1`, `F2`, `F3`: the three list files, in this order: core-MO populations, virtual-MO populations, core-electron transition intensities. Their format is described in [input-format.md](input-format.md); the theory is in equations 4 and 5 of the [publication](https://pubs.rsc.org/en/content/articlelanding/2025/cp/d4cp04615c).
- `LOGS`: the project folder that contains the three list files (see [Project folder](input-format.md#project-folder)). Without `--paths-inout`, the folder where you run the command.
- The results go to `LOGS/etdac_outputs/`: `data_etdac_matrix.h5` and the run log `data_etdac_matrix.log`. An earlier result there is kept as `data_etdac_matrix_oldversionN`, never overwritten.
- `--verbose` shows more detail on the screen; `--debug` also shows the full error trace, useful when reporting a problem.
- The older form `--paths-inout LOGS OUTPUT` is rejected: the output folder is no longer chosen, it is always `LOGS/etdac_outputs/`.

Example with the Phe-Tyr data shipped in the repository:

```bash
cd tests/data/phe_tyr
qm-etdac noauto --list-input resA_MOcore_list.log resB_MOvirt_list.log corevirt_fosce_AB_list.log
```

If an input is wrong, the program prints one line starting with `ERROR:`, writes no new result and stops with exit code 1. The run log in `etdac_outputs/` records the same message.

### 2. auto mode

```bash
qm-etdac auto CONFIG.json [--verbose | --debug]
```

The JSON file holds the same settings as the `noauto` command, under four keys, all required:

```json
{
  "corepop": "resA_MOcore_list.log",
  "virtpop": "resB_MOvirt_list.log",
  "etranscv": "corevirt_fosce_AB_list.log",
  "logspath": "tests/data/phe_tyr"
}
```

- `corepop`, `virtpop`, `etranscv`: the three list files, in the same order as `F1 F2 F3` of `noauto`, inside `logspath`.
- `logspath`: the project folder (see [Project folder](input-format.md#project-folder)), relative to the folder where you run the command, or absolute.
- The results go to `<logspath>/etdac_outputs/`, exactly as with `noauto`.
- The file is checked strictly: exactly these four keys, each value a non-empty text, no key twice. Files from older versions with an `outputpath` key are rejected: the output folder is no longer chosen.
- Every mistake in the file gives one line starting with `ERROR:` that names the file (for invalid JSON also the line and column), and the program stops with exit code 1.

Example: save the JSON above as `run.json` in the repository folder and run:

```bash
qm-etdac auto run.json
```
