# Input format

The program reads three **list files**. Each list file names, per sample, one CSV file
produced by [xas-qmol-parser](https://github.com/caraortizmah/x-ray_scripting_out):

| List file (example name) | Points to | CSV index column |
|--------------------------|-----------|------------------|
| `resA_MOcore_list.log` | core-MO population matrices | `num-1` |
| `resB_MOvirt_list.log` | virtual-MO population matrices | `num-1` |
| `corevirt_fosce_AB_list.log` | core→virtual oscillator-strength matrices | `virt\core` |

A complete, real example: `tests/data/phe_tyr/`.

## List files: the simple, robust format

```
f10,inputs/resA_MOcore_AB_3.5A_1-26.csv
f11,inputs/resA_MOcore_AB_3.6A_1-26.csv
f12,inputs/resA_MOcore_AB_3.7A_1-26.csv
```

- **UTF-8** text, one entry per line, Unix line endings (`\n`).
- Each line: `hash,path`. A **comma** separates the two fields; nothing else.
- **No spaces anywhere**: not around the comma, not at the start or end of a line, not in
  file names.
- **Hash**: letters and digits only (`[A-Za-z0-9]`, up to 64 characters), unique within the
  file. `f<number>` is a convention, not a rule. The same hashes must appear in all three
  list files (in any order): samples are paired by hash, not by line position.
- **Path**: relative to the folder of the list file. Absolute paths are not allowed. The
  path must stay inside the data root (by default the parent folder of the list files'
  folder; ADR 0003, ADR 0004) and point to an existing file.
- No blank lines, no comments, no header line.

## What the program tolerates, and how it tells you

| Found | Result |
|-------|--------|
| UTF-8 BOM at the start (Excel, some Windows editors) | removed; INFO in the log |
| Windows (`\r\n`) or classic Mac (`\r`) line endings, used consistently | accepted; INFO in the log |
| `\n` mixed with `\r\n` | accepted; WARNING |
| blank or whitespace-only line | ignored; WARNING naming the line |
| spaces inside a path | accepted; WARNING (may break shell commands or other tools) |

## Common mistakes (rejected with an error)

| Line | Problem |
|------|---------|
| `f10` | one field: the path is missing |
| `f10,a.csv,extra` | three fields |
| `f10, inputs/a.csv` | space after the comma |
| `f10,/home/me/data/a.csv` | absolute path |
| `f10,../../somewhere/a.csv` | path leaves the data root |
| a lone `\r` inside a line of a `\n` file | mixed line endings that cannot be removed safely |
| tab, invisible or control characters (e.g. zero-width space, ANSI codes) | forbidden characters |
| text saved as Latin-1 / Windows-1252 | not UTF-8 |

## CSV files

The CSV files are read as produced by xas-qmol-parser (comma-separated):

- population files: header `num-1,sym,lvl,<MO labels…>`; one row per atom;
- oscillator-strength files: header `virt\core,<core MO labels…>`; one row per virtual MO.

Their content is validated as described in ADR 0005 (finite numbers, populations ≥ 0,
letters-only `sym`/`lvl`, and the warnings for population sums above 100 %).
