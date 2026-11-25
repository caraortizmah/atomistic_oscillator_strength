# ADR 0002: The notebook is the numerical source of truth

- Status: accepted
- Date: 2026-11-26

## Context

The package was split out of `popmatrices/Bigscale/ETDAC_matrix_calculator.ipynb`.
That notebook reproduces `popmatrices/Bigscale/data_etdac_matrix.h5` exactly. The
package version had drifted: for example, it trimmed the virtual-population matrix,
which the notebook does not.

## Decision

The package must give the same numbers as the notebook.

1. The core-population matrix is **not** trimmed. The
   virtual-population matrix is **not** trimmed: zero columns carry no weight, but their existence is information.
2. The first product (core populations × oscillator strengths) is divided by 100 (percent scale). The second product (× virtual populations) is not. This is an intentional scale choice; the analysis uses the global pattern.
3. Products run over the MO labels the two matrices share.

## Alternatives considered

- Final result is normalized when is presented as heatmaps.

## Consequences

- The tests keep a frozen copy of the notebook's loop functions and assert equality
  (about 1e-12) against the package on random inputs.
- A golden test compares against `data_etdac_matrix.h5` when the data is present.
