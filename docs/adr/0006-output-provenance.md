# ADR 0006: Provenance metadata in output files

- Status: accepted; implementation details added 2026-11-27 in step 5e (see Consequences)
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
- Implemented and tested in step 5e, commit 3 (`gate_controler.Controler.inputs_read`, `outputs.provenance`, `outputs.write_etdac_h5`; tests in `tests/test_controler.py` and `tests/test_outputs.py`). Details decided during the implementation:
  - The SHA-256 is computed from the same bytes that were checked and parsed, never by reading the file again. A file swapped after the read cannot make the record describe content that was not used (TOCTOU); a test swaps the file and checks the record.
  - Only files whose content passed the checks are recorded (the list file once its entries passed the path policy, each CSV once its structure and values passed). A run that stops on an error writes no result, so nothing needs a record of rejected files.
  - Records are in read order. A file read twice with the same content is recorded once; a file whose content changed between two reads is recorded twice, because both versions were used.
  - A symlinked input is recorded under its real path (the file that was actually read), relative to the data root.
  - `input_files` is written with `json.dumps(..., ensure_ascii=True)`: quotes, brackets and commas in file names cannot break or forge the record, and non-ASCII names are escaped, so the attribute is plain ASCII for any reader.
  - `created_utc` is UTC to the second, e.g. `2026-11-27T19:30:00Z`.
  - Writing a result without any recorded input is a program error (`ValueError`): every run reads at least its list files.
  - The golden test checks the groups against the reference file (which has no file-level attributes) and the provenance separately: 159 records for the Phe-Tyr data (3 list files + 3 x 52 CSV files).
