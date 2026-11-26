# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `docs/project-state.md`: status, decisions and plan.
- `docs/adr/`: architecture decision records 0001–0004.

### Changed

- `.gitignore` ignores virtual environments by pattern (`venv*/`, `.venv*/`).
- `docs/installation.md`: `pyproject.toml` is the single build file; pip >= 21.3 required for editable installs.

### Removed

- `setup.py`: duplicated package discovery from `pyproject.toml` with conflicting settings.
- `requirements.txt`: duplicated the dev extras, had a typo (`pytest-conv`) and listed unused packages.

## [1.1.0]

Tagged in git; no changelog was kept before this file.

## [0.5.2]

Tagged in git; no changelog was kept before this file.
