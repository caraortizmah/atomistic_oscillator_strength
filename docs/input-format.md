# Input format

## What the inputs mean

For every molecular geometry (a **sample**, named by a short **hash** such as `f10`), the ETDAC calculation needs three matrices, produced from ORCA XAS outputs by [xas-qmol-parser](https://github.com/caraortizmah/x-ray_scripting_out):

| Matrix | Rows | Columns | Values |
|--------|------|---------|--------|
| core-MO populations | atoms | core MOs | Löwdin population of each core MO on each atom, in percent |
| virtual-MO populations | atoms | virtual MOs | Löwdin population of each virtual MO on each atom, in percent |
| core-electron transition intensities | virtual MOs | core MOs | intensity of the transition from the core MO to the virtual MO |

Each matrix is one CSV file. Three **list files** say which CSV file belongs to which sample:

| List file (example name) | Points to | CSV index column |
|--------------------------|-----------|------------------|
| `resA_MOcore_list.log` | core-MO population matrices | `num-1` |
| `resB_MOvirt_list.log` | virtual-MO population matrices | `num-1` |
| `corevirt_fosce_AB_list.log` | core-electron transition-intensity matrices | `virt\core` |

In the example names, A and B label the two molecular fragments (e.g. Phe and Tyr), not core and virtual. A complete, real example is in `tests/data/phe_tyr/`.

## Project folder

Keep everything for one system in one folder, the **project folder**:

```
my_project/
  resA_MOcore_list.log          # the three list files
  resB_MOvirt_list.log
  corevirt_fosce_AB_list.log
  inputs/                       # the CSV files named in the list files
  etdac_outputs/                # created by the program: results (.h5) and run log (.log)
```

Give the program this folder, or run it inside the folder. Paths in the list files are relative to the list file and must not leave the data folder (see the common mistakes below). The program writes only into `etdac_outputs/` of the project folder; an earlier result there is kept as `_oldversionN`, never overwritten. Where the program is installed does not matter, and uninstalling it never touches your project folders. `tests/data/phe_tyr/` is a complete example.

## List files

```
f10,inputs/resA_MOcore_AB_3.5A_1-26.csv
f11,inputs/resA_MOcore_AB_3.6A_1-26.csv
f12,inputs/resA_MOcore_AB_3.7A_1-26.csv
```

- **UTF-8** text, one entry per line, Unix line endings (`\n`).
- Each line: `hash,path`. A **comma** separates the two fields; nothing else.
- **No spaces anywhere**: not around the comma, not at the start or end of a line, not in file names.
- **Hash**: letters and digits only (A-Z, a-z, 0-9, up to 64 characters), unique within the file. `f<number>` is a convention, not a rule. The same hashes must appear in all three list files, in any order: samples are matched by hash, not by line position.
- **Keep hashes short**: at most 9 characters is recommended (e.g. `f0001`, enough for 10 000 samples).
- **Hashes in this version** assume that one run reads one set of three list files. When a large system can be split into many list files (planned), hashes will have to be unique across all of them; this page will change with that version.
- **Path**: relative to the folder of the list file, pointing to an existing file. Absolute paths are not allowed. The path must stay inside the **data folder**: by default, the folder that contains the list files' folder (for `tests/data/phe_tyr/`, that is `tests/data/`).
- No blank lines, no comments, no header line.

## What the program tolerates, and how it tells you

| Found | Result |
|-------|--------|
| UTF-8 BOM at the start (Excel, some Windows editors) | removed; INFO in the log |
| Windows (`\r\n`) or classic Mac (`\r`) line endings, used consistently | accepted; INFO in the log |
| `\n` mixed with `\r\n` | accepted; WARNING |
| blank or whitespace-only line | ignored; WARNING naming the line |
| spaces inside a path | accepted; WARNING (may break shell commands or other tools) |

## Common mistakes in list files (rejected with an error)

| Line | Problem |
|------|---------|
| `f10` | one field: the path is missing |
| `f10,a.csv,extra` | three fields |
| `f10, inputs/a.csv` | space after the comma |
| `f10,/home/me/data/a.csv` | absolute path |
| `f10,../../somewhere/a.csv` | path leaves the data folder |
| a lone `\r` inside a line of a `\n` file | mixed line endings that cannot be removed safely |
| tab, invisible or control characters (e.g. a zero-width space copied from a web page) | forbidden characters |
| text saved as Latin-1 / Windows-1252 | not UTF-8 |

## CSV files

The CSV files are read as produced by xas-qmol-parser (comma-separated):

- population files: header `num-1,sym,lvl,<MO labels…>`; one row per atom (`sym`: element symbol, e.g. `C`; `lvl`: orbital type, e.g. `s`);
- transition-intensity files: header `virt\core,<core MO labels…>`; one row per virtual MO.

Rules:

- UTF-8, the same line rules as list files (BOM and line endings reported, blank lines ignored with a warning, no control or invisible characters).
- Comma-separated, **no quotes, no spaces around cells**: `1,C,s,60.0`, not `1, C, s, 60.0`.
- Header exactly as above; at least one MO column and one data row.
- MO labels (header) and row labels (first column): non-negative integers, unique within the file.
- Every row has as many fields as the header.
- Numbers: plain decimal numbers such as `0`, `0.0`, `99.6`, `8.73323e-06` or `1E5`. Not allowed: `nan`, `inf`, empty cells, text, spaces, a `+` or `=` at the start, `1_000`, non-ASCII digits. `.5` and `5.` are read as 0.5 and 5.0 with a warning: write the zero.
- Populations and transition intensities are never negative (`-0.0` is accepted as zero).
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
| `1,C,s,nan` or an empty cell | not a number (it would spread as NaN through the results) |
| `1,C,s,=SUM(A1)` | a spreadsheet formula, not a number |
| `1,C,s,-0.1` | negative population |

### Population sums and precision (your responsibility)

Populations are in percent. A single value should not exceed 100 %, and the populations of one MO summed over all atoms should not exceed 100 %. Above that the program warns: "at the edge" up to 102.5 %, "beyond the rounding tolerance" above. All findings for one file come as **one warning** naming the file, the counts and the first value or column, so you know where to look. Sums below 100 % are normal (the parser does not write every small contribution) and give no warning. Core-electron transition intensities have no an expected limit as the case of percentages.

The 2.5 tolerance covers the rounding of values printed with **one decimal** for systems of **up to 47 atoms** (each value can be off by up to 0.05; 47 × 0.05 = 2.35). For larger systems the rounding error grows with the number of atoms (N × 0.05; 100 atoms: up to 5.0) and can trigger the "beyond the rounding tolerance" warning even for correct data. **Providing values with enough precision is the user's responsibility**: for systems larger than 47 atoms, export the populations with more decimals.

## Size limits

Very large inputs are refused, so that a run stays manageable on a workstation. A file that hits a limit is not damaged: it is larger than this version accepts. The limits may become configurable in a later version.

| Input | Accepted | Warning | Error |
|-------|----------|---------|-------|
| entries in a list file | up to 10 000 | 10 001 to 10 100: accepted, but split the samples into runs of at most 10 000 | more than 10 100 |
| size of a list file | up to 3 MB (10 000 entries take about 0.5 MB) | none | larger than 3 MB |
| size of a CSV file | up to 50 MB (the Phe-Tyr CSV files are at most 5.4 kB) | none | larger than 50 MB |
