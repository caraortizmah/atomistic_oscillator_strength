# Installation Guide for qm-etdac-calculator

## Quick Install

### From PyPI, mainly for users (not released yet)

```bash
pip install qm_etdac_calculator
```

## From repo, mainly for developers (as a package)

For development and testing:

### 1. Clone repo

```bash
git clone https://github.com/caraortizmah/atomistic_oscillator_strength.git
cd atomistic_oscillator_strength
```

### 2. Create virtual environment (recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python3 -m pip install --upgrade pip  # editable installs need pip >= 21.3
```

Any folder name matching `venv*/` or `.venv*/` is ignored by git.

All build configuration and dependencies are declared in `pyproject.toml` (PEP 621).
There is no `setup.py` or `requirements.txt`. Development uses a hashed lock file,
`requirements-dev.txt`, generated from `pyproject.toml` with pip-tools
(see `docs/adr/0001-pip-tools-before-uv.md`).

### 3. Install the locked development dependencies

```bash
python3 -m pip install --require-hashes -r requirements-dev.txt
```

This installs exactly the versions recorded in the lock file, and pip refuses any
download whose hash does not match. It contains:
- numpy, pandas, h5py (runtime)
- pytest and pytest-cov (testing)
- pip-tools (to regenerate the lock file)

### 4. Install the package in development (editable) mode

```bash
python3 -m pip install --no-deps -e .
```

`--no-deps` because the dependencies already came from the lock file in step 3.

### Updating the lock file

After changing dependencies in `pyproject.toml`:

```bash
pip-compile --extra dev --generate-hashes --allow-unsafe --strip-extras \
    -o requirements-dev.txt pyproject.toml
pip-sync requirements-dev.txt && python3 -m pip install --no-deps -e .
```

To upgrade all pinned versions, add `--upgrade` to `pip-compile`.
The lock file is valid for the Python version and OS it was compiled on.


##  Verify installation

### 1. Check package installation

```bash
python3 -c "from importlib.metadata import version; print(version('qm_etdac_calculator'))"
```

Expected output: `1.2.0.dev0`

### 2. Verify Command Availability

```bash
which qm-etdac
which qm-etdac-test
```

## Setup and check the Pipeline

Now you can run by your own

## Run Pipeline

```bash
qm-etdac
```

## Documentation for Pipeline usage

Read  
(...)

## System Requirements

- **OS**: Linux (primary support)
- **Python**: 3.11 or later
- **Shell**: Bash 4.0+
- **xas-qmol-parser**: Output retuls from the repo [https://github.com/caraortizmah/x-ray_scripting_out](xas-qmol-parser)
- **Tools**: Standard Unix utilities (grep, awk, sed, etc.)

## Troubleshooting

### Command Not Found

If `qm-etdac` or `qm-etdac-test` commands are not found after installation:

```bash
# Verify installation path
pip show qm_etdac_calculator

# Reinstall in editable mode
pip install --force-reinstall -e .
```

### Shell Script Permission Errors

If shell scripts aren't executable:

```bash
chmod +x bin/*.sh
```

## Uninstallation

To remove the package (named x-ray-quantumol-parser):

```bash
pip uninstall qm_etdac_calculator
```

In the future contributing.md and publishing.md

Enjoy! :)