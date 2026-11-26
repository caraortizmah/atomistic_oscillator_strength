#!/usr/bin/env bash

# Developer setup: create .venv and install the locked dev dependencies
# plus the package in editable mode. Run once per clone, or to rebuild .venv.
# The lock file is NOT regenerated here; see docs/installation.md.

set -euo pipefail
cd "$(dirname "$0")/.."            # repo root (this script lives in scripts/)

python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements-dev.txt
.venv/bin/python -m pip install --no-deps -e .

.venv/bin/python -c "from importlib.metadata import version; print('installed', version('qm_etdac_calculator'))"
echo "Done. Activate with: source .venv/bin/activate"
