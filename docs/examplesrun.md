# Guide to run qm-etdac-calculator

## Available commands

For the installed version there are two main commands: `qm-etdac` and `qm-etdac-test`

For non-installed version or developing mode program `qm-etdac` can be used by typing:

```bash
python src/qm_etdac_calculator/cli.py
```

and `qm-etdac-test` by typing:

```bash
python src/qm_etdac_calculator/cli.py test
```

Regarding running the ETDAC calculator, there are two modes of doing it:
     
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
qm-etdac auto 'json_file'
```

where the JSON file is a dictionary that contains the five arguments presented in the `noauto` mode.
More information regarding the format in [examples folder](../examples/).
