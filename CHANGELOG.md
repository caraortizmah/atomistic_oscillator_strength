# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `docs/project-state.md`: status, decisions and plan.
- `docs/adr/`: architecture decision records 0001–0004.
- `requirements-dev.txt`: hashed lock file generated with pip-tools.

### Changed

- `pyproject.toml`: runtime dependencies declared (numpy, pandas, h5py); Python >= 3.11;
  license as SPDX expression `GPL-3.0-only`; version read from `__version__` (single source);
  `dev` extra is now pip-tools, pytest, pytest-cov; `test` extra and `py.typed` declaration removed.
- Version is now `1.2.0.dev0`.
- `.gitignore` ignores virtual environments by pattern (`venv*/`, `.venv*/`).
- `docs/installation.md`: `pyproject.toml` is the single build file; pip >= 21.3 required for editable installs.

### Removed

- `setup.py`: duplicated package discovery from `pyproject.toml` with conflicting settings.
- `requirements.txt`: duplicated the dev extras, had a typo (`pytest-conv`) and listed unused packages.

## [1.1.0]

Tagged in git; no changelog was kept before this file.

## [0.5.2]

Tagged in git; no changelog was kept before this file.
