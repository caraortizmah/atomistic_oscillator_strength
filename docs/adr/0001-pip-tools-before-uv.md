# ADR 0001: Lock dependencies with pip-tools; revisit uv later

- Status: accepted
- Date: 2026-11-26

## Context

We need reproducible installs for development and CI ("pinned dependencies").
`pyproject.toml` declares compatible version ranges. A lock file records the exact,
tested versions and their hashes. The maintainer knows pip-tools but not uv. Future
targets include a Docker image and use as a node in n8n.

## Decision

Use pip-tools: `pip-compile --generate-hashes` produces `requirements-dev.txt` from
`pyproject.toml`, and `pip-sync` / `pip install --require-hashes` installs it.

## Alternatives considered

- **uv** (`uv.lock`): much faster, manages Python versions and venvs, one
  cross-platform lock file. Rejected for now only because it is new to the maintainer.
- **Exact pins in `pyproject.toml`**: rejected; it makes the package uninstallable next
  to other packages.

## Consequences

- Hash checking stops a tampered or substituted download from being installed.
- The lock file is valid for the Python version and OS it was compiled on.
- Moving to uv later does not touch code, because both read `pyproject.toml`.
  Revisit when the Docker image or n8n work starts. The PEP 751 `pylock.toml`
  standard reduces lock-in for both tools.
