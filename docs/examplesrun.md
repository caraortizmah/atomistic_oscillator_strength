# Guide to run qm-etdac-calculator

## Available commands

For the installed version there are two main commands: `qm-etdac` and `qm-etdac-test`

For non-installed version or developing mode program `qm-etdac` can be used by typing:

```bash
python qm_etdac_calculator/cli.py
```

and `qm-etdac-test` by typing:

```bash
python qm_etdac_calculator/cli.py test
```

Regarding running the ETDAC calculator, there are two modes of doing it:
     
### 1. noauto mode

```bash
qm-etdac noauto --list-input 'file_log1' 'file_log2' 'file_log3' --paths-inout 'logfiles_path' 'output_path'
```

where the first three files (`--list-input` group) are a list of file paths with an identification per file.
The first type of log file corresponds to the core MOs population.
The second type of log file corresponds to the virtual MOs population
The third type of log file corresponds to the electron transition intensities (core to virtual) MOs
The third type of information is an intermediate step. Find further about it in the theory in the equations 4th and 5th in this [xray spectrocopy publication](https://pubs.rsc.org/en/content/articlelanding/2025/cp/d4cp04615c).

the second two files (`--paths-inout` group) are the path where the three log files of the first group are placed and the path were the output of the calculation in H5 format will be placed.

More information regarding the formats of these files in [examples folder](../examples/).

### 2. auto mode

```bash
qm-etdac auto 'json_file'
```

where the JSON file is a dictionary that contains the five arguments presented in the `noauto` mode.
More information regarding the format in [examples folder](../examples/).
