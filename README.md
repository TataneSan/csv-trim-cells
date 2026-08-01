# csv-trim-cells

Trim leading/trailing whitespace from CSV cells — all cells, or only
selected columns. Perfect before diffing, deduplicating or importing
spreadsheets exported from Excel.

Zero dependencies, pure Python 3.9+.

## Features

- Trims every cell (header included) by default
- `-c/--columns` to restrict to named or indexed columns
- Understands headers with their own whitespace (" name " still matches
  `-c name`)
- `--check` CI mode: exit 2 when any cell needed trimming
- `-o` output file, `--json` summary report
- Multiple files, stdin support

## Install

```bash
pip install .
# or directly from GitHub
pip install git+https://github.com/TataneSan/csv-trim-cells.git
```

## Usage

```bash
# trim all cells
printf ' name , age \n alice , 30 \n' | csv-trim-cells -
# name,age
# alice,30

# only the "name" column
csv-trim-cells users.csv -c name

# write result to a file
csv-trim-cells dirty.csv -o clean.csv

# CI: fail when cells need trimming
csv-trim-cells data.csv --check || echo "cells need trimming"

# JSON summary
csv-trim-cells data.csv --json
```

## Options

| Option | Description |
|---|---|
| `-c, --columns COL...` | only trim these column names / 0-based indexes |
| `--check` | exit 2 when any cell needs trimming; no CSV written |
| `-o, --output FILE` | write CSV to FILE (single input only) |
| `--json` | emit a JSON summary report |

## Exit codes

| Code | Meaning |
|---|---|
| 0 | success |
| 1 | CLI or I/O error |
| 2 | `--check` found cells needing trimming |

## License

MIT
