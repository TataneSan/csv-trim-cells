# csv-trim-cells

Trim leading/trailing whitespace in CSV cells, with optional internal
whitespace collapse, column filtering and CI-friendly checks.

## Features

- Trims both, left or right side of every cell (`--side`)
- Preserves the header row by default (`--trim-header` to include it)
- Column filtering by name or 1-based index (`--columns`)
- Collapse internal whitespace runs to a single space (`--collapse`)
- Drop rows that become entirely empty (`--drop-empty-rows`)
- CI mode: `--check` exits 2 when any cell would change
- Machine-readable `--json` report
- Reads stdin when the file is omitted or `-`

## Install

```sh
pip install .
# or directly
pip install git+https://github.com/TataneSan/csv-trim-cells.git
```

## Usage

```sh
# Trim all cells (header preserved)
csv-trim-cells data.csv

# Semicolon-separated input, collapse internal spaces
csv-trim-cells --delimiter ';' --collapse data.csv

# Only trim columns 1 and 3, drop fully-empty rows
csv-trim-cells --columns 1,3 --drop-empty-rows data.csv

# CI: fail if anything would be trimmed
csv-trim-cells --check data.csv

# JSON report without writing the CSV
csv-trim-cells --json data.csv

# From stdin
cat data.csv | csv-trim-cells -
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | success (or `--check` with nothing to trim) |
| 1 | I/O or CLI usage error |
| 2 | `--check` found cells to trim, or `--require-trimmed-max` failed |

## License

MIT
