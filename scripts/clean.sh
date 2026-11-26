#!/usr/bin/env bash

# Remove generated development artefacts (caches, build output, egg-info).
# Never touches source code, data, outputs, .notes/ or .git/.
# Usage: scripts/clean.sh [--dry-run] [--all]
#   --dry-run  only list what would be removed
#   --all      also remove .venv (rebuild with scripts/dev-setup.sh); deactivate first

set -euo pipefail
cd "$(dirname "$0")/.."            # repo root (this script lives in scripts/)
[[ -f pyproject.toml ]] || { echo "error: repo root not found" >&2; exit 1; }

dry=0; all=0
for arg in "$@"; do
    case "$arg" in
        --dry-run) dry=1 ;;
        --all)     all=1 ;;
        -h|--help) sed -n '2,7p' "$0"; exit 0 ;;
        *) echo "error: unknown option '$arg' (see --help)" >&2; exit 2 ;;
    esac
done

shopt -s nullglob
targets=( *.egg-info src/*.egg-info build dist .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov )

if (( all )); then
    if [[ "${VIRTUAL_ENV:-}" == "$PWD/.venv" ]]; then
        echo "error: .venv is active; run 'deactivate' first" >&2; exit 1
    fi
    targets+=( .venv )
fi

# __pycache__ folders anywhere, except inside .git/ and .venv/ (.venv is handled as a whole)
while IFS= read -r -d '' d; do targets+=( "$d" ); done < <(
    find . -name __pycache__ -type d -not -path './.git/*' -not -path './.venv/*' -print0
)

removed=0
for t in "${targets[@]}"; do
    [[ -e "$t" ]] || continue
    if (( dry )); then echo "would remove: $t"; else rm -rf -- "$t"; echo "removed: $t"; fi
    removed=$((removed + 1))
done
(( removed )) || echo "nothing to clean"
