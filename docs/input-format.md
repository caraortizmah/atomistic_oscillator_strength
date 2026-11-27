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
- **Keep hashes short**: at most 9 characters is recommended (e.g. `f0001`, enough for 10 000 samples with room to spare). Short hashes keep the messages and logs readable and the list files small.
- **Temporary hash policy**: the rules above assume that one run reads one set of three list files. When a large system is split into many list files (planned, e.g. 1 000 000 samples in 100 files), hashes will have to be unique across all of them and may be longer; this page will change with that version.
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

Structure rules (checked before any number is interpreted; see ADR 0005 for the reasons):

- UTF-8, the same line rules as list files (BOM and line endings reported, blank lines ignored with a warning, no control or invisible characters).
- Comma-separated, **no quotes, no spaces around cells**: `1,C,s,60.0`, not `1, C, s, 60.0`.
- Header exactly as above; at least one MO column and one data row.
- MO labels (header) and row labels (first column): non-negative integers, unique within the file.
- Every row has as many fields as the header.
- Numbers: plain decimal numbers such as `0`, `0.0`, `99.6`, `8.73323e-06` or `1E5`. Not allowed: `nan`, `inf`, empty cells, text, spaces, `+` or `=` at the start (spreadsheet formulas), `1_000`, non-ASCII digits. `.5` and `5.` are read as 0.5 and 5.0 with a warning: write the zero.
- Populations and oscillator strengths are never negative (`-0.0` is accepted as zero).
- `sym` and `lvl`: 1 to 8 letters (A-Z, a-z), e.g. `C`, `atom`, `s`, `lvlMO`.

Common mistakes in CSV files (rejected with an error naming the sample and file):

| Found | Problem |
|-------|---------|
| `1, C, s, 60.0` | spaces around cells |
| `num-1;sym;lvl;7` | semicolons instead of commas (e.g. exported by a spreadsheet in some languages) |
| `"num-1",sym,lvl,7` | quotes |
| `num-1,sym,lvl,7,7` | duplicate MO label |
| `atom,sym,lvl,7` | wrong header |
| a row with one field more or less than the header | ragged row |
| `1,C,s,nan` or an empty cell | not a number (would spread as NaN through the results) |
| `1,C,s,=SUM(A1)` | formula, not a number |
| `1,C,s,-0.1` | negative population |

Their content is validated as described in ADR 0005 (finite numbers, populations ≥ 0,
letters-only `sym`/`lvl`, and the warnings for population sums above 100 %).

### Precision of the population values (your responsibility)

Populations are expected in percent. A single value should not exceed 100 %, and the sum of one MO's populations over the atoms should not exceed 100 %; above it the program warns ("at the edge" up to 102.5 %, "beyond the rounding tolerance" above). All of these findings for one file come as **one warning** naming the file, the counts and the first value or column, so you know where to look. Sums below 100 % are normal (the parser does not write every small contribution) and give no warning. Oscillator strengths have no 100 limit.

The 2.5 tolerance covers the rounding of values printed with **one decimal** for systems of **up to 47 atoms** (each value can be off by up to 0.05; 47 × 0.05 = 2.35). For larger systems the rounding error grows with the number of atoms (N × 0.05; 100 atoms: up to 5.0) and can trigger the "beyond rounding tolerance" warning even for correct data. **Providing values with enough precision is the user's responsibility**: for systems larger than 47 atoms, export the populations with more decimals.

## Size limits

The limits protect against resource exhaustion (an input so large that the program runs out of memory or time). They are a policy, not a program error: a file that hits one is not damaged, it is larger than this version accepts. The limits are fixed in this version and may become configurable later (ADR 0005).

| Input | Accepted | Warning | Error |
|-------|----------|---------|-------|
| entries in a list file | up to 10 000 | 10 001 to 10 100: accepted, but split the samples into runs of at most 10 000 | more than 10 100 |
| size of a list file | up to 3 MB (a typical line is about 45 bytes: 10 000 entries take about 0.5 MB) | none | larger than 3 MB, rejected without reading the whole file |
| size of a CSV file | up to 50 MB (the Phe-Tyr CSV files are at most 5.4 kB) | none | larger than 50 MB, rejected without reading the whole file |
