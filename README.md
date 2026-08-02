# csv-trim-cells

**Trim leading/trailing whitespace from every cell of a CSV file.**

Messy exports often carry stray spaces around values (`" Paris "`, `"42 "`),
which break joins, lookups, and comparisons downstream. csv-trim-cells sniffs
the delimiter, cleans every cell, and rewrites the file — or lints it in CI.

## Features

- Auto-detects the delimiter (`,`, `;`, tab, `|`) with a comma fallback
- Strips leading/trailing whitespace from every cell
- `--collapse`: reduce internal whitespace runs to a single space
- `--check`: lint mode — exit 2 if any cell had extra whitespace (no rewrite)
- `--json`: machine-readable report of modified cells grouped by column
- Reads a file or stdin (`-`); pure standard library

## Installation

```sh
pip install .
# or
pip install git+https://github.com/TataneSan/csv-trim-cells.git
```

## Usage

```sh
# Clean a file, write the trimmed CSV to stdout
csv-trim-cells data.csv > clean.csv

# In-place style (via a temp file)
csv-trim-cells data.csv > data.tmp && mv data.tmp data.csv

# From stdin
cat data.csv | csv-trim-cells -

# Also collapse internal whitespace runs
csv-trim-cells --collapse notes.csv > notes-clean.csv

# CI lint gate: fail if any cell still has extra whitespace
csv-trim-cells --check dirty.csv

# JSON report of modified cells per column
csv-trim-cells --json data.csv
```

### Example

Given `dirty.csv`:

```csv
name, city ,score
 Alice ," Paris ", 42
Bob,Lyon ,  37
```

```sh
csv-trim-cells dirty.csv
```

```csv
name,city,score
Alice,Paris,42
Bob,Lyon,37
```

(Values parsed from quotes are trimmed too — leading/trailing whitespace is
removed from every cell. Use `--collapse` to squeeze internal runs as well.)

### JSON output

```json
{
  "changed_cells": 5,
  "collapse": false,
  "columns": {
    "city": 2,
    "name": 1,
    "score": 2
  },
  "delimiter": ",",
  "file": "dirty.csv",
  "rows": 3
}
```

## Exit codes

| Code | Meaning |
|------|---------|
| `0`  | Success (file rewritten, or `--check` found nothing to trim) |
| `1`  | I/O or CLI error |
| `2`  | `--check` was given and at least one cell had extra whitespace |

## Development

```sh
python3 -m unittest discover -s tests -v
```

## License

MIT — see [LICENSE](LICENSE).
