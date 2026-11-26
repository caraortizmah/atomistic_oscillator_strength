# ADR 0004: Temporary default data root is the parent of the logs folder

- Status: accepted
- Date: 2026-11-26
- Supersedes: the default data root in ADR 0003 (the rest of ADR 0003 still applies)

## Context

ADR 0003 sets the default data root to the logs folder. The existing list files in
`popmatrices/Bigscale/` point to `../newFY_1-26/...`, so they would be rejected. The
folder `newFY_1-26` will be renamed later, but not now.

## Decision

Until `newFY_1-26` is renamed, the default data root is the **parent of the logs
folder** (exactly one level up). The rule itself stays strict:

- Every path is resolved with `Path.resolve()`, which follows symlinks.
- Absolute paths in list files are rejected.
- Any resolved path outside the data root is rejected.
- The data root is not configurable by the user yet (`--data-root` is not exposed).

## Alternatives considered

- Exposing `--data-root` now: postponed until the rename.
- Allowing any ancestor folder: rejected; it is no longer least privilege.

## Consequences

- `popmatrices/Bigscale/*.log` -> `popmatrices/newFY_1-26/*.csv` is accepted as is.
- When `newFY_1-26` is renamed, a new ADR returns the default to the logs folder and
  exposes `--data-root`.
