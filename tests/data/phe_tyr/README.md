# Phe–Tyr golden data set

Real input and output data for the golden test (`tests/test_golden.py`).

## What it is

The π-stacked **phenylalanine–tyrosine (Phe–Tyr)** amino-acid pair studied in:

> *X-ray absorption spectroscopy reveals charge transfer in π-stacked aromatic amino acids*,
> Phys. Chem. Chem. Phys. (2025). https://doi.org/10.1039/D4CP04615C

- X-ray absorption spectra (XAS) computed with ORCA; carbon 1s core excitations.
- First 26 excited states per geometry (`1-26` in the file names).
- 52 geometries: intermolecular separations **3.5–11.0 Å** (0.1 Å steps up to 8.0 Å,
  then 0.5 Å steps), the range used in the paper. Shorter separations exist in the
  original data, but they are not chemically reliable and are not included here.
- Fragment A = Phe (atoms 0–22), fragment B = Tyr (atoms 23–46). Aromatic ring atoms:
  Phe 6–11, Tyr 29–33 and 35 (from `popmatrices/Bigscale/conditions_ETDCA.txt`).

The input CSV files were produced from the ORCA outputs by
[xas-qmol-parser](https://github.com/caraortizmah/x-ray_scripting_out).

## Files

| File | Content |
|------|---------|
| `resA_MOcore_list.log` | list file: `hash,path` to the core-MO population matrices |
| `resB_MOvirt_list.log` | list file: `hash,path` to the virtual-MO population matrices |
| `corevirt_fosce_AB_list.log` | list file: `hash,path` to the core→virtual oscillator-strength matrices |
| `inputs/*.csv` | the 3 × 52 matrices; paths in the list files are relative to this folder |
| `reference/data_etdac_matrix_3.5-11.0A.h5` | expected ETDAC matrices, one group `sample_<hash>` per geometry |

- Population files: index column `num-1` (atom number), then `sym`, `lvl`, then one column
  per MO. Values are Löwdin populations in **percent**, printed with one decimal.
- Oscillator-strength files: index column `virt\core` (virtual MO), one column per core MO.

Naming note: in `resA_MOcore` / `resB_MOvirt`, **A and B label the fragments** (A = Phe,
B = Tyr). The pairing "A with core, B with virtual" is this data set's choice, not a
rule of the method. A future release may rename these files.

## Sample IDs (hashes)

Samples are identified as `f10` … `f61`, the same IDs as in the full original data set
(`f00` = 2.5 Å; `f10` = 3.5 Å is the first one kept here). `f<number>` is only this data
set's convention: any unique alphanumeric ID (`[A-Za-z0-9]`, up to 64 characters) is valid.

## Provenance

- `inputs/` and the list files: copied unchanged from `popmatrices/newFY_1-26/` and
  `popmatrices/Bigscale/` (samples `f10`–`f61` only; list paths rewritten to `inputs/…`).
- `reference/…h5`: the groups `sample_f10` … `sample_f61` copied unchanged (data,
  compression, attributes) from `popmatrices/Bigscale/data_etdac_matrix.h5`, which was
  produced by `popmatrices/Bigscale/ETDAC_matrix_calculator.ipynb`. Re-running the
  notebook's functions on the files in this folder reproduces all 52 matrices exactly
  (maximum absolute difference 0.0).
