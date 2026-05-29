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
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install package in development mode

```bash
pip install -e .
```

### 4. Install development dependencies

```bash
pip install -e ".[dev]"
```

This installs:
- pytest and pytest-cov (testing)
- shellcheck-py (shell script linting)
- pandas


##  Verify installation

### 1. Check package installation

```bash
python3 -c "import qm_etdac_calculator; print(qm_etdac_calculator.__version__)"
```

Expected output: `1.0.0`

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
- **Python**: 3.8 or later
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