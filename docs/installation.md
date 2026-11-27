# Installation guide for qm_etdac_calculator

## Requirements

- **OS**: Linux (primary support).
- **Python**: 3.11 or later.
- **Inputs**: matrices produced by [xas-qmol-parser](https://github.com/caraortizmah/x-ray_scripting_out) from ORCA XAS calculations (see [input-format.md](input-format.md)).

The Python dependencies (numpy, pandas, h5py) are installed automatically.

## Install

### From PyPI (not released yet)

```bash
pip install qm_etdac_calculator
```

### From the repository

```bash
git clone https://github.com/caraortizmah/atomistic_oscillator_strength.git
cd atomistic_oscillator_strength
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

A virtual environment (`.venv`) keeps the program and its dependencies separate from the rest of your system. Activate it with `source .venv/bin/activate` whenever you want to use the program.

To set up a development environment (locked dependencies, tests), see [development.md](development.md).

## Verify the installation

```bash
python3 -c "from importlib.metadata import version; print(version('qm_etdac_calculator'))"
```

Expected output: the installed version, e.g. `1.2.0.dev0`.

## Run

The `qm-etdac` command is being completed for release 1.2.0 ([examplesrun.md](examplesrun.md)). Until then, run the calculation from Python as shown in the [README](../README.md#run).

## Troubleshooting

### Command not found

If `qm-etdac` is not found after installation, check that the virtual environment is active and the package is installed:

```bash
source .venv/bin/activate
pip show qm_etdac_calculator
```

## Uninstall

```bash
pip uninstall qm_etdac_calculator
```

This removes only the program. Your results in `etdac_outputs/` are your data and are never touched.

Enjoy! :)
