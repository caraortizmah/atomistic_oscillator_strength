# ADR 0005: Input validation: allowlist, fail closed

- Status: accepted; revised 2026-11-26 before implementation (edge warning for rounding, size limits fixed now and configurable later, required tests added); revised 2026-11-27 during step 5c (list-file format details, see the section below)
- Date: 2026-11-26

## Context

The program reads untrusted files: list files (`hash,path` per line) and the CSV matrices they point to. A wrong value must never produce a silent, plausible-looking result (for example NaN spreading through the products). The same values may later reach other contexts: terminal and log output, `.h5` attributes, JSON, a GUI, a spreadsheet, or a workflow engine such as n8n.

## Decision

Every input is checked **before** any calculation. On a failure the run stops
(fail closed) with an error naming the sample hash and the file.

Errors:

| Item | Rule |
|------|------|
| List file lines | exactly two comma-separated fields: `hash,path` |
| Hash | matches `^[A-Za-z0-9]{1,64}$`; unique within a list file; the three list files contain the same set of hashes |
| Population CSV header | exactly `num-1,sym,lvl,<MO labels…>` |
| Oscillator-strength CSV header | exactly `virt\core,<core MO labels…>` |
| Atom and MO labels | integers, unique within the file |
| Numeric cells | parsed strictly as numbers; finite (no NaN, no ±inf); any text in a number column is an error |
| Populations | ≥ 0 (a negative population is impossible in this field) |
| Oscillator strengths | ≥ 0 |
| `sym`, `lvl` text columns | match `^[A-Za-z]{1,8}$` (letters only, e.g. `C`, `atom`, `s`, `lvlMO`) |
| Size limits | at most 10 000 entries per list file; at most 50 MB per CSV file (against resource exhaustion). Fixed (mandatory) in 1.2.0; see Consequences for making them configurable |

Warnings (the run continues, the warning is logged, the data's veracity should be checked):

| Item | Rule |
|------|------|
| Single population value | > 100 % |
| Sum of one MO's populations over the atoms, 100 % < sum ≤ 102.5 % | "at the edge": consistent with rounding, but reported so the user notices |
| Sum of one MO's populations over the atoms, sum > 102.5 % | "beyond rounding tolerance": check the veracity of the data |

Why the 2.5 tolerance: the parser prints populations with one decimal, so each value carries a rounding error of up to 0.05. Summed over 47 atoms, that is up to 47 × 0.05 = 2.35 percentage points. A column sum of, say, 101.2 is therefore probably a rounding artefact, not a data error, but it is still reported as a warning: data at the edge must never pass unnoticed. Above 102.5 rounding can no longer explain it, and the warning says so. A sum of exactly 100.0 gives no warning. In the Phe–Tyr data the largest column sum is 99.8.

Scope of the tolerance: 2.5 is calibrated for systems of up to 47 atoms with values printed to one decimal. For N atoms the worst-case rounding error is N × 0.05 percentage points (e.g. 100 atoms: 5.0), so larger systems can trigger the "beyond rounding tolerance" warning from rounding alone. Providing values with adequate precision (more decimals for larger systems) is the user's responsibility; the user documentation (`docs/input-format.md`) says so. Making the tolerance depend on the number of atoms is a possible future change and would need a revision of this ADR.

### Security distinction 1: context-aware handling (validate on input, encode on output)

Input validation and output encoding are two different controls, and neither replaces the other.

- **Input validation** (this ADR) is an allowlist: it accepts only what the data is supposed to look like. Because `sym`/`lvl` accept letters only and hashes accept letters and digits only, characters such as `<`, `>`, `"`, `'`, `=`, `{`, `}`, `$`, `;`, newline or ANSI escape codes cannot reach any output from these fields today.
- **Output encoding** must still be done by every output, **for its own context**, because input rules can change and new fields can be added:
  - HTML / GUI: HTML-escape (prevents XSS).
  - JSON (APIs, n8n): build with a JSON serialiser (`json.dumps`), never by string concatenation.
  - n8n and other workflow engines: pass values as data, never inside expressions (`{{ … }}`) or code nodes.
  - Shell: never `shell=True`; pass arguments as a list.
  - Terminal and logs: print untrusted values with `repr()` and truncate them, so a crafted value cannot inject fake log lines or terminal escape codes.

This is defence in depth: the allowlist shrinks what can arrive, and context-aware encoding makes each output safe even if something unexpected arrives anyway.

### Security distinction 2: CSV / formula injection

Spreadsheet programs execute a cell as a formula when it starts with `=`, `+`, `-`, `@` (also tab or carriage return), for example `=HYPERLINK(…)` or `=cmd|' /C calc'!A0`.

- **Inputs:** number columns are parsed strictly as numbers and text columns accept letters only, so no formula can enter through the CSV inputs. (A leading `-` in a number column is a negative number and is then rejected by the ≥ 0 rule.)
- **Outputs:** the program writes `.h5` files only. If a CSV export is ever added, numbers must stay numeric and every text cell starting with one of the characters above must be neutralised (prefixed with `'`), following the OWASP guidance on CSV
  injection.

### List-file format details (decided in step 5c)

The reader is strict about structure and tolerant only about harmless editing leftovers, which it always reports. The user-facing description is `docs/input-format.md`; every format error points to it.

| Found | Result |
|-------|--------|
| UTF-8 BOM at the start | removed; INFO |
| one line-ending style: `\r\n` (Windows) or `\r` (classic Mac) | accepted; INFO |
| `\n` mixed with `\r\n` | accepted; WARNING (the `\r` is a removable leftover) |
| lone `\r` in a file that also uses `\n` or `\r\n` | error: not interpreted, never edited |
| blank or whitespace-only line, anywhere | ignored; WARNING naming file and line (samples are paired by hash, not by line position) |
| tab, control or invisible character (zero-width, line separators, bidirectional overrides: "Trojan Source", CVE-2021-42574) | error |
| leading or trailing spaces in a field | error |
| spaces inside a path | accepted; WARNING (works in Python, no shell involved, but may break shell commands or tools that do not quote paths) |
| duplicate hash within one list file | error, checked for the whole list before any CSV is opened (implemented in step 5c, because a dict keyed by hash would silently keep only the last one) |

## Required tests

Every rule has a negative test (the input must be rejected or warned about) paired with a positive test just inside the boundary (the input must be accepted silently). The pairs prove each rule is exact: a rule that rejects everything would pass the negative tests alone. Tests are written failing first, one rule at a time (step 5).

| Rule | Negative: input → expected | Positive boundary: input → accepted |
|------|----------------------------|-------------------------------------|
| List line | 1 field, 3 fields, empty line → error | `f10,inputs/x.csv` |
| Hash pattern | `f 10`, `f10;rm`, `<b>`, 65 characters → error | `f10`, 64 characters |
| Hash duplicates / sets | duplicate within a list; hash missing from one of the three lists → error | same set in all three lists, any order |
| Header | `num-1,sym,lvl` misspelled or reordered; `virt\core` missing → error | exact headers |
| Labels | non-integer atom or MO label; duplicate label → error | unique integers |
| Numbers | `NaN`, `inf`, `-inf`, empty cell, `abc` → error | `0`, `0.0`, `1e-6` |
| Formula injection | `=HYPERLINK(…)`, `+1`, `@SUM(A1)` in a number column → error | plain numbers |
| Signs | population −0.1; oscillator strength −1e-9 → error | `0.0` |
| Text fields | `sym` = `<script>`, `C;`, `C1`, 9 letters → error | `C`, `atom`, `s`, `lvlMO`, 8 letters |
| Size | 10 001 list entries; CSV > 50 MB → error, before parsing | 10 000 entries; 50 MB |
| Paths (ADR 0003/0004) | absolute path; `../../etc/passwd`; symlink pointing outside the data root → error | relative path inside the data root |
| Output (ADR 0003) | existing output → renamed `_oldversion1`, never overwritten; existing `_oldversion1` → next is `_oldversion2` | empty output folder → plain name |
| Warning: single population | 100.1 → warning, run continues | 100.0 → no warning |
| Warning: MO sum at the edge | 100.1 and 102.5 → "at the edge" warning | 100.0 → no warning |
| Warning: MO sum beyond tolerance | 102.6 → "beyond rounding tolerance" warning | 102.5 → only the edge warning |
| Message safety | hostile value (newline, ANSI escape, 10 kB string) → message names hash and file, shows the value with `repr()`, truncated | — |

## Alternatives considered

- **Blocklist** (reject known-bad characters): rejected; it always misses something.
  An allowlist describes the valid data instead.
- **Silent clean-up** (drop bad rows, replace NaN by 0): rejected; it hides data problems behind a plausible result, which is exactly what this ADR prevents.
- **Trimming as the only guard** (ADR 0002): not sufficient; it removes all-zero columns but keeps NaN.

## Consequences

- Implemented and tested in step 5, one rule at a time (failing test first). Step 5c: list-line format, the details above, duplicates within a list, and paths (ADR 0003/0004). Step 5d: hash pattern, the same hashes in all three files, CSV structure and values, size limits, warnings.
- Error messages name the hash and the file, and show untrusted values with `repr()`, truncated.
- The rules describe the current parser output. A new parser format needs a new ADR.
- Future: the size limits become configuration (for example in the JSON run config), because data sets above 10 000 entries are realistic. The fixed values become the defaults, and a raised limit must be set explicitly by the user and reported in the log. This needs its own ADR when implemented.
