# ADR 0006: Provenance metadata in output files

- Status: accepted
- Date: 2026-11-26

## Context

The reference file `data_etdac_matrix.h5` has no file-level metadata: no program version, no date, no record of which inputs produced it. Its numbers can only be trusted by re-running the calculation.

## Decision

Every `.h5` file written by the program gets file-level attributes:

| Attribute | Content |
|-----------|---------|
| `program` | `qm_etdac_calculator` |
| `program_version` | the package version (e.g. `1.2.0`) |
| `created_utc` | creation time, ISO 8601 in UTC (e.g. `2026-11-26T17:45:00Z`) |
| `input_files` | JSON list of `{"path": …, "sha256": …}` for every list file and CSV read |

The per-sample groups (`sample_<hash>`, dataset `ETDAC_matrix`, attributes `hash`, `index_name`, `column_name`) stay exactly as they are, so existing readers and notebooks keep working.

`input_files` is built with a JSON serialiser, never by string concatenation (ADR 0005, context-aware output). Paths are stored relative to the data root, so no user home folder or machine layout leaks into a shared result.

## Alternatives considered

- A separate sidecar file (`.json` next to the `.h5`): rejected; it can get lost or mismatched. The metadata travels inside the result.
- No provenance: rejected; a result cannot be traced back to its inputs.

## Consequences

- Any result can be checked against its inputs: recompute the SHA-256 of the input files and compare. This is the same integrity idea as the hashed lock file (ADR 0001).
- Two runs on the same inputs give files that differ in `created_utc`, so `.h5` files are compared numerically, never by checksum.
- Implemented and tested in step 5.
